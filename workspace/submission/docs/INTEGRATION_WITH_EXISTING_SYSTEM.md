# 与 Makerverse / livestream-rs 的融合说明

## 1. 融合原则

不重写两个既有仓库，不把 AI 逻辑嵌入直播服务内部。采用旁路中间件：livestream-rs/Makerverse 负责直播、会话和媒体端点；独立 AI 服务负责帧抽样、事实、事件和证据索引；前端通过 Repository 与两个后端适配器展示。

```text
livestream-rs -> Makerverse LiveService/API -> media endpoint
                                          \
                                           -> AI source adapter -> events/evidence
frontend <-----------------------------------------------^      |
                                                             SQLite/REST
```

## 2. 已完成的源码审计

`workspace/source-snapshots/Makerverse/` 与 `livestream-rs/` 保存了干净快照和 commit 记录。静态审计记录了 .NET Aspire 服务边界、LiveService/LiveController、媒体端点 DTO、livestream-rs 的端口和 README 配置，以及 MinIO/Redis/数据库相关依赖。具体源码事实见 `PHASE0_AUDIT.md`、`ARCHITECTURE_BASELINE.md` 和 `Makerverse与livestream-rs项目重要信息整理.md`。

## 3. 已实现的低风险适配

- 前端 `createMakerverseLiveAdapter`：调用 `/lives/online` 与 `/lives/{id}/endpoint`；
- DTO 同时接受 PascalCase、lowerCamelCase、扁平和嵌套播放端点；
- AI `SourceResolver` 对 RTMP/RTSP/HTTP/HLS 做配置检查，不声称解码成功；
- Evidence resolver 保留 `fixture`、`provided_unverified`、`available`、`unavailable` 等状态；
- 所有真实地址、token、局域网信息使用环境变量，不进入提交包。

## 4. 真实联调所需资料

1. Makerverse API 基址、鉴权方式、CORS 和在线 Live 示例；
2. livestream-rs 启动参数、推流协议、播放 URL、MinIO/Redis 配置和时间轴规则；
3. .NET SDK、Cargo、FFmpeg 或等价部署环境；
4. 浏览器网络面板中 HLS/HTTP-FLV 请求、状态码和跨域响应；
5. AI source_id 与 live_id、playlist、segment 时间戳之间的映射；
6. 老师/机器人资料规定的摄像头和部署约束。

## 5. 失败与降级

连接失败、无在线 Live、未提供 endpoint、CORS 错误或媒体类型不支持时，前端显示可诊断原因；AI 任务保留失败/停止状态；事件证据显示待解析。禁止把“API 返回 200”扩大成“真实视频可播放”或“机器人已联调”。

## 6. 下一步验收记录模板

| 项目 | 证据 | 结果 |
|---|---|---|
| Makerverse `/lives/online` | 原始 JSON + 时间 | 待补 |
| endpoint DTO | 原始 JSON + 归一化结果 | 待补 |
| HLS/HTTP-FLV 请求 | 浏览器网络记录 | 待补 |
| AI 时间轴 | source_id/live_id 映射 | 待补 |
| 直播断流/重连 | 日志与任务状态 | 待补 |
| 机器人相机到 AI | 实机日志/照片 | 待补 |
