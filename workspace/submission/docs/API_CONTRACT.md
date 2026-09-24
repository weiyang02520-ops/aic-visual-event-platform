# AI REST API 契约（当前实现）

日期：2026-09-22

基础地址：`http://127.0.0.1:8010`

## 健康与来源

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/health` | 服务存活 |
| GET | `/ready` | 数据库、插件管理器、检测器和跟踪器就绪探针 |
| GET | `/api/v1/sources/inspect?source=...` | 来源路由/可用性检查 |
| GET | `/api/v1/sources/frames?source=...` | Mock/JSONL/OpenCV 本地帧预览 |
| GET | `/api/v1/vision/preview?source=...&detector=fixture\|motion` | 检测、跟踪和观察事实预览 |
| GET | `/api/v1/evidence/resolve?...` | 证据状态解析 |
| GET | `/api/v1/providers/detectors?source=...` | 检测 provider 可用性、选择状态和 fallback 原因 |

`/ready` 返回 `ready`、`status`、`database`、`plugin_manager`、`detector`、`tracker` 和 `plugins` 字段。`ready=true` 只表示本地进程、SQLite 目录、插件管理器和当前选中的 detector/tracker 已就绪，不表示真实直播、模型指标或机器人已验收。

## 插件与分析任务

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/v1/plugins` | 列出插件及状态 |
| POST | `/api/v1/plugins/{id}/enable` | 启用插件 |
| POST | `/api/v1/plugins/{id}/disable` | 停用插件 |
| POST | `/api/v1/analysis/jobs` | 创建分析任务，body 至少包含 `source` |
| GET | `/api/v1/analysis/jobs` | 任务列表 |
| GET | `/api/v1/analysis/jobs/{id}` | 任务详情 |
| POST | `/api/v1/analysis/jobs/{id}/stop` | 请求停止任务 |

## 事件和登记

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/v1/events` | 事件列表，可按 plugin/review 状态过滤 |
| GET | `/api/v1/events/{id}` | 事件详情 |
| POST | `/api/v1/events/{id}/review` | 人工确认或驳回 |
| GET/POST/DELETE | `/api/v1/objects` | 自定义物品登记 |
| GET/POST/DELETE | `/api/v1/persons` | 人员登记 |
| POST | `/api/v1/registry/match` | 用登记向量或灰度矩阵做 CPU baseline 相似度匹配 |

## 统一事件最小字段

`event_id`、`schema_version`、`plugin_id`、`event_type`、`title`、`description`、`source_id`、`started_at`、`ended_at`、`confidence`、`severity`、`review_status`、`subject`、`object`、`location`、`facts`、`evidence`、`metadata`。

## 交互边界

- `202 Accepted` 的分析任务可能先返回 `queued/running`，客户端应按 `job_id` 轮询；
- `POST /api/v1/analysis/jobs/{id}/stop` 设置任务取消事件；后台任务在帧提取/插件阶段边界检查后保持 `stopped`，不会把已停止任务覆盖为 `completed`；
- `review_status` 是人工复核状态，不等同于模型真值；
- `confidence` 是当前 provider/规则组合的事件置信度，不是比赛准确率；
- `evidence.status` 必须按 resolver 返回值展示，不能默认当作可回放；
- 真实 Makerverse 鉴权、livestream-rs 地址和机器人任务接口不在当前 AI API 中硬编码。
