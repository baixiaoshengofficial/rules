#!/usr/bin/env python3
"""Refresh the scoped Google/FCM/YouTube snapshot; inspect the diff before publishing."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Google/Google.list',
    'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/GoogleFCM/GoogleFCM.list',
    'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/GoogleCN.list',
    'https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/YouTube.list',
]


def fetch(url):
    with urlopen(url, timeout=60) as response:
        return response.read().decode('utf-8-sig')


def main():
    entries = set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for content in pool.map(fetch, SOURCES):
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith(('#', ';', 'DOMAIN-KEYWORD,')):
                    continue
                kind = line.split(',')[0]
                # Gateway routing has no reliable client process identity.
                if kind == 'PROCESS-NAME':
                    continue
                if kind not in {'DOMAIN', 'DOMAIN-SUFFIX', 'IP-CIDR', 'IP-CIDR6'}:
                    raise ValueError(f'Review unsupported upstream rule: {line}')
                if kind.startswith('IP-CIDR') and not line.endswith(',no-resolve'):
                    raise ValueError(f'Review DNS-resolving upstream rule: {line}')
                entries.add(line)
    # These service suffixes replace keywords; other country domains come from upstream.
    entries.update('DOMAIN-SUFFIX,' + domain for domain in
                   ['google.com', 'gmail.com', 'blogspot.com', 'appspot.com', 'recaptcha.net', 'youtube.com', 'dns.google'])
    suffixes = {r.split(',')[1] for r in entries if r.startswith('DOMAIN-SUFFIX,')}
    kept = []
    for row in entries:
        kind, value, *_ = row.split(',')
        if kind in {'DOMAIN', 'DOMAIN-SUFFIX'}:
            if any(value.endswith('.' + suffix) or (kind == 'DOMAIN' and value == suffix)
                   for suffix in suffixes):
                continue
        kept.append(row)
    header = [
        '# Google / FCM / YouTube 合并快照；由 scripts/update_google_rules.py 更新。',
        '# 去掉宽泛关键字，合并重复和被父域覆盖的规则；不声明覆盖所有未来域名。',
        '# AI、下载、广告及 dl.google.com / dl.l.google.com / time.google.com 例外由 INI 优先处理。',
        '# 上游更新时间：' + date.today().isoformat(),
        *['# ' + source for source in SOURCES],
    ]
    (ROOT / 'Google.list').write_text('\n'.join(header + sorted(kept)) + '\n')
    print(f'Google.list: {len(entries)} unique input rules -> {len(kept)} scoped rules')


if __name__ == '__main__':
    main()
