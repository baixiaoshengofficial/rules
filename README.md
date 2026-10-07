# rules

用于 Subconverter 生成 Nikki / Clash/Mihomo 订阅的自用规则。以 `baixiaosheng.ini` 为主，
`baixiaosheng.toml` 由脚本同步生成，作为 Subconverter 外部配置使用。

## 使用与更新

将配置、`clash-base.yaml` 和所有 `.list` 文件一起发布到本仓库 `main`，再更新 Nikki 订阅。
四个重点规则集由 Mihomo 原生 `classical/text` provider 每 24 小时更新，更新订阅不一定会
立刻刷新已有 provider 缓存；修改规则后，在面板的规则集合中手动更新对应 provider，并检查加载数量。

INI 引用 `clash-base.yaml`，后者定义 `hongguo-ad`、`quic`、`ai`、`tiktok` 四个 provider。
不要直接把这些文件交给 Subconverter 展开：上游 Clash 转换器会过滤文件里的 `AND` 和
`DOMAIN-REGEX`。配置通过内联 `RULE-SET` 保留集合引用，交给 Mihomo 解析。需要支持这些规则的
Mihomo 内核；本次集成验证使用 v1.19.32。此配置不面向原版 Clash 或其他代理客户端。

## 分流顺序

局域网 → 红果广告 → UDP/443 → AI/TikTok → 必要白名单 → 广告/隐私 → 开发下载 → 地区与服务 →
国内直连 → GEOSITE/GEOIP → 漏网之鱼。

- 红果固定 `REJECT`；广告调度、素材和日志分片使用限定域名的正则，覆盖编号及区域轮换。
  保留正常封面、播放、登录所用的大域，避免把 `byteimg.com`、`snssdk.com`、`pstatp.com` 整站封禁。
  更新后重启红果并清理旧广告缓存；命中应显示 `红果广告 / REJECT`。
- QUIC 集合只匹配 **UDP/443**，默认 `REJECT`，不阻断 TCP/443、UDP/53 或 UDP/3478。
  局域网及红果规则先匹配；若要允许 UDP/443，可切换 `🛑 QUIC` 到代理或直连。
  其他端口的 QUIC 不在这个端口规则的覆盖范围内。
- AI 补充 Claude 文件/MCP、ChatGPT 语音/异步 WebSocket、Gemini API、NotebookLM、
  Perplexity、DeepSeek。共享支付、认证、监控和云平台大域不再整体归入 AI。
- TikTok 补充欧美 CDN、直播和商店，优先于通用国内/媒体规则；排除共享 `snssdk.com` 和其他产品。
  分流命中不能替代地区限制、账号、SIM 卡或节点出口的验证。
- Steam 下载例外先于代理补充规则；大范围国内直连在广告规则之后，必要 `UnBan` 白名单保留。
- 均衡组采用 `consistent-hashing`；地区筛选支持英文代码、中文和 emoji 名称，故转及自动选择可从选择组使用。
  节点确实缺少某地区时仍需检查生成后的组成员，不能靠正则创造可用节点。
- 默认保留 BanAD、BanProgramAD 和隐私规则；移除未使用的 AdBlock 分组及停用配置。
  如需额外启用 ACL4SSR 的 `BanEasyList.list` / `BanEasyListChina.list`，在 INI 的
  `BanEasyPrivacy.list` 后添加 `ruleset=🛑 广告拦截,<列表 URL>`，再同步 TOML。
  必须放在服务规则和 `FINAL` 之前，追加到 `FINAL` 后不会生效。

## 策略组选择

