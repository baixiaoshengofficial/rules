#!/usr/bin/env python3
"""Verify that routing unknown domains does not cause an extra DNS lookup.

Uses a converted config, local DNS recorder and dummy proxy; never contacts an
external resolver. The control removes no-resolve and must produce a lookup.
"""
import argparse
import copy
import json
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import time

import yaml
from test_integration import ROOT, free_port, socks_request, wait_for


class DNSRecorder(socketserver.BaseRequestHandler):
    def handle(self):
        packet, sock = self.request
        end = 12
        labels = []
        while packet[end]:
            size = packet[end]
            labels.append(packet[end + 1:end + 1 + size].decode())
            end += size + 1
        end += 1
        kind = struct.unpack('!H', packet[end:end + 2])[0]
        self.server.queries.append('.'.join(labels))
        answer = b''
        if kind == 1:
            answer = b'\xc0\x0c' + struct.pack('!HHIH', 1, 1, 60, 4) + bytes([203, 0, 113, 250])
        response = packet[:2] + struct.pack('!HHHHH', 0x8180, 1, bool(answer), 0, 0)
        sock.sendto(response + packet[12:end + 4] + answer, self.client_address)


def run(config, mihomo, geodata, control):
    with tempfile.TemporaryDirectory(prefix='rules-dns-') as temporary, socket.socket() as sink:
        sink.bind(('127.0.0.1', 0))
        sink.listen(128)
        work = Path(temporary)
        for name in ('GeoSite.dat', 'geoip.metadb', 'country.mmdb'):
            source = geodata / name
            if source.exists():
                (work / name).symlink_to(source.resolve())
        document = copy.deepcopy(config)
        port = free_port()
        document.update({'port': 0, 'socks-port': 0, 'mixed-port': port,
                         'external-controller': '', 'allow-lan': False,
                         'log-level': 'debug', 'hosts': {}, 'tun': {'enable': False}})
        document['proxies'] = [{'name': 'dns-test-node', 'type': 'ss',
                               'server': '127.0.0.1', 'port': sink.getsockname()[1],
                               'cipher': 'aes-128-gcm', 'password': 'dns-test'}]
        group_names = {g['name'] for g in document['proxy-groups']}
        for group in document['proxy-groups']:
            group['proxies'] = list(dict.fromkeys(
                name if name in group_names | {'DIRECT', 'REJECT'} else 'dns-test-node'
                for name in group['proxies']))
        for provider in document['rule-providers'].values():
            filename = provider['url'].rsplit('/', 1)[1]
            (work / filename).write_bytes((ROOT / filename).read_bytes())
            provider.clear()
            provider.update({'type': 'file', 'behavior': 'classical', 'format': 'text',
                             'path': str(work / filename)})
        geoip = 'GEOIP,CN,🎯 全球直连,no-resolve'
        assert geoip in document['rules'], 'Expected no-resolve in generated config'
        if control:
            document['rules'] = [r.replace(geoip, 'GEOIP,CN,🎯 全球直连') for r in document['rules']]
        with socketserver.UDPServer(('127.0.0.1', 0), DNSRecorder) as dns:
            dns.queries = []
            worker = threading.Thread(target=dns.serve_forever, daemon=True)
            worker.start()
            document['dns'] = {
                'enable': True, 'ipv6': False, 'enhanced-mode': 'redir-host',
                'nameserver': [f'127.0.0.1:{dns.server_address[1]}'],
                'default-nameserver': ['127.0.0.1'],
            }
            path = work / 'config.yaml'
            path.write_text(yaml.safe_dump(document, allow_unicode=True))
            log_path = work / 'runtime.log'
            with log_path.open('w') as log:
                process = subprocess.Popen([mihomo, '-d', str(work), '-f', str(path)],
                                           stdout=log, stderr=subprocess.STDOUT)
                try:
                    wait_for(lambda: 'Mixed(http+socks) proxy listening' in log_path.read_text())
                    host = 'unclassified-dns-regression.example.org'
                    with socks_request(port, host, 443) as sock:
                        sock.sendall(b'probe')
                        wait_for(lambda: host in log_path.read_text() and 'using 🐟 漏网之鱼' in log_path.read_text())
                    time.sleep(0.3)
                    queries = [q for q in dns.queries if q == host]
                    assert bool(queries) == control, (control, queries, log_path.read_text())
                    return len(queries)
                except AssertionError as error:
                    raise AssertionError(log_path.read_text()) from error
                finally:
                    process.terminate()
                    process.wait(timeout=10)
                    dns.shutdown()
                    worker.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--mihomo', required=True)
    parser.add_argument('--geodata-dir', required=True, type=Path)
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text())
    result = {name: run(config, args.mihomo, args.geodata_dir, control)
              for name, control in [('control_dns_queries', True), ('fixed_dns_queries', False)]}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
