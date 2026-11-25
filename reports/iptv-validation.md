# IPTV 地区分流验证（2026-11-26）

香港、台湾、日本的 IPTV 规则已合入现有 Mandatory 列表。TVB 翡翠台、TVB Plus、凤凰中文台、凤凰资讯台走香港节点，KBS WORLD 中转走韩国节点。澳广视使用香港节点作为当前可用的邻近出口。

`📺 IPTV中转` 当前负责 BreadTV、Love Nature 4K 和 CGTN Rakuten 公网线路，默认香港。这些是跨区分发的线路，保留独立的出口选择。

主播放列表 98 条公网线路的入口与已观察到的媒体主机均覆盖，共 80 条精确域名和 3 条单一 IP 规则。局域网组播通过第一层局域网规则优先匹配。[线路与规则映射](iptv-routing.json)

离线检查通过。Subconverter 转换的 INI 与 TOML 输出相同，Mihomo 通过 878 次 TCP/UDP 路由探测，两份配置均验证了 83 个不同 IPTV 主机或 IP 的策略命中。[路由验证记录](iptv-engine-routes.json)

家庭网关现有节点的 HTTP 初查中，澳视澳门、澳门资讯、客家电视台、EBS 1TV 和 NBC News NOW 的入口在对应节点上返回 HTTP 200，直连对照未通过。13 条新增线路在当前家庭网络通过两轮媒体解码和人工画面核对。新规则在隔离实例验证，家庭网关要在更新订阅并重载后才会用上这份规则。HTTP 初查只探测入口响应。[补源、画面与地区探测记录](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/country-expansion.md)

本次网上补源新增 26 个频道。ViuTV、澳广视卫星 96、NHK 综合台与新增台日韩美线路的媒体主机均按表绑定。两轮取流与画面核对见 [公开补源报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/web-expansion.md)。

主流台专项新增 HOY 76、77、78 和 SBS JTV 全州。HOY 的两个精确主机走香港，JTV 的单一 IP 走韩国。两条香港出口及韩国出口均通过地区定位，媒体测试使用本机隔离的代理实例。[主流台专项报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-priority.md)

台湾线路复测新增民视新闻台和原住民族电视台。民视新闻台复用台湾组已有单一 IP 规则，原住民族电视台按精确媒体域名分流。两路均在软路由的两条 `twl` 线路上通过媒体解码和节目画面核对。[台湾播放复测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/twl-playback.md)

日本、美国和澳门新增 24 条直播线路。日本组新增 3 条精确域名，美国组新增 10 条，澳视葡文复用香港组。新增线路均通过对应出口的多轮解码和节目画面核对。[本轮补源与播放测试](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/variety-expansion.md)
