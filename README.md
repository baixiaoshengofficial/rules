# rules

用于 Subconverter 生成 Clash/Mihomo 订阅的自用规则。

## 红果短剧广告

`HongGuoAD.list` 覆盖红果的广告接口、字节广告 SDK、广告素材分片和
HTTPDNS 绕过链路。`baixiaosheng.ini` 和 `baixiaosheng.toml` 都将该规则集固定到
`REJECT`，避免策略组状态被误切换为 `DIRECT`。

在 Nikki 更新订阅后，建议重启红果并清理已缓存的广告。规则命中时，
Nikki/Mihomo 连接记录中的对应请求应显示为 `红果广告 / REJECT`。

该规则不封禁与正常封面、视频、登录混用的整个字节大域，以降低透明网关下的误杀。
