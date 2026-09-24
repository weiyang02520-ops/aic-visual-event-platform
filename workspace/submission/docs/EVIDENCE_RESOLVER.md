# Evidence Resolver

日期：2026-09-22

## API

`GET /api/v1/evidence/resolve` 接收 `source_id`、`started_at`、`ended_at`，可选 `uri`，返回：

- `fixture`：Mock/fixture 的确定性引用，只用于演示和测试；
- `provided_unverified`：调用者给了 HTTP/HLS/RTSP 等 URI，但没有验证保留策略、授权和时间对齐；
- `unavailable`：没有配置可证明的归档或分片解析器；
- `unsupported`：URI scheme 不在当前 resolver 能力内。

## 设计边界

resolver 不猜测 MinIO 对象键、HLS 分片名称、签名 URL 或直播时间偏移。后续接入 livestream-rs/Makerverse 时，需要根据真实部署补充 source_id 到 live_id、playlist、segment 时间轴和鉴权的映射；在此之前，前端必须显示“待解析/未验证”，不能显示成“可回放”。

## 验证

该阶段 resolver 专项测试为 16 passed；当前 AI 全套回归已扩展到 28 passed，覆盖 fixture、unavailable、provided_unverified、非法时间窗和 REST 响应；前端事件中心已显示证据状态。
