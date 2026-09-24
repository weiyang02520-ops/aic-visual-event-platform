# AI REST API 参考

默认地址：`http://127.0.0.1:8010`。实际部署地址、鉴权和 CORS 必须通过环境变量配置。

## 基础

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/health` | 进程存活检查 |
| GET | `/ready` | 数据库、插件管理器、detector 和 tracker 就绪状态 |

示例：

```json
{
  "ready": true,
  "status": "ready",
  "database": "ok",
  "plugin_manager": "ok",
  "detector": "ok",
  "tracker": "ok",
  "plugins": 2
}
```
| GET | `/api/v1/plugins` | 列出插件 |
| POST | `/api/v1/plugins/{plugin_id}/toggle` | 全局启用/停用插件 |
| GET | `/api/v1/events` | 事件历史 |
| POST | `/api/v1/events/{event_id}/review` | 确认或驳回事件 |

## 分析任务

```http
POST /api/v1/analysis/jobs
Content-Type: application/json

{"source":"mock://elderly-medication"}
```

返回 `job_id`、`status`、`progress` 和 `event_ids`。通过 `GET /api/v1/analysis/jobs/{job_id}` 查询；`POST /api/v1/analysis/jobs/{job_id}/stop` 请求停止。停止成功后的终态为 `stopped`，不得当作 `completed`。

## 来源与证据

- `GET /api/v1/sources/inspect?source=...`：检查来源类型和能力；
- `GET /api/v1/sources/frames?source=...`：在支持的 provider 上读取有限帧；
- `GET /api/v1/evidence/resolve?source_id=...&started_at=...&ended_at=...`：返回 resolver 状态、时间窗和可选 URI。

证据状态包括 `fixture`、`provided_unverified`、`available` 和 `unavailable`。不存在可验证 URI 时，不应构造播放链接。

## 注册对象与人员

- `GET /api/v1/objects`、`POST /api/v1/objects`；
- `GET /api/v1/persons`、`POST /api/v1/persons`；
- `POST /api/v1/registry/match`：提交 embedding 或灰度矩阵，返回排序后的相似度和 `accepted`。

当前 embedding 匹配是 CPU heuristic，不是身份认证。

## 错误处理

无效 JSON、未知插件、未知任务、停止后的重复请求和不支持的来源应返回受控 HTTP 错误或明确状态。调用方不得把 HTTP 200 的 fixture 结果解释成真实媒体或实机结果。
