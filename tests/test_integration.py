#!/usr/bin/env python3
"""Convert both configs with Subconverter and probe real Mihomo TCP/UDP routing.

Requires Python 3.11+, PyYAML, a local Subconverter and a Mihomo executable.
Unpublished repository files are served locally; external rules are downloaded.
No subscription credentials or working proxy nodes are required.
"""

import argparse
import base64
import concurrent.futures
from contextlib import contextmanager
import functools
import hashlib
import http.server
import ipaddress
import json
from pathlib import Path
import socket
import socketserver
import struct
import subprocess
import tempfile
import threading
import time
import tomllib
import urllib.parse
import urllib.request

import yaml

from test_rules import NEGATIVE, POSITIVE, ROOT, rules

OWNER = "https://raw.githubusercontent.com/baixiaoshengofficial/rules/main/"


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def wait_for(check, timeout=20):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            result = check()
            if result:
                return result
        except (OSError, urllib.error.URLError):
            pass
        time.sleep(0.05)
    raise AssertionError("Timed out waiting for service or route evidence")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


@contextmanager
def fixture_server(directory):
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()


def prepare_fixtures(directory, prefix, cache):
    config = tomllib.loads((ROOT / "baixiaosheng.toml").read_text())
    urls = {r["ruleset"] for r in config["rulesets"]
            if r["ruleset"].startswith("https://")}
    urls.add(config["custom"]["clash_rule_base"])
    cached = {}
    if cache and (cache / "index.json").exists():
        cached = {r["url"]: Path(r["cache"]) for r in
                  json.loads((cache / "index.json").read_text()) if r.get("status") == 200}

    def asset(url):
        if url.startswith(OWNER):
            name = url.removeprefix(OWNER)
            data = (ROOT / name).read_bytes()
        else:
            name = hashlib.sha256(url.encode()).hexdigest() + ".list"
            data = cached[url].read_bytes() if url in cached else fetch(url)
        (directory / name).write_bytes(data)
        return url, prefix + name

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        replacements = dict(pool.map(asset, sorted(urls)))
    # All provider contents use current workspace files, including regex/AND.
    base = yaml.safe_load((ROOT / "clash-base.yaml").read_text())
    for provider in base["rule-providers"].values():
        name = provider["url"].removeprefix(OWNER)
        (directory / name).write_bytes((ROOT / name).read_bytes())
        provider["url"] = prefix + name
    (directory / "clash-base.yaml").write_text(yaml.safe_dump(base, allow_unicode=True))
    for name in ("baixiaosheng.ini", "baixiaosheng.toml"):
        text = (ROOT / name).read_text()
        for old, new in replacements.items():
            text = text.replace(old, new)
        (directory / name).write_text(text)


def convert(url, prefix, name):
    # Exercise ASCII, emoji, Chinese and suffix-based node names.
    names = ["HK-01", "🇭🇰 香港 02 hkl", "TW-01", "🇹🇼 台湾 02 twl",
             "JP-01", "🇯🇵 日本 02 jpl", "SG-01", "新加坡 02 sgoracle",
             "US-01", "美国 ATT 家宽", "DE-01", "英国 UK-02"]
    credential = base64.b64encode(b"aes-128-gcm:integration-test").decode()
    nodes = "|".join(f"ss://{credential}@127.0.0.1:19999#{urllib.parse.quote(n)}"
                     for n in names)
    query = urllib.parse.urlencode({
        "target": "clash", "url": nodes, "config": prefix + name, "udp": "true",
    })
    document = yaml.safe_load(fetch(url.rstrip("/") + "/sub?" + query))
    assert isinstance(document, dict) and document.get("rules"), document
    assert set(document["rule-providers"]) == {"hongguo-ad", "quic", "ai", "tiktok"}
    for provider in document["rule-providers"]:
        assert any(r.startswith(f"RULE-SET,{provider},") for r in document["rules"])
    groups = {g["name"]: g for g in document["proxy-groups"]}
    for name in ("🇭🇰 香港均衡", "🇯🇵 日本均衡", "🇭🇰 TW均衡", "🇸🇬 SG均衡"):
        assert groups[name]["strategy"] == "consistent-hashing", groups[name]
        assert len(groups[name]["proxies"]) >= 2, groups[name]
        assert "DIRECT" not in groups[name]["proxies"], groups[name]
    assert groups["红果广告"]["proxies"] == ["REJECT"]
    assert "♻️ 自动选择" in groups["🚀 节点选择"]["proxies"]
    download = groups["📦 下载节点"]["proxies"]
    assert download[0] == "🚀 节点选择", download
    assert {p["name"] for p in document["proxies"]} <= set(download), download
    return document


class SinkHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # Accept dummy SS transports without decrypting or contacting a service.
        self.request.settimeout(15)
        try:
            while self.request.recv(65536):
                pass
        except OSError:
            pass


class Sink(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def receive(sock, length):
    chunks = bytearray()
    while len(chunks) < length:
        chunk = sock.recv(length - len(chunks))
        if not chunk:
            raise OSError("SOCKS socket closed")
        chunks.extend(chunk)
    return bytes(chunks)


def socks_request(port, host, target_port, command=1):
    sock = socket.create_connection(("127.0.0.1", port), timeout=3)
    sock.sendall(b"\x05\x01\x00")
    assert receive(sock, 2) == b"\x05\x00"
    address = host.encode()
    sock.sendall(bytes([5, command, 0, 3, len(address)]) + address
                 + struct.pack("!H", target_port))
    return sock


def runtime_checks(document, mihomo, directory, label):
    work = directory / label
    work.mkdir(exist_ok=True)
    # Reusing --output must not silently test yesterday's cached providers.
    for cached_provider in (work / "ruleset").glob("*.list"):
        cached_provider.unlink()
    mixed, controller = free_port(), free_port()
    with Sink(("127.0.0.1", 0), SinkHandler) as sink:
        thread = threading.Thread(target=sink.serve_forever, daemon=True)
        thread.start()
        # Keep actual generated policies/rules; only dummy transports and ports
        # are changed to prevent contacting real services.
        for proxy in document["proxies"]:
            proxy["port"] = sink.server_address[1]
        document.update({
            "port": 0, "socks-port": 0, "mixed-port": mixed, "allow-lan": False,
            "external-controller": f"127.0.0.1:{controller}",
            "log-level": "debug",
            "geox-url": {
                "geoip": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.dat",
                "geosite": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat",
                "mmdb": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/country.mmdb",
            },
        })
        # Download once and reuse the real geodata in the second config test.
        for name in ("GeoSite.dat", "geoip.metadb", "country.mmdb"):
            shared = directory / name
            if shared.exists() and not (work / name).exists():
                (work / name).symlink_to(shared)
        config_path = work / "config.yaml"
        config_path.write_text(yaml.safe_dump(document, allow_unicode=True))
        result = subprocess.run([mihomo, "-t", "-d", str(work), "-f", str(config_path)],
                                capture_output=True, text=True, timeout=120)
        (work / "validation.log").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stdout + result.stderr
        # After validating the unchanged generated policies, isolate runtime
        # traffic: DIRECT-only groups use a dummy transport too. All rule order,
        # payloads and group names remain unchanged. TEST-NET hosts prevent LAN
        # rules from masking the domain-provider checks.
        for group in document["proxy-groups"]:
            if group["proxies"] == ["DIRECT"]:
                group["proxies"] = [document["proxies"][0]["name"]]
        fixture_hosts = [host for hosts in NEGATIVE.values() for host in hosts]
        fixture_hosts += [host for hosts in POSITIVE.values() for host in hosts]
        fixture_hosts += [row.split(",")[1] for name in POSITIVE for row in rules(name)
                          if row.split(",")[0] in ("DOMAIN", "DOMAIN-SUFFIX")]
        fixture_hosts += ["cdn.steamcontent.com", "normal-content.example.org",
                          "hm.baidu.com", "xdrig.com"]
        document["hosts"] = {host: "203.0.113.250" for host in fixture_hosts}
        runtime_path = work / "runtime.yaml"
        runtime_path.write_text(yaml.safe_dump(document, allow_unicode=True))
        log_path = work / "runtime.log"
        with log_path.open("w") as log:
            process = subprocess.Popen([mihomo, "-d", str(work), "-f", str(config_path)],
                                       stdout=log, stderr=subprocess.STDOUT)
            api = f"http://127.0.0.1:{controller}"
            try:
                wait_for(lambda: json.loads(fetch(api + "/version")))
                wait_for(lambda: len(providers := (json.loads(fetch(api + "/providers/rules"))
                                                   .get("providers") or {})) == 4
                         and all(p.get("ruleCount", 0) > 0 for p in providers.values()),
                         timeout=30)
                for provider in document["rule-providers"].values():
                    source_name = provider["url"].rsplit("/", 1)[1]
                    assert (work / provider["path"]).read_bytes() == (ROOT / source_name).read_bytes()
                # First prove real HTTP provider initialization with the
                # generated DIRECT policies; then isolate only the transports.
                request = urllib.request.Request(api + "/configs?force=true",
                    data=json.dumps({"path": str(runtime_path)}).encode(),
                    headers={"Content-Type": "application/json"}, method="PUT")
                with urllib.request.urlopen(request, timeout=30) as response:
                    assert response.status == 204
                count = probe_routes(mixed, log_path, sink.server_address[1], work / "routes.json")
                print(f"{label}: Mihomo validation OK, {count} TCP/UDP route probes OK; "
                      f"{len(document['rules'])} generated rules")
                return count
            finally:
                process.terminate()
                process.wait(timeout=10)
                sink.shutdown()
                for name in ("GeoSite.dat", "geoip.metadb", "country.mmdb"):
                    source = work / name
                    if source.exists() and not source.is_symlink() and not (directory / name).exists():
                        source.rename(directory / name)


def probe_routes(port, log, sink_port, results_path):
    count = 0
    results = []
    expected = {"AI.list": ("ai", "🤖 AI"), "TikTok.list": ("tiktok", "🎵 TikTok"),
                "HongGuoAD.list": ("hongguo-ad", "红果广告")}

    def tcp(host, provider=None, group=None, target_port=443):
        nonlocal count
        offset = len(log.read_text())
        sock = socks_request(port, host, target_port)
        try:
            sock.sendall(b"route-probe")
            def evidence():
                return next((line for line in log.read_text()[offset:].splitlines()
                             if f"--> {host}:{target_port} " in line
                             and " match " in line and " using " in line), None)
            entry = wait_for(evidence)
            if provider:
                assert f"match RuleSet({provider})" in entry, (host, entry)
            else:
                assert not any(f"match RuleSet({name})" in entry
                               for name in ("ai", "tiktok", "hongguo-ad", "quic")), (host, entry)
                assert "IPCIDR(127.0.0.0/8)" not in entry, (host, entry)
            if group:
                choices = group if isinstance(group, tuple) else (group,)
                assert any(f"using {choice}[" in entry for choice in choices), (host, entry)
            if provider == "hongguo-ad" or group in ("🍃 应用净化", "🛑 广告拦截"):
                assert "[REJECT]" in entry, entry
            results.append({"network": "tcp", "host": host, "port": target_port,
                            "expected_provider": provider, "expected_group": group,
                            "evidence": entry})
            count += 1
        finally:
            sock.close()

    for name, (provider, group) in expected.items():
        hosts = list(POSITIVE[name])
        for row in rules(name):
            kind, value, *_ = row.split(",")
            if kind in ("DOMAIN", "DOMAIN-SUFFIX"):
                hosts.append(value)
        for host in dict.fromkeys(hosts):
            tcp(host, provider, group)
    # Real order checks against fetched upstream lists and shared-content domains.
    download_hosts = POSITIVE["Download.list"] + [row.split(",")[1] for row in rules("Download.list")]
    for host in dict.fromkeys(download_hosts):
        tcp(host, group="📦 下载节点")
    for host, group in [
        ("github.com", "🚀 节点选择"), ("api.github.com", "🚀 节点选择"),
        ("hub.docker.com", "🚀 节点选择"),
        ("router.huggingface.co", "🚀 节点选择"),
        ("registry.npmmirror.com", "🎯 全球直连"),
        ("mirrors.tuna.tsinghua.edu.cn", "🎯 全球直连"),
        ("pypi.tuna.tsinghua.edu.cn", "🎯 全球直连"),
        ("download-cdn.clf.jetbrains.com.cn", "🎯 全球直连"),
        ("dl.google.com", "🎯 全球直连"),
    ]:
        tcp(host, group=group)
    for host, group in [
        ("reading.snssdk.com", ("🎯 全球直连", "🎞️ 国内媒体")),
        ("p3-reading.byteimg.com", "🎯 全球直连"),
        ("api.fqnovel.com", None),
        ("cdn.steamcontent.com", "🎯 全球直连"),
        ("hm.baidu.com", "🍃 应用净化"),
        ("xdrig.com", "🛑 广告拦截"),
    ]:
        tcp(host, group=group, target_port=sink_port)
    # Optional lists may exclude domains deliberately covered by active providers.
    for host in dict.fromkeys(host for name in expected for host in NEGATIVE[name]):
        tcp(host, target_port=sink_port)
    tcp("normal-content.example.org", target_port=sink_port)

    # SOCKS5 UDP ASSOCIATE + actual datagrams, with TCP/443 already covered above.
    control = socks_request(port, "0.0.0.0", 0, command=3)
    try:
        reply = receive(control, 4)
        assert reply[:2] == b"\x05\x00", reply
        address = receive(control, 4) if reply[3] == 1 else receive(control, 16)
        relay_port = struct.unpack("!H", receive(control, 2))[0]
        relay = (str(ipaddress.ip_address(address)), relay_port)
        if relay[0] == "0.0.0.0":
            relay = ("127.0.0.1", relay_port)
        for host, dst_port, match in [
                ("api.openai.com", 443, "quic"),
                ("api.openai.com", 3478, "ai"),
                ("api.openai.com", 53, "ai"),
                ("www.tiktok.com", 443, "quic"),
                ("ad.zijieapi.com", 443, "hongguo-ad"),
                ("127.0.0.1", 443, "全球直连"),
        ]:
            offset = len(log.read_text())
            # New source ports avoid reusing a prior UDP NAT session.
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp:
                data = host.encode()
                packet = b"\x00\x00\x00\x03" + bytes([len(data)]) + data
                packet += struct.pack("!H", dst_port) + b"udp-route-probe"
                udp.sendto(packet, relay)
                entry = wait_for(lambda: next((line for line in log.read_text()[offset:].splitlines()
                                              if f"{host}:{dst_port}" in line and match in line
                                              and " match " in line), None))
                if match in ("quic", "hongguo-ad"):
                    assert f"RuleSet({match})" in entry and "[REJECT]" in entry, entry
                results.append({"network": "udp", "host": host, "port": dst_port,
                                "expected_provider": match, "evidence": entry})
                count += 1
    finally:
        control.close()
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subconverter-url", default="http://127.0.0.1:25509")
    parser.add_argument("--mihomo", required=True)
    parser.add_argument("--remote-cache", type=Path)
    parser.add_argument("--output", type=Path, help="Keep configs/logs for inspection")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="rules-integration-") as temporary:
        directory = args.output or Path(temporary)
        directory.mkdir(parents=True, exist_ok=True)
        fixture = directory / "fixtures"
        fixture.mkdir(exist_ok=True)
        with fixture_server(fixture) as prefix:
            prepare_fixtures(fixture, prefix, args.remote_cache)
            documents = {kind: convert(args.subconverter_url, prefix, "baixiaosheng." + kind)
                         for kind in ("ini", "toml")}
            assert documents["ini"] == documents["toml"], "INI/TOML conversion differs"
            print("Subconverter:", fetch(args.subconverter_url.rstrip("/") + "/version").decode().strip())
            total = sum(runtime_checks(doc, args.mihomo, directory, kind)
                        for kind, doc in documents.items())
            print(f"Integration: {total} native route probes passed; INI/TOML output identical")


if __name__ == "__main__":
    main()
