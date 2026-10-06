#!/usr/bin/env python3
"""Offline coverage, false-positive, syntax and configuration regression checks."""

import ipaddress
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def rules(name):
    return [line for line in (ROOT / name).read_text().splitlines()
            if line and not line.startswith("#")]


def matches(name, host):
    for rule in rules(name):
        kind, value, *_ = rule.split(",")
        if kind == "DOMAIN" and host == value:
            return True
        if kind == "DOMAIN-SUFFIX" and (host == value or host.endswith("." + value)):
            return True
        if kind == "DOMAIN-KEYWORD" and value.lower() in host.lower():
            return True
        if kind == "DOMAIN-REGEX" and re.search(value, host):
            return True
    return False


POSITIVE = {
    "Download.list": [
        "release-assets.githubusercontent.com", "codeload.github.com",
        "objects.githubusercontent.com", "raw.githubusercontent.com", "ghcr.io",
        "npm.pkg.github.com", "pkg-containers.githubusercontent.com",
        "auth.docker.io", "registry-1.docker.io", "production.cloudflare.docker.com",
        "cdn01.quay.io", "us-west1-docker.pkg.dev", "registry.k8s.io",
        "huggingface.co", "cas-bridge.xethub.hf.co", "transfer.xethub-eu.hf.co",
        "us.gcp.cdn.hf.co", "cdn-lfs-us-1.hf.co", "registry.npmjs.org",
        "files.pythonhosted.org", "repo.maven.apache.org", "api.nuget.org",
        "static.crates.io", "proxy.golang.org", "static.rust-lang.org",
        "download-cdn.jetbrains.com", "vscode.download.prss.microsoft.com",
        "ms-python.gallerycdn.vsassets.io",
    ],
    "Residential.list": [
        "chatgpt.com", "api.openai.com", "sora.com", "files.oaiusercontent.com",
        "chatgpt-async-webps-prod-eastus-12.webpubsub.azure.com",
        "api.anthropic.com", "files.claudeusercontent.com", "claudemcpcontent.com",
        "generativelanguage.googleapis.com", "notebooklm.google.com",
        "api16-normal-c-useast1a.tiktokv.com", "shop.tiktokglobalshopv.com",
        "live.ttlivecdn.com", "p19.tiktokcdn-us.com", "www.netflix.com",
        "video.nflxvideo.net",
    ],
    "AI.list": [
        "api.openai.com", "chatgpt.com", "cdn.oaistatic.com",
        "files.oaiusercontent.com", "chatgpt.livekit.cloud", "turn.livekit.cloud",
        "us.turn.livekit.cloud",
        "openaiassets.blob.core.windows.net",
        "chatgpt-async-webps-prod-eastus-12.webpubsub.azure.com",
        "claude.ai", "files.claudeusercontent.com", "claudemcpcontent.com",
        "aistudio.google.com", "generativelanguage.googleapis.com",
        "notebooklm.google.com", "api.perplexity.ai", "api.deepseek.com",
    ],
    "TikTok.list": [
        "www.tiktok.com", "api16-normal-c-useast1a.tiktokv.com",
        "api.tiktokv.eu", "p16.tiktokcdn-eu.com", "p19.tiktokcdn-us.com",
        "live.ttlivecdn.com", "shop.tiktokglobalshopv.com", "api.tiktokminis.us",
        "p16-tiktokcdn-com.akamaized.net", "a.tiktokv.com.edgekey.net",
        "api.isnssdk.com", "p16.ibyteimg.com",
    ],
    "HongGuoAD.list": [
        "ad.zijieapi.com", "ads3-normal-lf.zijieapi.com",
        "ads12-normal-newregion.zijieapi.com", "ads9-normal.zijieapi.com",
        "p1-ad-sign.byteimg.com", "p19-ad-sign.byteimg.com",
        "log12-applog-newregion.fqnovel.com", "rtlog9-applog.fqnovel.com",
        "api-access.pangolin-sdk-toutiao.com", "dig.bdurl.net", "dig.zjurl.cn",
    ],
}
NEGATIVE = {
    "Download.list": [
        "github.com", "api.github.com", "avatars.githubusercontent.com",
        "login.microsoftonline.com", "account.jetbrains.com", "hub.docker.com",
        "api.openai.com", "router.huggingface.co", "inference.hf.co",
        "chatgpt.com", "www.tiktok.com", "www.netflix.com",
        "mirrors.tuna.tsinghua.edu.cn", "registry.npmmirror.com",
        "pypi.tuna.tsinghua.edu.cn", "cdn.steamcontent.com",
        "download-cdn.clf.jetbrains.com.cn", "dl.google.com",
        "other.s3.amazonaws.com", "other.blob.core.windows.net",
        "storage.googleapis.com", "other.cloudfront.net",
        "ghcr.io.example.org", "notdocker.example.org", "evil-huggingface.co",
    ],
    "Residential.list": [
        "api.deepseek.com", "github.com", "stripe.com", "auth0.com",
        "accounts.google.com", "storage.googleapis.com", "cloudflare.com",
        "other.webpubsub.azure.com", "turn.livekit.cloud", "api.statsig.com",
        "reading.snssdk.com", "p3-reading.byteimg.com", "www.douyin.com",
        "netflix.com.example.org", "not-tiktok.com", "claude.ai.example.org",
    ],
    "AI.list": [
        "stripe.com", "auth0.com", "sentry.io", "intercom.io",
        "maps.googleapis.com", "storage.googleapis.com",
        "myclaudestore.example", "openai.com.example.org",
        "other.blob.core.windows.net", "other.webpubsub.azure.com",
    ],
    "TikTok.list": [
        "reading.snssdk.com", "security.snssdk.com", "api.fqnovel.com",
        "www.douyin.com", "p3-reading.byteimg.com", "capcut.com", "trae.ai",
        "tiktok.com.example.org", "not-tiktok.com",
    ],
    "HongGuoAD.list": [
        "api.fqnovel.com", "reading.snssdk.com", "security.snssdk.com",
        "p3-reading.byteimg.com", "p9-novel-sign.byteimg.com",
        "v3-reading-video.fqnovelvod.com", "sf3-ttcdn-tos.pstatp.com",
        "hongguoduanju.com", "ads12-normal-newregion.zijieapi.com.example.org",
        "p19-ad-sign.byteimg.com.example.org",
    ],
}


