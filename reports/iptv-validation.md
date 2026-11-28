# IPTV 地区分流验证

香港、台湾、日本的 IPTV 规则已合入现有 Mandatory 列表。TVB 翡翠台、TVB Plus、凤凰中文台、凤凰资讯台走香港节点，KBS WORLD 中转走韩国节点。澳广视使用香港节点作为当前可用的邻近出口。

原 `📺 IPTV中转` 策略组已从 INI 和 TOML 移除。软路由取流与连接记录确认 BreadTV、CGTN Rakuten 通过香港节点播放，Love Nature 4K 通过美国节点播放。CGTN Rakuten 走 `DIRECT` 时 TLS 连接超时。

主播放列表 146 条公网线路的入口与已观察到的媒体主机均覆盖，共 113 条精确域名和 10 条单一 IP 规则。局域网组播通过第一层局域网规则优先匹配。[线路与规则映射](iptv-routing.json)

离线检查通过。Subconverter 转换的 INI 与 TOML 输出相同，均未生成旧中转策略组。Mihomo 通过 958 次 TCP/UDP 路由探测，两份配置均验证了 123 个不同 IPTV 主机或 IP 的策略命中。[路由验证记录](iptv-engine-routes.json)

家庭网关现有节点的 HTTP 初查中，澳视澳门、澳门资讯、客家电视台、EBS 1TV 和 NBC News NOW 的入口在对应节点上返回 HTTP 200，直连对照未通过。13 条新增线路在当前家庭网络通过两轮媒体解码和人工画面核对。新规则在隔离实例验证，家庭网关要在更新订阅并重载后才会用上这份规则。HTTP 初查只探测入口响应。[补源、画面与地区探测记录](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/country-expansion.md)

本次网上补源新增 26 个频道。ViuTV、澳广视卫星 96、NHK 综合台与新增台日韩美线路的媒体主机均按表绑定。两轮取流与画面核对见 [公开补源报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/web-expansion.md)。

主流台专项新增 HOY 76、77、78 和 SBS JTV 全州。HOY 的两个精确主机走香港，JTV 的单一 IP 走韩国。两条香港出口及韩国出口均通过地区定位，媒体测试使用本机隔离的代理实例。[主流台专项报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-priority.md)

台湾线路复测新增民视新闻台和原住民族电视台。民视新闻台复用台湾组已有单一 IP 规则，原住民族电视台按精确媒体域名分流。两路均在软路由的两条 `twl` 线路上通过媒体解码和节目画面核对。[台湾播放复测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/twl-playback.md)

日本、美国和澳门新增 24 条直播线路。日本组新增 3 条精确域名，美国组新增 10 条，澳视葡文复用香港组。新增线路均通过对应出口的多轮解码和节目画面核对。[本轮补源与播放测试](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/variety-expansion.md)

主流台复查新增 TVB 明珠台、ViuTVsix 和 SBS 江原 G1。香港两路复用已有入口和媒体域名规则，韩国组新增 G1 的单一 IP。软路由订阅更新并重载后应用这份配置。[主流台复查报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-followup.md)

播出时段复测新增无线新闻台、凤凰香港台、台湾五个主频和 KBS 1TV／2TV。香港组加入一个域名和一个单一 IP，台湾组加入五个主频共用的单一 IP，韩国组加入 KBS 的入口、媒体和密钥域名。台湾线路按指定使用 `twl` 验证。[播出时段复测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/mainstream-daytime.md)

MBC 本台通过韩国出口连续播放，入口复用 `KrMandatory.list` 的已有规则，新增精确媒体域名 `live.imnews.imbc.com`。[两台播放验证](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/seoul-main-tv.md)

## SBS 本台

`KrMandatory.list` 包含固定入口 `www.hwado.net` 和媒体主机 `tvlive.sbs.co.kr`。INI 和 TOML 生成的配置均将两个域名分流到 `🇰🇷 韩国节点`。韩国出口由软路由上的韩国组成员决定。[SBS 播放复测](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/sbs-route-retest.md)

2026-11-27 更新软路由的 `subscribepro` 订阅并重载 Nikki，韩国组的生效规则由 15 条增至 22 条。连接记录确认 `www.hwado.net` 和 `tvlive.sbs.co.kr` 均命中精确域名规则并经 `🇰🇷 韩国节点` 转至 `kr_jp_cdt->oracle`，分别观察到 1 条和 158 条连接。操作前后核对的 36 个策略组类型、成员及固定选择一致。

SBS 本台 720p 经该软路由连续取流 240.001 秒，H.264 视频和 AAC 音频均无超过 250 毫秒的时间戳间隔。全段解码通过，无分片跳过或 HTTP 错误。[实测样本和路由记录](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/sbs-route-retest.md#2026-11-27-软路由实测)

## 2026-11-27 韩国地方台与美国新闻气象补源

新增韩国 15 个频道和美国 2 个频道。`KrMandatory.list` 新增 12 个精确域名和 4 个单一 IP，覆盖 YTN、MBC 地方台及 SBS 地方联播台等。`USMandatory.list` 新增 CBS News 24/7 的专用媒体域名，WeatherNation 复用美国组已有的 Roku 主机规则。[本轮取流和画面复测](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/regional-local-expansion.md)

## 2026-11-28 港澳台日韩美补源

新增 14 路，其中香港 4、日本 1、韩国 2、美国 7。香港线路复用 `HkMandatory.list` 的已有规则。`KrMandatory.list` 新增 2 条精确域名规则。`USMandatory.list` 新增 8 条精确域名规则。`JpMandatory.list` 复用 Fast TV 的已有规则。对应地区的入口、跳转和媒体主机已写入映射表。[本轮实测报告](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/regional-live-expansion.md)

## 2026-11-28 澳门、台湾和日本地面台补源

`TwMandatory.list` 新增 `live.ntdtv.com` 和 `mobile.ccdntech.com`。两路直播均在两个与软路由同名节点出口 IP 一致的 `twl` 测试实例上连续解码约 45 秒。TUY 山形台复用 `JpMandatory.list` 的 `tv-stream-test.daydreamer-json.cc`，在两条日本线路上连续解码 34.08 秒。[本轮播放验证](https://github.com/baixiaoshengofficial/shtelcomiptv/blob/main/reports/macau-taiwan-japan.md)