- `🚀 节点选择` 集中提供地区、家宽、均衡和自动选择；地区组可进入相应故障转移组。
- AI、TikTok 保留独立地区及家宽入口，便于固定服务出口；Netflix 保留专用节点入口。
- Microsoft、Apple、游戏、国外媒体、漏网之鱼精简为节点选择、手动切换、直连；
  Speedtest 提供同样三个选项，默认直连。默认出口顺序不变。
  这些服务的地区选择统一由 `🚀 节点选择` 控制；`🐸 手动切换` 也是共享选择器，
  修改它会影响所有引用它的服务。如需为某服务单独固定地区，在该服务 INI 分组中
  添加对应引用（例如 `` `[]🇯🇵 日本节点``），再同步 TOML。

## Google 分组边界

`Google.list` 合并 Google、GoogleCN、FCM 和 YouTube，统一交给 `🎵 Google`；
YouTube 网页、API、视频和图片 CDN 使用同一分组，FCM 推送也跟随该组。
AI、下载和广告过滤仍优先；`dl.google.com`、`dl.l.google.com`、`time.google.com`
及其子域在 INI 中明确直连，不跟随 Google。

该快照去掉 `google`、`gmail`、`youtube` 等任意子串关键字，保留明确域名、后缀及
带 `no-resolve` 的 IP 规则。无关名称不会因此进入 Google 组；其他通用代理列表仍可能命中它们。
`dns.google` 属于 Google 组，但 Mihomo 内置 DNS 是否使用该组取决于最终 DNS 上游配置。

运行 `python3 scripts/update_google_rules.py` 从文件头列出的四个上游重新生成快照，
审阅差异后运行离线与集成测试。网关无法可靠识别客户端进程，快照不收录进程名规则。
与直接订阅上游不同，该快照需要显式更新并发布，随后更新订阅。

## 家宽候选列表

`Residential.list` 是按服务分段的可选覆盖列表，默认未接入 INI/TOML。
它表示可用家宽做对照测试的目标，不代表这些服务强制住宅 IP，也不是完整服务依赖清单。
所有分段都是有效规则，接入前按需要裁剪；已有节点正常使用时，无需切换。

| 服务 | 纳入理由及证据边界 |
| --- | --- |
| ChatGPT / OpenAI / Sora | 优先排查出口 IP 的候选；[官方错误排查](https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages)提到被标记的代理 IP，但未承诺家宽能解决。Sora 随同服务域名纳入，不表示其要求家宽。 |
| Claude | 条件候选；[官方说明](https://support.claude.com/en/articles/8461763-where-can-i-access-claude)给出可用地区，没有家宽要求。 |
| Gemini / AI Studio / NotebookLM | 条件候选；[AI Studio/Gemini API 文档](https://ai.google.dev/gemini-api/docs/available-regions)列出地区、年龄及验证条件。NotebookLM 随现有 Google AI 规则列为候选，各产品资格需分别检查。 |
| TikTok | 根据本仓库关注范围纳入账号、直播、商店及专属 CDN，作为固定出口对照候选；本次未获得可核验的官方家宽要求。 |
| Netflix | 播放异常时的条件候选；[官方说明](https://help.netflix.com/en/node/114701)指出 VPN 可能影响片库，直播和广告套餐不支持 VPN；家宽代理也不能保证解除限制。 |

以上家宽选择建议是运维判断，不是服务商要求。未将 DeepSeek、GitHub、下载、游戏、红果、
银行或支付网站整体纳入；现有证据不足以支持它们统一强制家宽。
共享的 Google 登录、Stripe、Auth0、Cloudflare、LiveKit TURN 和字节跳动大域也未整体纳入，
因此登录跳转、语音、部分 CDN 仍可能走原策略。需要整类 AI/TikTok 同出口时，优先使用现有
`🤖 AI` / `🎵 TikTok` 分组选择家宽，减少维护重复名单。

如启用该文件，在 `clash-base.yaml` 增加名为 `residential` 的 HTTP provider，使用
`behavior: classical`、`format: text`、`interval: 86400`、独立缓存路径
`./ruleset/residential.list`，URL 指向本仓库发布后的 `Residential.list`。
在 INI 的 QUIC 引用之后、AI 引用之前加入：

```ini
ruleset=🏡 家宽节点,[]RULE-SET,residential
```

然后运行同步脚本生成 TOML。该优先级保留局域网、红果、UDP/443 拦截，候选域名会优先于
AI/TikTok/Netflix 原分组。正则必须由原生 provider 加载。
家宽分组按节点名称筛选，不能验证 IP 类型；使用前确认成员和出口地区，手动固定合适节点。
若没有匹配节点，先修正节点命名或筛选表达式，勿启用覆盖；转换器可能把空组补成 `DIRECT`。
该分组是共享的，改变选择会影响所有引用它的服务；不同账号需要不同地区时，应分别选择节点。
验收时比较相同设备/账号在两个出口的结果，并检查连接日志、出口 IP 和地区。
仓库测试只能验证匹配与语法，无法证明真实出口属于家宽或能通过服务端检查。

## 开发下载与大流量

`Download.list` 已接入 `📦 下载节点`，位于广告过滤之后、GitHub/Google/Microsoft 等通用服务之前。
它与上游 ACL4SSR 的直连 `Download.list` 是不同文件，后者继续作为国内下载补充。

| 范围 | 处理方式 |
| --- | --- |
| GitHub | Release、Raw、源码压缩包、明确的 LFS/Packages 主机走下载组；网页、API、头像保留原策略。 |
| 容器 | Docker Hub 鉴权/注册表/镜像 CDN、GHCR、Quay、GCR、Kubernetes 注册表与 Artifact Registry 包/镜像域名。 |
| 模型 | Hugging Face 主站、LFS、Xet 和模型 CDN；独立推理主机保留原代理策略。 |
| 包管理器 | npm/Yarn、PyPI、Maven/Gradle、NuGet、Cargo、RubyGems、Go 模块；国内镜像维持直连。 |
| 工具 | Rust/Node、JetBrains 安装包、VS Code/Visual Studio 更新及扩展。 |

下载组默认跟随 `🚀 节点选择`，同时直接列出订阅节点，可单独固定大带宽、流量充足的普通节点，
不会改动共享的手动选择器。配置不能识别套餐额度或真实带宽；若主选择组当前使用家宽，
下载组默认也会跟随，需在下载组直接选择合适节点。视频、直播继续由各服务组负责；Steam 国内 CDN、JetBrains 国内 CDN 及前置白名单中的 `dl.google.com` 直连。

域名规则无法区分 URL 路径、文件大小和传输方向：例如 `huggingface.co`、`nodejs.org` 的网页，
包注册表的元数据和上传也会走下载组。GitHub 的初始 Release 页面仍走主策略，重定向后的文件主机走下载组。
未把 `amazonaws.com`、`cloudfront.net`、`blob.core.windows.net`、`storage.googleapis.com`
等共享云域名整体收录；未明确归属的下载跳转继续原策略，需要结合连接日志逐个补充。

域名依据包括 [GitHub 网络说明](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)、
[Docker 允许列表](https://docs.docker.com/desktop/enterprise/allow-list/)、
[Hugging Face Xet 迁移说明](https://huggingface.co/blog/migrating-the-hub-to-xet)和
[VS Code 网络说明](https://code.visualstudio.com/docs/setup/network)。更新列表时同时添加下载命中、
国内镜像直连、普通网页/API 与共享云服务不误分流的测试。

## 修改与验证

### DNS 与 Nikki

末尾的 `GEOIP,CN` 使用 `no-resolve`：只对已有目标 IP 做国内判断，不为了匹配该规则
额外解析未知域名。未分类、尚无真实 IP 的域名会进入漏网之鱼；这不等于禁止所有 DNS 查询。
`clash-base.yaml` 未定义 DNS/TUN，需要由客户端或 Nikki 混入提供；它本身不保证 DNS 防泄露。

Nikki 排查应查看**用于启动的最终配置**中的 `dns`，并核对 IPv4/IPv6 DNS 劫持和客户端访问控制，
不能仅查看订阅原文。浏览器安全 DNS、局域网设备自身的解析路径也需要分别验证。
DNS 测试网站显示的是递归解析器出口，其地区不一定等于节点地区；请结合 IP、服务商和预期 DNS 策略判断。
Nikki 的订阅更新不会自动重载服务，更新后需手动重载/重启，见
[Nikki 官方说明](https://github.com/nikkinikki-org/OpenWrt-nikki/wiki)。

以下专项测试读取集成测试生成的配置，用本地 DNS 记录器对比“去掉 no-resolve”与实际配置：

```sh
python3 tests/test_dns_routing.py --config /tmp/rules-test-results/ini/config.yaml \
  --mihomo /path/to/mihomo --geodata-dir /tmp/rules-test-results
