# 计划要求—证据矩阵

最后核验：2026-09-22

状态含义：

- `PASS_LOCAL`：当前源码/本机服务/测试已直接验证；
- `MOCK_ONLY`：有确定性 fixture 或 CPU heuristic，但不能推导真实性能；
- `BLOCKED_EXTERNAL`：依赖老师资料、真实部署、工具链、数据或硬件；
- `SCAFFOLD`：结构和接口已经准备，正式内容待补。

## AI 与事件

| 计划要求 | 当前证据 | 状态 |
|---|---|---|
| 独立运行与 health/ready | `ai-engine` 启动、`GET /health`、`GET /ready` | PASS_LOCAL |
| 统一 schema 与 SQLite | `models.py`、`storage.py`、API tests | PASS_LOCAL |
| 视频输入抽象 | Mock/JSONL/OpenCV provider 与测试 | PASS_LOCAL |
| 真实网络媒体输入 | SourceResolver/媒体 adapter，仅配置边界 | BLOCKED_EXTERNAL |
| 检测/跟踪接口 | detector registry、MotionCPU、Fixture、CentroidTracker | PASS_LOCAL |
| 真实训练模型与性能 | 无授权数据/权重/评估脚本 | BLOCKED_EXTERNAL |
| PrimitiveFact 与关系 | `fact_pipeline.py`、`relations.py`、测试 | PASS_LOCAL |
| 养老/工作室插件 | manifest 自动发现、并行、启停、fixture 测试 | PASS_LOCAL |
| 事件状态机与停止 | analysis job、stop 语义和回归测试 | PASS_LOCAL |
| 证据时间窗 | EvidenceResolver 和 API/前端状态 | PASS_LOCAL / MOCK_ONLY |
| 真实回放定位 | 无 live_id/playlist/segment 时间轴 | BLOCKED_EXTERNAL |
| 注册对象/人员 | CRUD、CPU embedding、registry match | PASS_LOCAL / MOCK_ONLY |

## 前端

| 计划要求 | 当前证据 | 状态 |
|---|---|---|
| Dashboard/Monitor/Events/Detail | `App.tsx` 视图与 build | PASS_LOCAL |
| Plugins 真实开关 | Repository 调用 enable/disable | PASS_LOCAL |
| Objects/Persons/Settings | Registry 与 Settings view | PASS_LOCAL |
| Mock 模式 | Mock repository、离线 fixture | PASS_LOCAL / MOCK_ONLY |
| Real AI API | Real repository、任务轮询、HTTP smoke | PASS_LOCAL |
| Makerverse adapter | DTO 归一化、媒体 URL 分类 | PASS_LOCAL / SCAFFOLD |
| 浏览器视觉交互 | 无浏览器会话 | BLOCKED_EXTERNAL |
| 真实 HLS/HTTP-FLV 播放 | 无在线端点和网络 trace | BLOCKED_EXTERNAL |
| 响应式现场截图 | 无浏览器视觉验收 | BLOCKED_EXTERNAL |

## 文档与交付

| 计划要求 | 当前证据 | 状态 |
|---|---|---|
| AI/架构/插件/创新/实验/API/部署/局限 | `workspace/docs/*.md` | PASS_LOCAL |
| 比赛材料包 | `COMPETITION_MATERIAL_PACK.md`，真实字段待补 | SCAFFOLD |
| LaTeX 骨架 | `docs/latex/` 12 个文件，结构检查通过 | PASS_LOCAL / SCAFFOLD |
| FINAL_REPORT/MANIFEST/LICENSES | `workspace/submission/` | PASS_LOCAL |
| 一键清洁度/测试验收 | `VERIFY.ps1 -SkipFrontendBuild` 输出 `VERIFY_OK` | PASS_LOCAL |
| 老师最终主文档融合 | 根目录未发现老师文档 | BLOCKED_EXTERNAL |
| 机器人实机与安全验收 | 根目录未发现机器人资料 | BLOCKED_EXTERNAL |

## 结论

当前已达到“可运行软件原型 + 可审计材料包 + 干净阶段性提交包”的证据范围；尚未达到“真实比赛部署、真实模型指标、机器人实机和最终老师文档融合”的完成条件。后续只能在外部资料到位后升级对应状态，不能用本矩阵中的 `PASS_LOCAL` 替代真实验收。
