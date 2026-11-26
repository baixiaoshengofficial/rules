# IPTV 地区分流验证（2026-11-26）

香港、台湾、日本的 IPTV 规则已合入现有 Mandatory 列表。TVB 翡翠台、TVB Plus、凤凰中文台、凤凰资讯台走香港节点，KBS WORLD 中转走韩国节点。澳广视使用香港节点作为当前可用的邻近出口。

原 `📺 IPTV中转` 策略组已从 INI 和 TOML 移除。软路由取流与连接记录确认 BreadTV、CGTN Rakuten 通过香港节点播放，Love Nature 4K 通过美国节点播放。CGTN Rakuten 走 `DIRECT` 时 TLS 连接超时。

主播放列表 112 条公网线路的入口与已观察到的媒体主机均覆盖，共 88 条精确域名和 6 条单一 IP 规则。局域网组播通过第一层局域网规则优先匹配。[线路与规则映射](iptv-routing.json)

离线检查通过。Subconverter 转换的 INI 与 TOML 输出相同，均未生成旧中转策略组。Mihomo 通过 900 次 TCP/UDP 路由探测，两份配置均验证了 94 个不同 IPTV 主机或 IP 的策略命中。[路由验证记录](iptv-engine-routes.json)

家庭网关现有节点的 HTTP 初查中，澳视澳门、澳门资讯、客家电视台、EBS 1TV 和 NBC News NOW 的入口在对应节点上返回 HTTP 200，直连对照未通过。13 条新增线路在当前家庭网络通过两轮媒体解码和人工画面核对。新规则在隔离实例验证，家庭网关要在更新订阅并重载后才会用上这份规则。HTTP 初查只探测入口响应。[补源、画面与地区探测记录](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/country-expansion.md)

本次网上补源新增 26 个频道。ViuTV、澳广视卫星 96、NHK 综合台与新增台日韩美线路的媒体主机均按表绑定。两轮取流与画面核对见 [公开补源报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/web-expansion.md)。

主流台专项新增 HOY 76、77、78 和 SBS JTV 全州。HOY 的两个精确主机走香港，JTV 的单一 IP 走韩国。两条香港出口及韩国出口均通过地区定位，媒体测试使用本机隔离的代理实例。[主流台专项报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-priority.md)

台湾线路复测新增民视新闻台和原住民族电视台。民视新闻台复用台湾组已有单一 IP 规则，原住民族电视台按精确媒体域名分流。两路均在软路由的两条 `twl` 线路上通过媒体解码和节目画面核对。[台湾播放复测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/twl-playback.md)

日本、美国和澳门新增 24 条直播线路。日本组新增 3 条精确域名，美国组新增 10 条，澳视葡文复用香港组。新增线路均通过对应出口的多轮解码和节目画面核对。[本轮补源与播放测试](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/variety-expansion.md)

主流台复查新增 TVB 明珠台、ViuTVsix 和 SBS 江原 G1。香港两路复用已有入口和媒体域名规则，韩国组新增 G1 的单一 IP。软路由订阅更新并重载后应用这份配置。[主流台复查报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-followup.md)

播出时段复测新增无线新闻台、凤凰香港台、台湾五个主频和 KBS 1TV／2TV。香港组加入一个域名和一个单一 IP，台湾组加入五个主频共用的单一 IP，韩国组加入 KBS 的入口、媒体和密钥域名。台湾线路按指定使用 `twl` 验证。[播出时段复测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-daytime.md)

MBC 本台通过韩国出口连续播放，入口复用 `KrMandatory.list` 的已有规则，新增精确媒体域名 `live.imnews.imbc.com`。[两台播放验证](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/seoul-main-tv.md)

## SBS 本台

`KrMandatory.list` 包含固定入口 `www.hwado.net` 和媒体主机 `tvlive.sbs.co.kr`。两份订阅配置都将它们分流到 `🇰🇷 韩国节点`。节目实测通过的路径为 `hk_cdt->hkl → kr_oracle`，由韩国出网。[播放复测](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/sbs-route-retest.md)

`🇰🇷 韩国节点` 内的 `🇰🇷 韩国（香港接入）` 从内联提供器 `kr-via-hk` 加载链路。韩国组默认优先尝试原有韩国节点；香港接入线路可在面板内选择。提供器初始只有拒绝流量的占位节点，需通过 Nikki 本地混入填入实际节点。使用实际节点在隔离 Mihomo 实例复测，Cloudflare 和 IPPure 均确认韩国出口，SBS 连续播放 45 秒无跳段。[Mihomo 前置代理](https://wiki.metacubex.one/en/config/proxies/dialer-proxy/) · [Nikki 混入先后顺序](https://github.com/nikkinikki-org/OpenWrt-nikki/blob/main/nikki/files/nikki.init)

在 Nikki 自定义配置混入的 `proxy-providers.kr-via-hk.payload` 中使用现有 `kr_oracle` 节点的配置，名称改为 `kr_oracle_via_hk`，副本加上 `dialer-proxy: "hk_cdt->hkl"`。自动让 SBS 走两跳线路时，将以下两条放入本地 `nikki-rules`。更新订阅并重载后生效。节点凭据由本地混入提供。

```yaml
nikki-rules:
  - DOMAIN,www.hwado.net,🇰🇷 韩国（香港接入）
  - DOMAIN,tvlive.sbs.co.kr,🇰🇷 韩国（香港接入）
```
