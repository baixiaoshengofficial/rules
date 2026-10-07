# Repository Guidelines

## Project Structure & Module Organization

This repository contains Subconverter configuration and routing rules for generating Clash/Mihomo subscriptions.

- `baixiaosheng.ini` is primary; `scripts/sync_config.py` generates the external `baixiaosheng.toml` configuration.
- `Google.list` combines scoped Google, FCM and YouTube rules; refresh it with `python3 scripts/update_google_rules.py`, then review the diff and run tests.
- Root-level `.list` files provide routing and blocking rules, including `AI.list`, `TikTok.list`, `Download.list`, regional `*Mandatory.list` files, `HongGuoAD.list`, and `block_quic.list`. `Residential.list` is an optional candidate list, not enabled by default.
- `clash-base.yaml` defines native Mihomo providers for AI, TikTok, HongGuo and QUIC. `iptvsh.m3u` contains IPTV channel metadata and stream URLs.
- `tests/` contains offline and integration checks; `README.md` explains routing, deployment and validation.


## Build, Test, and Development Commands

Run from the repository root:

- `sh tests/test_hongguo_rules.sh`: validate HongGuo rule syntax, duplicates, domain matching, and configuration references.
- `python3 tests/test_rules.py`: check syntax, coverage, false positives and policy order.
- `python3 scripts/sync_config.py --check`: detect configuration drift; omit `--check` to regenerate TOML.
- `MIHOMO_BIN=/path/to/mihomo sh tests/run_integration.sh`: run real converter/engine checks; prerequisites are in `README.md`.
- `git diff --check`: detect whitespace errors before committing.

No application build is required. Integration tests need Linux Docker, Mihomo, Python 3.11+ and PyYAML (`tests/requirements.txt`).

## Coding Style & Naming Conventions

Preserve UTF-8 encoding, Chinese labels, emoji, and existing file names. Write one comma-separated rule per line, such as `DOMAIN,ad.zijieapi.com` or `DOMAIN-SUFFIX,example.com`, without added spaces. Use `#` comments in lists/TOML and `;` comments in INI.

Keep configuration entries unindented; TOML uses spaces around `=`. Shell scripts use POSIX `sh`, `set -eu`, and two-space indentation. No formatter or linter is configured. Preserve rule precedence; edit the INI and regenerate TOML. Native `AND` and `DOMAIN-REGEX` rules must remain in providers, because Subconverter filters them when expanding lists.

## Testing Guidelines

Tests use POSIX utilities and Python `unittest`; no coverage threshold is configured. Name checks `tests/test_<feature>.sh` or `tests/test_<feature>.py`. For HongGuo changes, add both expected blocked hosts and normal-content hosts that must remain accessible. Keep the HongGuo group restricted to `REJECT`; avoid blocking shared parent domains used for login or playback.

## Commit & Pull Request Guidelines

History uses short imperative subjects such as `Update baixiaosheng.ini` and `Improve HongGuo ad blocking rules`. Follow that style and keep commits focused.

PRs should identify affected files, intended routing behavior, and validation results. Link relevant issues when available. For behavior changes, include representative connection-log evidence and any false-positive checks.

## Configuration Safety

Do not commit subscription credentials or access tokens. Verify rule-source URLs and policy-group references when changing configuration. Treat IPTV LAN addresses as deployment-specific settings.