```

对照应出现未知域名查询，实际配置应为零。测试验证规则匹配不额外触发解析；
不代替 Nikki 路由器、浏览器及真实 DNS 上游的端到端泄露测试。

### 常规回归

```sh
python3 scripts/sync_config.py
python3 scripts/sync_config.py --check
sh tests/test_hongguo_rules.sh
python3 tests/test_rules.py
git diff --check
```

离线测试验证语法、重复、重点域名、正常内容反例、规则顺序、分组可达性与循环引用，以及 INI/TOML 同步。
Python 脚本需要 Python 3.11+；不要直接编辑生成的 TOML。

实际集成测试需要 Linux Docker、Mihomo 可执行文件和 PyYAML：

```sh
python3 -m pip install -r tests/requirements.txt
docker pull tindy2013/subconverter@sha256:9fd004f00e90a7f67631f4d9a3f435c95b0fe58e7afdce8b8c6ca28c92826632
MIHOMO_BIN=/path/to/mihomo sh tests/run_integration.sh --output /tmp/rules-test-results
```

测试自动启动临时 Subconverter，把当前未发布文件通过本地 HTTP 提供给转换器，下载外部规则，
并比较两种配置的完整转换输出。随后校验 Mihomo 配置、真实下载四个 provider，核对缓存内容与源码一致，
再通过 SOCKS5 发起 TCP/UDP 探测，检查原生引擎日志中的策略命中。为避免请求真实服务，探测阶段
将仅直连组的出口替换成测试接收端，保留原有规则、顺序和策略组名称。

输出目录包含两份 `config.yaml`、隔离出口的 `runtime.yaml`、校验日志、运行日志和 `routes.json`。
这些带本地测试 URL 的 YAML 仅供检查，不能部署。集成测试不包含手机上的登录、播放或实际广告体验；
新增域名应结合连接记录，同时补充正常内容反例，不宣称完整覆盖所有服务端变化。

## 规则来源

重点服务域名参考 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community/tree/master/data)
和 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Clash)，
按服务用途筛选；红果分片正则由已有明确广告域名归纳，保留正常内容反例。
其他广告与分流源仍沿用 ACL4SSR / blackmatrix7，自定义规则统一指向本仓库。