class RuleTests(unittest.TestCase):
    def test_list_syntax_and_duplicates(self):
        for path in ROOT.glob("*.list"):
            entries = rules(path.name)
            self.assertEqual(len(entries), len(set(entries)), path.name)
            for rule in entries:
                fields = rule.split(",")
                kind, value = fields[:2]
                with self.subTest(file=path.name, rule=rule):
                    if kind in ("DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"):
                        self.assertEqual(len(fields), 2)
                        self.assertRegex(value, r"^[A-Za-z0-9_.-]+$")
                    elif kind == "DOMAIN-REGEX":
                        self.assertEqual(len(fields), 2)
                        re.compile(value)
                    elif kind in ("IP-CIDR", "IP-CIDR6"):
                        self.assertEqual(fields[2:], ["no-resolve"])
                        ipaddress.ip_network(value)
                    elif kind == "DST-PORT":
                        self.assertEqual(len(fields), 2)
                        self.assertTrue(0 < int(value) < 65536)
                    elif kind == "AND":
                        self.assertEqual(rule, "AND,((NETWORK,UDP),(DST-PORT,443))")
                    else:
                        self.fail(f"Unsupported rule: {rule}")

    def test_service_coverage(self):
        # Every explicit domain/suffix must match, plus independently chosen
        # real service endpoints and rotating shards.
        for name, hosts in POSITIVE.items():
            for rule in rules(name):
                kind, value, *_ = rule.split(",")
                if kind in ("DOMAIN", "DOMAIN-SUFFIX"):
                    hosts = hosts + [value]
                    if kind == "DOMAIN-SUFFIX":
                        hosts = hosts + ["coverage." + value]
            for host in hosts:
                with self.subTest(file=name, host=host):
                    self.assertTrue(matches(name, host))

    def test_normal_content_and_shared_services(self):
        for name, hosts in NEGATIVE.items():
            for host in hosts:
                with self.subTest(file=name, host=host):
                    self.assertFalse(matches(name, host))

    def test_group_graph(self):
        config = tomllib.loads((ROOT / "baixiaosheng.toml").read_text())
        groups = {g["name"]: g for g in config["custom_groups"]}
        self.assertEqual(len(groups), len(config["custom_groups"]), "Duplicate group names")
        edges = {}
        for name, group in groups.items():
            choices = group["rule"]
            self.assertEqual(len(choices), len(set(choices)), name)
            self.assertTrue(choices, name)
            refs = [ref[2:] for ref in choices if ref.startswith("[]")]
            self.assertTrue(set(refs) <= set(groups) | {"DIRECT", "REJECT"}, name)
            edges[name] = [ref for ref in refs if ref in groups]
        visited, active = set(), set()

        def visit(name):
            self.assertNotIn(name, active, f"Circular group reference: {name}")
            if name in visited:
                return
            active.add(name)
            for child in edges[name]:
                visit(child)
            active.remove(name)
            visited.add(name)

        for rule in config["rulesets"]:
            visit(rule["group"])
        self.assertEqual(visited, set(groups), "Unreachable groups")

    def test_config_sync_and_precedence(self):
        subprocess.run([sys.executable, str(ROOT / "scripts/sync_config.py"),
                        "--check"], check=True)
        config = tomllib.loads((ROOT / "baixiaosheng.toml").read_text())
        self.assertEqual(config["version"], 1)
        self.assertTrue(config["custom"]["enable_rule_generator"])
        self.assertTrue(config["custom"]["overwrite_original_rules"])
        sources = [r["ruleset"] for r in config["rulesets"]]
        self.assertIn("LocalAreaNetwork.list", sources[0])
        self.assertEqual(sources[1:5], [
            "[]RULE-SET,hongguo-ad", "[]RULE-SET,quic",
            "[]RULE-SET,ai", "[]RULE-SET,tiktok",
        ])
        direct = next(i for i, s in enumerate(sources) if s.endswith("/Direct.list"))
        ads = next(i for i, s in enumerate(sources) if s.endswith("/BanProgramAD.list"))
        self.assertLess(ads, direct)
        download = next(i for i, s in enumerate(sources) if s.endswith("/rules/main/Download.list"))
        github = next(i for i, s in enumerate(sources) if s.endswith("/GitHub.list"))
        self.assertLess(ads, download)
        self.assertLess(download, github)
        self.assertLess(download, direct)
        for host in ("notdocker.example.org", "ghcr.io.example.org", "evil-huggingface.co"):
            self.assertFalse(matches("ProxyLite.list", host), host)
        self.assertNotIn("DOMAIN-KEYWORD,steamcontent", rules("ProxyLite.list"))
        self.assertFalse(any("jokerknight" in s or "GEOIP,!CN" in s for s in sources))
        self.assertEqual(sources[-2:], ["[]GEOIP,CN", "[]FINAL"])
        groups = {g["name"]: g for g in config["custom_groups"]}
        self.assertEqual(groups["红果广告"]["rule"], ["[]REJECT"])
        for rule in config["rulesets"]:
            self.assertIn(rule["group"], groups)
        for group in groups.values():
            if group["type"] == "load-balance":
                self.assertEqual(group["strategy"], "consistent-hashing")
            for ref in group["rule"]:
                if ref.startswith("[]"):
                    self.assertIn(ref[2:], set(groups) | {"DIRECT", "REJECT"})


if __name__ == "__main__":
    unittest.main()
