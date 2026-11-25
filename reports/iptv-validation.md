# IPTV 分流验证（2026-11-25）

## 变更与匹配范围

七份 IPTV 列表共 30 条精确域名规则、两条 /32 IP 规则，覆盖主播放列表当前 29 条公网线路：原有 26 条和本次新增港台电视 32、33、34。入口、重定向、已下载分片和主清单显式音轨的主机均已对应策略，完整映射见 [iptv-routing.json](iptv-routing.json)。港台电视 35 也预留同地区的域名规则，但媒体清单 404，播放列表中没有该项。

局域网代理和组播地址未加入公网分流，不改路由器配置。共享 CDN 只匹配具体主机；同主机下的不同频道无法按域名拆分。IP 规则只限定单一地址，仍可能影响这个 IP 上的其他节目和端口。地区规则在通用媒体和 GEOIP 之前，国内直播明确直连。

## 测试结果

- `sh tests/test_hongguo_rules.sh`：通过。
- `python3 tests/test_rules.py`：6 项通过，涵盖 IPTV 策略引用、顺序、共享 CDN 反例、IP 边界、韩国筛选、组循环及配置同步。
- `python3 scripts/sync_config.py --check` 与 `git diff --check`：通过。
- Subconverter v0.9.0-a0d4eab + Mihomo v1.19.34：INI/TOML 完整转换输出相同，57,519 条生成规则。
- 实际 Mihomo TCP/UDP 路由测试共 778 次通过；每份配置均验证 32 个不同 IPTV 目标的策略命中，包含媒体跳转主机和两个裸 IP。地区筛选、空地区 REJECT，以及主节点故障和恢复的回退/回切通过。证据见 [iptv-engine-routes.json](iptv-engine-routes.json)。这些隔离测试使用本地接收端，不表示真实代理带宽。

集成运行在 macOS Docker Desktop：使用仓库原有 `test_integration.py`，临时测试包装器仅将 HTTP fixture 绑定到本机局域网接口，使容器可读取待发布文件；转换、Mihomo 校验与路由测试逻辑均未替换。没有使用真实订阅凭据，也没有把测试 YAML 部署到路由器。

## 家庭网络实测与新增线路

原有 26 条公网源均下载真实媒体并成功解码，其中香港电台第二台第一次 TLS 超时，单独重测通过。新增港台电视 32、33、34 均经过两轮媒体解码并核对画面；33、34 是央视一套和 CGTN Documentary 转播。测试时连接记录命中旧规则 `DomainSuffix(akamaized.net)`，经通用节点组和手动组使用香港命名出口；没有切换策略或全局模式。新增三路均为 1920×1080。

HTTP 出口对照中，NHK 日本节点约 60 ms、直连约 319 ms；Arirang 韩国节点约 61 ms、直连约 223 ms。这是控制接口的 URL 健康探测，不能代表分片传输速率，更不能仅据此添加频道。港台电视 35 的入口健康探测成功，但媒体清单返回 404；大爱源媒体 GET 返回 403；澳门、明珠候选探测仍失败。均未加入播放列表。

完整媒体报告、HTTP 对照及失败原因见 [IPTV 仓库地区验证](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/regional-validation.md)。当前结果属于短样本测试，后续可用性仍取决于节点出口、源站、地区和节目限制。

## 生效方式

本次已修改的是 GitHub 规则源，需要在 Nikki/OpenClash 更新订阅并重载，再刷新播放器。七份列表由 Subconverter 展开，不是原生 provider；仅刷新四个旧 provider 不足以加载新列表。新配置应出现 `📺 IPTV中转` 和 `🇰🇷 韩国节点`。中转组默认香港，可单独试其他地区或直连；韩国组缺少韩国节点时会拒绝，需检查生成后的成员。

本次未替换运行中的路由器配置，未切换用户已有策略选择，因此没有声称新规则已在家庭网关上线，也没有声称所有频道都已因新规则提速。
