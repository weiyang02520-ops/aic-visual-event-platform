# AIC 机器人智能识别项目（当前可提交暂存包）

这是从开发工作区筛选出的提交暂存包，不包含 Python 缓存、SQLite 运行数据库、Node 依赖、Vite 构建产物、模型权重或访问凭据。

## 目录

- `ai-engine/`：独立 Python AI 服务，含统一事件、来源/帧管线、CPU 基线检测、时序事件推理、模型 provider 契约、关系事实、场景插件、证据 resolver、REST API 和测试；
- `frontend/`：React + Vite 控制台，含 Mock/Real API 切换、总览、监控、事件复核、插件、对象/人员登记、媒体边界适配器；
- `docs/`：架构、API、插件、媒体、模型、证据链和提交检查材料；其中 `AI_ALGORITHM_FINAL_REPORT.md` 是当前 AI 最终报告，`FRONTEND_AI_INTEGRATION_CONTRACT.md` 是 frontend handoff 契约。
- `FINAL_REPORT.md`：当前阶段报告，列出已完成项和未验证项；
- `MANIFEST.md`：暂存包内容、排除项与最终打包规则。
- `LICENSES.md`：第三方依赖清单和最终许可证复核提示。
- `VERIFY.ps1`：运行提交包清洁度、AI 测试和可选前端构建检查。

## 当前验证

- AI：`414 passed`；包含注册对象/人员 CPU baseline embedding、布尔和数字字符串特征拒绝、灰度强度范围验证、空/全零登记向量 API 错误映射、无 ID 药品标签级候选去重、药柜/药架储存目标及药品说明书/处方文档排除、显式非人物主体/无效身份 ID/无效置信度拒绝服药推理、低分早期手部事实不掩盖后续有效动作、显式关键点动作规则及单帧丢失去抖、布尔关键点/框/阈值拒绝、极大关键点数值安全忽略、浮点帧差像素保留和抽样框原帧坐标映射、并发 job 状态隔离、运行中帧提取取消、灰度范围及 bbox/区域边界溢出校验、时序事件推理器及插件集成、冒号 ID 关系冷却键碰撞防护、跨人物关联保护、共享人物标签、全局匹配分配、帧时间顺序/几何配置校验、直接实体/区域输入校验、数值阈值类型检查与重复 ID 隔离（包含超大整数转换溢出防护）、FixtureDetector 浮点框与置信度验证、非法分数/对象行 API fail-closed 与多区域事件保留验证、人物标签变体跟踪连续性、抽帧参数严格整数校验、OpenCV 异常 FPS/PTS fallback、坏帧/重复框防护、漏检间隔清理关系/运动/区域 cooldown 且不推断运动/放下/区域离开、JSONL 恢复坏行的 observation_gap、连续段状态隔离和跨 gap 推理拒绝，非有限距离不生成关系事件、可选 `AI_ZONES_JSON` 区域配置、按区域隔离的待归还状态与转移闭环、相同时间戳不依输入顺序推断归还或缺失、可验证的任务停止语义、事件与 completed 状态原子提交、完成任务幂等重跑和 ONNX safety fallback；
- 前端：TypeScript + Vite production build 通过；
- 前端事件中心支持关键词/状态筛选、详情抽屉、证据时间窗查看和人工确认/驳回；
- Real API HTTP smoke：health、plugins、events、objects、persons、evidence、detector provider 均通过；
- 当前仍未宣称真实 Makerverse/livestream-rs 在线直播、真实模型准确率或机器人实机结果。
- 养老完整动作链和工作室超时缺失仍依赖上游提供 `hand_to_face` / `scene_observed` 事实；测试用例使用 Mock/fixture，不代表真实视频识别性能。
- 包状态：`STAGED_PROTOTYPE`，老师主文档和机器人资料到位后必须重新融合、验收和生成最终包。
- `docs/COMPETITION_MATERIAL_PACK.md` 和 `docs/latex/` 提供正式材料语气与 LaTeX 结构骨架，未代填老师模板、赛道、硬件和真实指标。

## 运行入口

AI 服务和前端的安装、启动、环境变量与限制分别见各自 README。真实部署前必须补齐老师主文档、机器人协议/硬件资料、媒体服务地址、鉴权/CORS 和模型权重/类别契约。

## 证据边界

Mock、fixture、CPU heuristic 和本地 AVI 读取只证明软件链路可以运行，不等于比赛现场性能或机器人联调通过。提交正式材料时，应将真实部署日志、样例、指标和硬件照片作为独立证据追加。
