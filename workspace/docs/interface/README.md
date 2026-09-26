# Frontend / Backend / AI Interface v1

状态：TASK-0011 草案，供 frontend adapter 迁移使用。

AI 已冻结。本文档只描述现有 backend API 和已经冻结的 AI 事件语义，不新增 AI 算法、REST 路由、WebSocket 或真实媒体流。

## 数据流

```text
AI facts / scene reasoners
  -> UnifiedEvent + EvidenceRef
  -> backend REST /api/v1
  -> frontend src/api adapters
  -> React views
```

## 约定

- backend JSON 使用 snake_case；frontend adapter 保留原字段名，不在页面组件内重复转换。
- `source_id` 是输入来源标识，不等于人物身份。
- `timestamp`、`started_at`、`ended_at` 使用 timezone-aware ISO 8601 字符串。
- `continuity_segment` 发生 observation gap 或 quality boundary 后递增，不能跨段拼接事实。
- `review_status` 只能是 `pending`、`confirmed`、`rejected`。
- candidate/review 事件不能在 UI 中升级为医疗、物理或身份确定性结论。
- Real 请求失败时 adapter 返回明确错误，页面不能静默显示旧 Mock 数据。

## 文件对应

- `events.md`：UnifiedEvent、PrimitiveFact、EvidenceRef；
- `providers.md`：health/ready/provider status/source status；
- `registry.md`：objects/persons/registry match；
- `jobs.md`：analysis jobs、source inspection、evidence resolve；
- `../frontend/src/contracts/`：TypeScript 编译时契约；
- `../frontend/src/api/`：Mock/Real 请求适配层。
