# Task Log

## 2026-09-22

- 读取 `Codex_Master_Execution_Plan_V5_FINAL.md`，确认其是长期任务规格参考。
- 创建 `workspace/ai-engine/`、`workspace/frontend/`、`workspace/docs/`、`workspace/submission/`。
- 创建 `agent-state/` 及项目状态文件。
- 未修改 Makerverse、livestream-rs 或任何业务代码。
- 完成计划书一致性体检，记录版本叠加、目录冲突、赛道未定、算法目标未定义、范围过宽、证据链和机器人资料阻塞。
- 读取用户提供的 ChatGPT 共享对话，确认计划书是最终交给 Codex 的长期执行规格；计划体检记录转为内部执行注意事项。
- 创建 `Codex_启动提示词.md`，用于新 Codex 会话直接接管项目。
- 开始 Phase 0；核验资料目录、工具链和两个仓库 checkout。
- 发现 FFmpeg、Cargo 不在 PATH；Python、Node/npm、.NET、Git 可用。
- 将 Makerverse 与 livestream-rs 克隆到 `workspace/source-snapshots/`，记录 clean checkout 和 commit。
- 生成 `workspace/docs/PHASE0_AUDIT.md`、`ARCHITECTURE_BASELINE.md`、`INTEGRATION_NOTES.md`，完成 Phase 0 静态审计。
- 建立 `workspace/ai-engine/` Python 服务：统一事件 schema、SQLite、插件 manifest 扫描、养老/工作室插件、Mock analysis jobs 和 REST API。
- AI 单元/API 测试通过：4 passed；真实 Uvicorn HTTP smoke 通过，产生 1 条 `suspected_medication` 待复核事件。
- 记录 FastAPI 204 response body 兼容问题并修复。
- 建立 `SourceResolver` 和 `/api/v1/sources/inspect`，区分 Mock、本地文件、流媒体配置和不可用来源；不把“已配置”当成“已连接”。
- AI 测试扩展为 5 passed，覆盖 Windows 路径和 livestream-rs 来源路由边界。
- 建立 `workspace/frontend/` React + Vite 控制台：Mock/Real API 切换、总览、监控、事件复核、插件、对象/人员登记和设置页。
- 安装前端依赖并完成 `npm run build`；Vite dev server `127.0.0.1:4173` 返回 200 HTML 根入口。
- Phase 2：新增 `Frame`、`CancellationToken`、Mock/JSONL 本地 provider 和 `FramePipeline`；新增 `/api/v1/sources/frames` 帧预览 API。
- Phase 2 测试通过：8 passed；HTTP smoke 返回 3 个带 source_id、index、timestamp、provider 的 Mock 帧。
- Phase 3：新增 Detector/Tracker protocol、CPU MotionDetector、FixtureDetector、CentroidTracker 和统一 observations；全套测试 11 passed。
- Phase 4：新增 person-object distance、near、pickup/putdown candidate、motion、zone entered/left 和 cooldown；增强养老/工作室插件状态；全套测试 15 passed。
- 新增保守 `EvidenceResolver` 和 `/api/v1/evidence/resolve`；前端事件中心显示 fixture、已提供未验证、可回放或待解析状态；AI 测试扩展为 16 passed。
- 再次完成 AI + 前端全量回归：AI 16 passed，前端 `npm run build` 通过。
- 增加前端 `npm run smoke:real`，验证 Real API 的 health、plugins、events、objects、persons 和 evidence 路径；返回 health `ok`、2 plugins。
- 生成 `API_CONTRACT.md` 和 `SUBMISSION_READINESS_CHECKLIST.md`，为最终老师文档融合和清洁提交保留可核对入口。
- 扩展 `OpenCVFrameProvider`，支持常见本地视频容器的可选读取和抽帧；用 16x12、2 帧 AVI fixture 真实读取验证；AI 全套测试扩展为 18 passed。
- 新增 `FrameFactExtractor` 并接入 `AnalysisService`，本地 JSONL/OpenCV 输入可进入检测、跟踪、关系和 PrimitiveFact 链；AI 测试扩展为 20 passed。
- 新增模型 provider registry：`motion_cpu`、`fixture`、可选 `onnx`，暴露 `/api/v1/providers/detectors` 和明确 fallback 原因；AI 测试扩展为 22 passed。
- Real API smoke 扩展检测 provider 状态，返回 selectedDetector `motion_cpu`。
- 新增前端媒体边界适配器：兼容 Makerverse `LivestreamEndpointDto` 的 PascalCase/嵌套 `PlaybackEndpoints`，统一转换为 `LiveSession`；RTMP/RTSP/HLS/HTTP-FLV/Mock 地址会显示不同的浏览器能力和证据提示，不硬编码真实 URL。
- 新增 `workspace/docs/MEDIA_PLAYBACK_ADAPTER.md`，记录真实联调清单和当前未连接结论。
- Frontend latest: `npm run build` passed after media adapter normalization; browser-level playback and Makerverse runtime remain unverified.
- 新增 `embeddings.py`：纯 CPU 灰度网格+强度直方图 baseline、向量归一化和余弦相似度；对象/人员登记可保存 embedding，新增 `/api/v1/registry/match`，保留阈值与 `accepted`/人工复核边界。
- AI 回归由 22 passed 扩展为 27 passed，覆盖坏向量、维度跳过、排序/阈值、REST 登记匹配和带 embedding 的本地 fixture→PrimitiveFact registry_matches 链；新增 `workspace/docs/REGISTRY_EMBEDDINGS.md`。
- 前端事件中心把原占位搜索/筛选改为真实关键词过滤（标题、描述、插件、来源、位置、主体/对象）和 pending/confirmed/rejected 状态过滤；生产构建继续通过。
- Real 监控页接入 `createMakerverseLiveAdapter`：通过 `VITE_MAKERVERSE_API_URL` 和可选 token 拉取 `/lives/online`、`/{id}/endpoint`，复用 playback 分类；未配置/失败/无在线直播时保留明确提示，不渲染虚构视频。
- 事件中心新增可操作详情抽屉：显示统一事件描述、事实、时间窗、证据 resolver 状态和人工确认/驳回；表格“打开”按钮不再是空操作。
- 修复 analysis job stop 竞态：`AnalysisService` 使用任务级取消事件，在帧提取和插件评估边界检查；停止任务不会被后台回写为 `completed`，新增回归测试。
- 前端 Repository 新增 `getAnalysis`；Real 模式 `runDemo` 按 `job_id` 轮询 `queued/running` 到 `completed/failed/stopped` 后再刷新事件，覆盖 API `202 Accepted` 语义。
- 收紧 ONNX provider 可用性：即使权重文件和 runtime 存在，没有 verified input/output adapter 也只能报告 unavailable 并 fallback 到 `motion_cpu`；新增回归测试防止误选。
- 修正 provider 状态列表在未传 `source` 时的选择标记：请求不可用 provider 也会明确选中 `motion_cpu`，避免前端出现没有 selected provider 的状态。
- 将 Makerverse 与 livestream-rs 克隆到 `workspace/source-snapshots/`，记录 clean checkout 和 commit。
- 生成 `workspace/docs/PHASE0_AUDIT.md`、`ARCHITECTURE_BASELINE.md`、`INTEGRATION_NOTES.md`，完成 Phase 0 静态审计。
## 2026-09-22 — 阶段性提交包报告与证据总览

- 新增 `workspace/docs/当前实现与证据总览.md`，集中说明源码静态核验、Mock、Local Service、真实部署和机器人实机证据边界。
- 在 `workspace/submission/` 新增阶段性 `FINAL_REPORT.md` 与 `MANIFEST.md`；继续明确该目录是 `STAGED_PROTOTYPE`，不是最终比赛提交包。
- AI 回归测试重新核验为 `29 passed`；前端 `npm run build` 通过。
- 当前外部阻塞仍为老师主文档、机器人资料以及 .NET SDK/Cargo/FFmpeg；未据此编造赛道、协议、指标或实机结果。

## 2026-09-22 — 文档材料包与 LaTeX 骨架

- 按计划书 P12/P13 交付项新增 AI 算法、插件架构、前端系统、既有系统融合、创新点、实验计划、API、部署演示、局限和比赛材料包文档。
- 新增 `THIRD_PARTY_NOTES.md`、阶段性 `LICENSES.md` 和 `workspace/docs/latex/` 中文 LaTeX 骨架；未臆造老师模板、学校 Logo、赛道标题或真实指标。
- 所有上述材料已同步到 `workspace/submission/docs/`，提交包继续排除 agent-state、缓存、运行数据库、依赖目录、构建产物和个人绝对路径。

## 2026-09-22 — 前端轻量路由

- 前端新增 hash 路由（`#dashboard`、`#monitor`、`#events` 等），监听浏览器 hash 变化并保留前进/后退语义；不引入额外运行时依赖。
- `npm run build` 通过，更新后的 `App.tsx` 已同步到 submission 前端。

## 2026-09-22 — 证据回放入口边界

- 事件详情抽屉新增条件式“打开证据回放”链接：只有 resolver 状态为 `available` 且 URI 存在时才可打开；fixture/未验证/待解析状态显示边界提示。
- 前端 production build 通过，`App.tsx`、`styles.css` 和对应设计文档已同步到 submission。

## 2026-09-22 — 工作区入口

- 新增 `workspace/README.md`，给后续会话和用户提供从索引、状态、AI、前端、文档到 submission 的最短入口。

## 2026-09-22 — AI 可读日志

- AI 服务新增标准 logging：插件加载/启停/异常和分析任务创建/开始/停止/完成/失败均有结构化字段；明确不记录原始图像、embedding 内容或凭据。
- 源码和提交包 AI README 已同步说明日志边界；源代码与提交包测试均为 `29 passed`。

## 2026-09-22 — readiness probe

- `/ready` 从路径/数量返回升级为部署探针：明确 `ready`、数据库、插件管理器、detector、tracker 和插件数量；真实直播/模型/机器人仍不由该探针假定。
- 源码和 submission AI 回归均为 `29 passed`；Uvicorn `/ready` 与前端 Real smoke 实测通过。

## 2026-09-22 — submission 一键验收

- 新增 `workspace/submission/VERIFY.ps1` 与 `VERIFY.md`：检查必需文件、缓存/数据库/依赖/绝对路径/敏感字面量，运行 AI 测试，并在依赖存在时构建前端。
- 当前执行 `.\VERIFY.ps1 -SkipFrontendBuild` 通过，输出 `VERIFY_OK`，AI `29 passed`；脚本清理了测试 runtime，submission 复扫 `bad_count=0`。

## 2026-09-22 — 计划要求证据矩阵

- 新增 `REQUIREMENT_EVIDENCE_MATRIX.md`，逐项标记 `PASS_LOCAL`、`MOCK_ONLY`、`BLOCKED_EXTERNAL` 或 `SCAFFOLD`，避免把本地测试范围扩大为真实比赛完成。

## 2026-09-23 — AI algorithm audit and temporal reasoning

- 读取项目交付索引、agent-state 当前计划/状态、AI 算法设计、实验计划、服务源码、时序 reasoner 和对应测试；确认新 `algorithm_reasoner.py` 之前未被场景插件调用。
- 将 `MedicationSequenceReasoner` 接入养老插件；完整候选要求同一人物/对象、有效时序和阈值，泛化“盒子”与不同 ID 不能触发完整疑似事件；增加不完整拿取线索。
- 将 `WorkshopStateReasoner` 接入工作室插件；超时缺失要求 `scene_observed`，区域 return 要求回到同一分区，`putdown_candidate` 不单独视为归还；事件保留原始事实。
- 加强 MotionDetector 来源/任务状态隔离和无效矩阵校验；修正相同 bbox detections 的 track 归一化覆盖；embedding 输入拒绝 ragged/非有限矩阵。
- 让 `FrameFactExtractor` 支持显式 zones，并以三帧 JSONL fixture 验证同一对象离开/返回原区域到 workshop event 的完整本地链路。
- 更新 AI 算法、provider、插件、temporal、embedding 文档和证据边界；当前上游仍没有真实 `hand_to_face` / `scene_observed` 输出，`AnalysisService` 默认未传 zone 列表。
- 定向测试：reasoner/plugin 23 passed；provider/embedding 21 passed；source-to-fact 25 passed。最新 AI 全量回归：66 passed，218 条 Python 3.14 FastAPI/Starlette deprecation warnings。
- 将 22 个 AI 源码、测试与算法文档文件同步到 `workspace/submission/`；运行 `VERIFY.ps1 -SkipFrontendBuild` 得到 `VERIFY_OK` / `66 passed`，再扫描确认 forbidden artifacts `0`、sensitive literal hits `0`、104 files；逐文件 SHA-256 比对 `hash_mismatches=0`。

## 2026-09-23 — centroid assignment and timestamp safety

- 用两个合成输入复现 CentroidTracker 贪心关联缺陷：总距离 18 而全局最优为 10；另一个受门限约束的场景中贪心只匹配一个 ID，但存在两匹配解。
- 用 Hungarian assignment 替代逐边贪心，先最大化门控后的匹配数，再最小化总距离；1,200 个小型矩形成本矩阵与 brute-force 枚举的最优成本一致。
- RelationEngine 将时间规范为 UTC 并拒绝倒退时间；JSONL 中的倒序帧触发失败，不继续写关系状态。
- 定向回归：providers `14 passed`；relations + fact pipeline `7 passed`。完整 AI 源码回归 `71 passed`，218 条 Python 3.14 FastAPI/Starlette deprecation warnings。
- 将 12 个跟踪/时间安全源码、测试和文档文件同步到 `workspace/submission/`；`VERIFY.ps1 -SkipFrontendBuild` 使用项目内 `runtime/.pytest-temp` 返回 `VERIFY_OK` / `71 passed`，结束后 runtime 已清理；污染扫描为 0 项，12 文件 SHA-256 全部一致。

## 2026-09-23 — shared person-label semantics

- 加入 `entity_labels.py`，关系层和时序 reasoner 共用人物标签分类，统一识别“家属”“工作人员”“老人”及大小写不敏感的英文别名。
- 先加失败回归确认关系层未识别 `家属` / `Person`；修复后关系、reasoner 和 JSONL job targeted tests 返回 `30 passed`。JSONL 养老 fixture 改用“家属”后仍只产生不完整待复核线索。
- 当前 AI 全量测试 `73 passed`，218 条第三方弃用警告。
- 同步 10 个 AI 源码/测试/算法文档文件到 submission；项目内 basetemp 下运行 verifier 返回 `VERIFY_OK` / `73 passed`，runtime 清理后扫描无禁用产物和敏感内容，10 个文件 SHA-256 一致。
- 用户重申只允许变动 AIC 项目根目录内文件。只读检查发现早先 pytest 临时目录在系统 TEMP；未对其执行删除或改写，并把续跑自动化更新为只在项目内创建文件、使用项目内绝对 basetemp。

## 2026-09-23 — explicit-keypoint hand-to-face action rule

- 增加 `KeypointActionExtractor`，只消费显式 pose keypoints，不从图像像素推断姿态；要求 wrist 靠近鼻点、同一药品框和满足置信度门限，并按人物/药品 episode 去重。
- `FixtureDetector` 保留 keypoints metadata；`FrameFactExtractor` 在每帧关系事实生成后追加动作事实；JSONL `AnalysisService` 测试验证两帧输入形成 `suspected_medication` 并保留动作证据。
- 增加安全语义断言，确认该事件仍是 `pending` / `needs_review=true` / `medical_diagnosis=false`。
- 定向 action/core/fact-pipeline 测试 `13 passed`；AI 全量测试 `77 passed`。
- 将 15 个 AI 源码、测试和算法文档文件同步到提交暂存包；`VERIFY.ps1 -SkipFrontendBuild` 使用项目内 basetemp 返回 `VERIFY_OK` / `77 passed`，清理后扫描无污染，15 个唯一同步文件 SHA-256 全部一致。
- 证据边界：关键点是明确 fixture/上游输入，没有姿态模型、真实视频准确率或实机验证。
- 新增跨人物防误关联测试，并在 AnalysisService 端到端用例中断言生成事件继续保持待复核且不构成医学诊断；源码与提交副本全量回归更新为 `78 passed`。

## 2026-09-23 — keypoint dropout debounce

- 增加回归复现 keypoint 在一帧中断后恢复会重复产生 `hand_to_face` action edge 的问题。
- `KeypointActionExtractor` 现容忍一个采样帧缺失；缺失更久后重新武装；`FrameFactExtractor` 将帧索引传入 extractor 以供去抖。
- AI 源码全量测试 `79 passed`，218 条第三方弃用警告；提交副本同步和验收待完成。
- 后续补齐一帧漏点去抖回归，关键点测试 `5 passed`；submission 已同步并 `VERIFY_OK` / `79 passed`，7 个文件哈希一致。

## 2026-09-23 — relation geometry input validation

- 为 `Entity` bbox/confidence、`Zone` geometry 和 `RelationEngine` near/motion/cooldown 参数添加 finite/range validation，避免无效区域静默地产生空状态。
- 定向 relation/fact-pipeline 测试 `23 passed`；AI 源码全量测试更新为 `93 passed`。
- 同步 relation validation、对应测试与算法文档到 `workspace/submission/`；项目内 pytest basetemp 下 verifier 返回 `VERIFY_OK` / `93 passed`，清理后扫描 0 污染/敏感字面量，7 个同步文件 SHA-256 一致。

## 2026-09-23 — one-frame dropout end-to-end verification

- 将关键点 AnalysisService fixture 扩展为：动作已触发、下一采样帧漏点、随后动作仍在；事件存储里只保留一条 `hand_to_face` 事实。
- 针对用例 `1 passed`，AI 全量回归 `93 passed`；同步更新的 `test_core.py` 在提交副本 verifier 中再次通过。
- 该结果仍为显式 keypoint JSONL fixture，不代表真实摄像头 pose tracking。

## 2026-09-23 — zone configuration service path

- Added a strict parser for optional AI_ZONES_JSON rectangles and routed parsed zones through app creation into AnalysisService / FrameFactExtractor; unset config leaves the service zone list empty.
- Added parser boundary tests and an API-level JSONL exit/return regression. Targeted tests returned 8 passed, 3 deselected; source full suite returned 101 passed.
- Updated algorithm/deployment docs and the curated submission mirror. Made VERIFY.ps1 pin pytest temporary files beneath the staged AI runtime and clean them afterward.
- Staged verifier returned VERIFY_OK / 101 passed; post-scan found no forbidden artifacts or sensitive literals, and 13 synchronized files matched SHA-256.
- Evidence boundary: rectangles and detector observations are synthetic fixtures; no actual camera zone calibration or real video metrics are available.

## 2026-09-23 — per-zone workshop pending state

- Audited zone transition handling and reproduced a cross-zone overwrite: a later removal in zone B replaced the pending removal in zone A, so a return to A was not recognized.
- Added the red/green regression and changed pending removal storage to tracked-object plus zone scope. A return closes only the matching zone; other zone state remains intact.
- Targeted reasoner/plugin/fact-pipeline tests returned 27 passed; full source suite returned 102 passed. Staged verifier returned VERIFY_OK / 102 passed.
- Updated the temporal reasoning, scene-plugin, algorithm, implementation-summary, and staged report docs. Post-scan found 0 forbidden artifacts / 0 sensitive literals; 15 synchronized AI source/doc hashes matched.
- Fixture boundary: this verifies event-state logic over synthetic facts, not calibrated camera regions or real tracking.

## 2026-09-23 — scope timeout observations to removal region

- Reproduced a false object_missing event when an object left shelf A and a later scene_observed fact covered bench B.
- Added region matching for timeout evidence when both facts are scoped. Unscoped legacy observations keep the prior global-coverage behavior.
- Targeted tests returned 28 passed; source full suite returned 103 passed. Curated submission verifier returned VERIFY_OK / 103 passed.
- Updated AI temporal/deployment docs and the staged mirror. Post-scan found 0 forbidden artifacts / 0 sensitive literals; 15 synchronized source/doc hashes matched.
- The regression uses synthetic facts. There is no current scene_observed source or real camera-coverage evidence.

## 2026-09-23 — scope explicit missing evidence by zone

- Reproduced a mismatch where object_missing at shelf A consumed the latest removal from bench B for the same object.
- Scoped explicit missing facts now select only same-zone pending removal state. Unscoped missing facts remain global, and explicit object_returned behavior is unchanged.
- Targeted reasoner/plugin/fact-pipeline tests returned 29 passed; source full suite and staged verifier returned 104 passed.
- Updated AI algorithm docs and the staged mirror; post-scan found 0 forbidden artifacts / 0 sensitive literals and 15 synchronized hashes matched.
- Evidence remains fixture-only; actual zone calibration and observation providers are absent.

## 2026-09-23 — direct Zone contract and duplicate-ID isolation

- Audited the programmatic Zone path and reproduced permissive direct construction: blank IDs, blank labels, booleans/numeric strings and duplicate IDs passed or collided even though AI_ZONES_JSON rejects them.
- Added strict, normalized Zone validation, unique-ID checks before RelationEngine mutates time state, and blank-ID fallback to location matching in WorkshopStateReasoner.
- Targeted relation/fact-pipeline/config/reasoner/API tests returned 70 passed; source full suite and staged verifier returned 119 passed.
- Updated AI algorithm docs and synchronized 17 source/test/doc files; post-scan found no forbidden artifacts or sensitive literals.
- Evidence boundary: validation protects deterministic logic; no real camera calibration or physical region accuracy is claimed.

## 2026-09-23 — validate direct Entity inputs and duplicate identities

- Reproduced direct Entity failures: empty/non-string identity and labels passed, numeric strings/bools could reach bbox arithmetic, and duplicate IDs shared RelationEngine state.
- Entity now normalizes valid ID/label/bbox/confidence and rejects invalid values; RelationEngine rejects duplicate entity IDs before timestamp mutation.
- Targeted relations/fact-pipeline/reasoner/config tests returned 83 passed; source full suite and staged verifier returned 136 passed.
- Updated AI algorithm docs and synchronized relation code/tests. Post-scan found 0 forbidden artifacts / 0 sensitive literals and 17 synchronized hashes matched.
- Evidence remains CPU/fixture-level; no real detector or tracking accuracy is implied.

## 2026-09-23 — preserve detector fixture precision

- Reproduced that FixtureDetector converted bbox coordinates with int(), moving a 50.8 px gap to the 50 px near threshold, and clamped invalid scores including NaN.
- Detection now validates labels, numeric boxes, confidence, and metadata; FixtureDetector preserves fractional boxes and raises with a row index for invalid values rather than clamping.
- Targeted provider/fact-pipeline tests returned 26 passed; full source suite and staged verifier returned 145 passed.
- Updated AI algorithm/provider docs and staged sources/tests; post-scan found 0 forbidden artifacts / 0 sensitive literals and 20 synchronized hashes matched.
- Evidence boundary: synthetic JSONL precision test only; no real detector performance is claimed.

## 2026-09-23 — align tracker labels with shared person semantics

- Reproduced ID fragmentation when a stable person moved from the label Person to person or 工作人员; relation classification already treated those labels as people, but the tracker compared raw strings.
- CentroidTracker now shares person alias classification and casefolds full non-person labels. Person/object categories remain gated separately.
- Targeted provider/fact-pipeline/core tests returned 36 passed; source full suite and staged verifier returned 148 passed.
- Updated AI algorithm/tracker documentation; 21 synchronized source/doc hashes matched and staged contamination scan was clean.
- Evidence is limited to synthetic detections and deterministic track IDs, not real identity accuracy.

## 2026-09-23 — fixture subpixel and confidence integrity

- Reproduced that bbox x=50.8 was truncated to 50, turning a distance above the near threshold into a near/pickup candidate; also reproduced NaN confidence clamping to 1.0.
- Fixture Detection now preserves finite fractional coordinates and rejects malformed labels, boxes, and scores. The adapter reports the object index; an API regression confirms the job fails without saving events.
- Targeted provider/fact-pipeline tests returned 26 passed and the targeted API test returned 1 passed. Source suite and submission verifier returned 149 passed.
- Updated AI provider/algorithm docs and staged package. Post-scan found 0 forbidden artifacts / 0 sensitive literals; 21 synchronized source/doc hashes matched.
- Evidence is synthetic fixture-only; no real video metrics are reported.

## 2026-09-23 — fail closed on malformed fixture detections

- Reproduced that explicit malformed object rows were silently skipped and the API job completed without events.
- FixtureDetector now accepts a missing objects field as empty, but rejects a malformed explicit list or row with an indexed error. API regression verifies failed status and empty event storage.
- Targeted provider/fact-pipeline/API tests returned 39 passed; source and staged suites returned 154 passed.
- Updated provider and algorithm docs and synchronized the curated package; post-scan found no forbidden artifacts or sensitive literals and 21 source/doc hashes matched.
- This is fixture input-integrity evidence, not real model detection evidence.

## 2026-09-23 — scope workshop event deduplication by region

- Reproduced same-time shelf A and bench B removals for one object collapsing into one removal and one timeout-missing candidate.
- Added region scope to workshop dedup keys so distinct zones retain their evidence while same-zone duplicates still merge.
- Targeted reasoner/plugin tests returned 28 passed; source full suite and staged verifier returned 155 passed.
- Updated AI temporal/scene docs and the curated submission; post-scan found no forbidden artifacts or sensitive literals, and 21 synchronized hashes matched.
- Evidence uses synthetic facts and zones; real camera overlap behavior remains unmeasured.

## 2026-09-23 — numeric threshold input contracts

- Reproduced bool thresholds being accepted as 1 and numeric strings raising inconsistent TypeError in relation/tracker/reasoner configuration.
- Hardened MotionDetector, CentroidTracker, RelationEngine, MedicationSequenceReasoner and WorkshopStateReasoner to reject bool/string values and enforce finite/range checks with ValueError.
- Targeted provider/relation/reasoner tests returned 120 passed; full source suite and staged verifier returned 173 passed.
- Updated algorithm/config docs and synchronized the submission. Post-scan found no forbidden artifacts or sensitive literals; 21 hashes matched.
- Evidence covers deterministic configuration validation only.

## 2026-09-23 — reset relation continuity after detection gaps

- Reproduced stale `motion`, `putdown_candidate`, and `left_zone` outputs when an entity was missing for a sampled frame and later reappeared.
- RelationEngine now clears the affected previous-position, proximity-pair, and zone-membership continuity; the JSONL frame-to-fact regression confirms no event is inferred across the missed sample.
- Targeted relation/fact-pipeline tests: 62 passed. Source and curated submission suites: 180 passed each; submission verifier returned `VERIFY_OK` with 386 third-party deprecation warnings.
- Initial staged run exposed four existing reasoner tests and one implementation file missing from the curated package. Synced the current AI reasoner source/tests, then confirmed all 36 AI source/test/config hashes and six updated AI docs match the staged copy.
- Updated the AI algorithm/temporal docs and current concise evidence summaries. The pinned Makerverse/livestream-rs repositories remain media/control integration references; they did not supply a vision model for this work.
- Limits: synthetic JSONL/CPU only; missed events during fully unobserved intervals remain possible, and real camera/model performance is unverified.

## 2026-09-23 — fail closed on Boolean keypoints and preserve grayscale precision

- Reproduced malformed Boolean keypoints creating a `hand_to_face` fact and a possible complete medication event. Tightened keypoint geometry, identity and configuration validation; invalid action geometry is treated as absent evidence.
- Reproduced MotionDetector quantizing fractional grayscale into a false threshold crossing and clipping an out-of-range pixel into a detection. The CPU detector now preserves float intensities and rejects values outside finite non-Boolean `[0,255]`, resetting history after invalid input.
- Added JSONL-to-elderly-care regression plus keypoint/config tests; targeted action/fact tests returned 26 passed. Provider tests returned 43 passed.
- Full source suite and curated submission verifier both returned 203 passed; verifier returned `VERIFY_OK` with 386 third-party deprecation warnings. All 36 AI source/test/config hashes match, six updated AI docs match staged copies, and local pytest temp dirs were cleaned.
- These are deterministic CPU/fixture integrity results. No learned pose/object model or real video metrics are established.

## 2026-09-23 — reject coerced registry features

- Reproduced Boolean embeddings being normalized into valid vectors and marked `accepted=true`, numeric strings and Boolean thresholds being coerced by request models, and out-of-range gray pixels being clipped into a feature.
- Embedding vector/matrix and threshold validators now reject booleans and coercible strings; grayscale accepts only finite `[0,255]` values and preserves fractions. Vector normalization uses an overflow-resistant norm. API handlers return 400 for empty/all-zero registration vectors without persisting them; schema type errors return 422.
- Targeted embedding/API tests returned 35 passed. Full source suite and curated verifier returned 223 passed; `VERIFY_OK`, 454 third-party deprecation warnings.
- Updated registry/algorithm docs and concise submission evidence. Limits remain CPU heuristic and synthetic data, with no real identity recognition metrics.

## 2026-09-23 — preserve label-distinct medication candidates without IDs

- Reproduced two complete same-person sequences for different no-ID medication labels collapsing to one candidate at the reasoner dedup stage.
- Dedup now prefers entity IDs and falls back to normalized labels only when IDs are absent. Same-label duplicate evidence still collapses; distinct labels remain separate.
- Added reasoner tests and an elderly-care plugin integration test. Targeted reasoner/plugin suite returned 43 passed.
- Full source and curated submission suites returned 226 passed; `VERIFY_OK`, 454 third-party deprecation warnings. All 36 AI code/test/config hashes and seven AI documentation copies match; local pytest temp dirs were cleaned.
- Evidence remains constructed facts and a deterministic plugin path; no real detector or visual identity performance is claimed.

## 2026-09-23 — reject explicit non-person medication subjects

- Reproduced an ID-bearing `自动发药柜` subject being treated as a person and producing `suspected_medication`.
- Medication inference now rejects a subject with an explicit unsupported/non-person label. It retains ID-only subjects without labels solely for legacy fact compatibility.
- Added complete/incomplete reasoner tests and an elderly-care plugin regression. Targeted reasoner/plugin tests returned 45 passed.
- Source and curated submission suites returned 228 passed; verifier returned `VERIFY_OK`. All 36 AI source/test/config hashes and seven AI doc copies match; project-local temp dirs were cleaned.
- Results use constructed facts, not real person-detector output.

## 2026-09-23 — validate PrimitiveFact confidence before coercion

- Reproduced Boolean confidence=True becoming 1.0 and numeric strings becoming floats before reasoner threshold checks; the malformed fact could generate a complete suspected-medication event.
- PrimitiveFact now validates confidence before coercion as a finite non-Boolean real in [0,1]; integers and floats remain valid.
- Targeted reasoner/plugin suite returned 52 passed. Full source and curated submission suites returned 235 passed; VERIFY_OK, 454 third-party deprecation warnings.
- Updated temporal/algorithm docs and agent state. All 36 AI source/test/config hashes match, seven AI docs match their staged copies, and the project-local pytest temp directory was cleaned.
- Limitation: input contract tests do not calibrate detector confidence on real footage.

## 2026-09-23 — reject malformed temporal identity values

- Reproduced bool, fractional, and list-valued IDs being stringified and treated as stable person/object identities, yielding a complete medication event.
- Entity IDs now accept only non-empty strings or integers. Malformed object IDs cannot trigger the label fallback; truly blank/missing IDs retain the existing label-based compatibility behavior.
- Targeted reasoner/plugin tests returned 58 passed. Full source and curated submission suites returned 241 passed; `VERIFY_OK`, 454 third-party deprecation warnings.
- AI source/test/config hashes and seven staged AI docs match. Project-local test temp directories were cleaned; evidence remains constructed facts, not real detection performance.

## 2026-09-23 — select confidence-qualified action evidence

- Reproduced a low-confidence matching hand action masking a later qualified action and a low-confidence optional put-down suppressing an otherwise valid complete sequence.
- Complete inference now continues to a same-person/same-object hand fact meeting the threshold; weak optional put-down evidence is ignored. Incomplete inference retains its explicit rule that a matching action fact means the step was observed.
- Targeted reasoner/plugin tests returned 60 passed. Source and curated submission suites returned 243 passed; `VERIFY_OK`, 454 third-party deprecation warnings.
- Updated algorithm/temporal docs and state records; 36 AI source/test/config hashes and seven staged AI docs match, and project-local pytest temp directories were cleaned.
- Limits: constructed facts only; real gesture confidence and event quality have not been evaluated.

## 2026-09-23 — distinguish medicine objects from storage locations

- Reproduced storage/location labels such as 药柜 and medicine cabinet being classified as medicine objects, allowing a hand-to-face geometry rule to generate a suspected medication event.
- The shared medication classifier now excludes known storage/location labels, with explicit medicine/medication/drug categories taking precedence. Added direct reasoner and JSONL-to-elderly-plugin coverage.
- Targeted reasoner/fact/plugin tests returned 76 passed; reasoner/plugin-only tests returned 68 passed. Full source and curated submission suites returned 252 passed; `VERIFY_OK` with 454 third-party deprecation warnings.
- Synchronized AI code/tests/docs; 36 source/test/config hashes match, seven docs match staged copies, and project-local temp dirs were cleaned.
- Limits: local fixture evidence only; real model class quality and label alias recall remain unverified.

## 2026-09-23 — isolate stateful motion detector sessions per job

- Reproduced source interleaving corrupting the single shared MotionCPUProvider history in the service-level detector registry.
- Added job-local provider sessions for stateful motion detection and wired FrameFactExtractor to request a fresh session; stateless fixture providers remain shared.
- Targeted provider/frame-pipeline tests returned 13 passed. Source and curated submission suites returned 254 passed; `VERIFY_OK`, 454 third-party deprecation warnings.
- Synced AI code/tests/docs; all 36 source/test/config hashes match, seven AI docs match the curated copy, and project-local pytest temp dirs were cleaned.
- Limitation: synthetic frames only; real video concurrency and detector quality remain unverified.

## 2026-09-23 — reject overflowing bbox and zone extents

- Reproduced finite bbox/zone components summing to an infinite edge, causing invalid region coverage and potentially unbounded geometry in keypoint proximity.
- Detection, Entity, Zone, JSON environment-zone parsing through Zone, and KeypointActionExtractor bbox inputs now require finite computed right/bottom edges.
- Targeted provider/relation/zone-config/keypoint tests returned 130 passed. Full source and curated submission suites returned 259 passed; verifier returned VERIFY_OK with 454 third-party deprecation warnings.
- Synced code/tests/docs; all 36 AI source/test/config hashes match and seven AI docs match the staged copy; local pytest temps were cleaned.
- Evidence is synthetic extreme-coordinate validation; no real camera range is established.

## 2026-09-23 — prevent relation cooldown-key collisions

- Reproduced string-concatenated cooldown collisions for valid colon-containing person/object and entity/zone IDs, causing a distinct near/pickup or zone-entry event to be suppressed.
- Replaced concatenated strings with structured tuple keys for all relation cooldown categories and zone-edge direction.
- Targeted relation tests returned 60 passed. Full source and curated submission suites returned 261 passed; `VERIFY_OK` with 454 third-party deprecation warnings.
- AI source/test/config hashes and seven AI docs match staged copies; project-local test temps were cleaned. Evidence uses synthetic IDs only.

## 2026-09-23 — ignore unrepresentable keypoint numbers safely

- Reproduced unbounded JSON integers in keypoints/bboxes raising OverflowError during float conversion and aborting the frame-to-fact job.
- KeypointActionExtractor now treats values that cannot become finite floats as absent geometry; invalid extreme configuration values raise ValueError.
- Targeted keypoint/frame-pipeline tests returned 33 passed. Source and curated submission suites returned 265 passed; `VERIFY_OK` with 454 third-party deprecation warnings.
- Synced AI code/tests/docs; 36 AI source/test/config hashes and seven AI docs match staged copies, and local pytest temps were cleaned.
- Evidence is synthetic only; no real pose model or video metrics are claimed.

## 2026-09-23 — propagate stop requests into running frame extraction

- Reproduced that an active analysis job could continue traversing source frames after stop_job because its cancellation event was not passed into FrameFactExtractor.
- Each analysis job now has a CancellationToken propagated to the frame pipeline/provider; extraction checks between frames and cancellation returns stopped without evaluating plugins or storing partial events.
- Targeted core/fact/frame-pipeline tests returned 23 passed. Full source and curated submission suites returned 266 passed; `VERIFY_OK` with 454 third-party deprecation warnings.
- Limit: a synchronous decoder call already underway cannot be interrupted until it returns; frame-boundary cancellation and event non-persistence are verified using a deterministic provider.

## 2026-09-23 — map sampled motion regions back to source pixels

- Reproduced motion bboxes staying in the downsampled matrix coordinate system while zone config and relation geometry use source-frame pixels.
- MotionDetector now scales boxes back to source pixels, clips the final sample cells, and resets comparison history when source image dimensions or sampling stride changes.
- Provider tests returned 46 passed. Full source and curated submission suites returned 268 passed; `VERIFY_OK` with 454 third-party deprecation warnings.
- Synced code/tests/docs; 36 AI source/test/config hashes and seven AI docs match staged copies, and local pytest temps were cleaned.
- Limit: synthetic image-array only; no real camera coordinate or accuracy claim.

- Completed running-job cancellation propagation and frame-boundary stop regression; source and staged suites reached 266 passed.
- Mapped sampled motion regions to source-frame pixels, preserving zone/relation coordinate consistency; source and staged suites reached 268 passed.
- Hardened job finalization: per-job terminal locking, atomic event-batch/completed-status transaction, and idempotent completed-job rerun; added stop/completion race regressions. Source and curated submission suites reached 270 passed with VERIFY_OK; updated current AI docs and evidence.

- Reproduced WorkshopStateReasoner inferring object_returned from simultaneous left_zone/entered_zone facts based solely on input order. Updated transition matching to require strictly earlier removal evidence; added permutation tests for inferred and explicit transitions. Targeted reasoner/plugin suite: 72 passed; source and curated suites: 274 passed, VERIFY_OK. Synced the AI module and current reasoning docs.

- Reproduced a false suspected_medication candidate for an object labeled 药品说明书. Added shared negative target labels for instructions/lists/records/prescription forms/package inserts, preserving explicit medicine category precedence; added reasoner and JSONL/plugin regressions. Targeted suite 85 passed; source and curated suites 288 passed with VERIFY_OK.

- Reproduced stale RelationEngine cooldowns suppressing near/pickup, motion, and zone events after a detection gap, plus finite coordinate arithmetic overflowing to Infinity in relation facts. Pruned cooldown state with its evidence continuity and dropped non-finite distances/displacements. Added five tests; relation suite 65 passed, source and curated suites 293 passed, VERIFY_OK.

- Audited JSON-number conversion boundaries after confirming oversized integers raised OverflowError outside the keypoint path. Added ValueError normalization for detector/entity/zone geometry and confidence, tracker/relation thresholds, AI_ZONES_JSON, and reasoner thresholds; guarded timedelta range and revalidated fact confidence at inference. Targeted numeric suite 53 passed, reasoner/plugin suite 95 passed, full source/curated suites 311 passed, VERIFY_OK.

- Reproduced permissive/coercive FramePipeline arguments: True became a 1 ms interval or one-frame cap, while fractional max_frames leaked TypeError. Added strict integral/range checks and zero-frame behavior. Targeted frame-pipeline tests: 15 passed; source and curated suites: 321 passed, VERIFY_OK.

- Mocked OpenCV to reproduce FPS/PTS metadata OverflowErrors. Added finite metadata normalization, 25 fps fallback, PTS read-index fallback, and explicit range errors; eight mocked metadata regressions pass. Full source and curated suites returned 329 passed with VERIFY_OK.

- Reproduced recovered-JSONL state leakage: after a malformed line was skipped, the following valid frame could inherit pre-gap detector/tracker/relation/keypoint state and temporal evidence. Added discontinuity metadata, `observation_gap`, continuity segments, detector-session recreation, and cross-gap reasoner rejection; six targeted regressions passed and the reasoner/plugin subset returned 97 passed.
- Synchronized ten AI source/test files, eight AI algorithm documents, the staged README/report, and the verifier's absolute project-local pytest basetemp. Full source and curated submission suites both returned 334 passed; `VERIFY_OK`, 454 non-blocking third-party warnings. All 41 AI hashes match; only the pre-existing PHASE0_AUDIT docs mismatch remains. No external PROJECTS.json entry was created or changed.

- Read and visually checked the two user-provided AIC competition PDFs. Mapped the current project to candidate `AI+场景创新`, recorded the 20/15/20/15/10/15/5 score table and material constraints, and separated official rule facts from the user transcript's privacy/skeletonization design input.
- Added the rules-alignment document and updated AI algorithm, experiment, material-pack, readiness, and evidence-summary docs. No algorithm source or test behavior changed; real camera-side privacy processing, model/data metrics, application effects, and robot evidence remain open.

- Reproduced a frame-preview privacy leak where top-level JSONL `gray` matrices were serialized through `/api/v1/sources/frames`; the existing sanitizer only handled OpenCV `image` payloads. Added redaction for `image`, `gray`, `pixels`, and `raw_pixels`, preserving shape/encoding summaries and fixture object rows. API tests returned 8 passed; source and curated suites returned 335 passed with `VERIFY_OK`.
- Synchronized `app.py`, `test_api.py`, privacy/competition docs, and the curated submission package. The fix covers REST serialization only; camera-side skeletonization and raw-frame retention remain external evidence gates.

- Reproduced a workshop state leak when `observation_gap` was omitted by an upstream caller: later-segment return/missing/scene observations could consume an earlier pending removal. Added same-`continuity_segment` filters for explicit and timeout transitions, with two regressions. Reasoner/plugin tests returned 99 passed; source and curated suites returned 337 passed with VERIFY_OK.
- Synchronized `algorithm_reasoner.py`, `test_algorithm_reasoner.py`, and temporal/plugin documentation; no real scene or robot evidence was inferred from the fixture facts.

- Extended frame-preview redaction to nested, hyphenated, camelCase, depth, thermal, RGB/BGR, and raw-frame keys; added a nested JSONL regression preserving pose metadata. Source and curated suites returned 338 passed with VERIFY_OK.
- Audited the four reference DOCX works in `算法精英/` and added `REFERENCE_ALGORITHM_AUDIT.md`, explicitly retaining their privacy, tracking, multimodal, safety, and sim-to-real ideas as references rather than current evidence. Renderer absence was recorded.

- Added `AI_ALGORITHM_ANALYSIS_PLAN.md` with staged P0–P4 work packages linking the supplied DOCX ideas to current AI contracts, future model/data gates, temporal scenes, multimodal quality handling, and robot validation. Synchronized the plan to the curated package without changing source behavior.

- Reproduced reusable `KeypointActionExtractor` state leaking across source changes. Added source-based episode/frame reset and mixed-source rejection with two regressions; source suite reached 340 passed. Curated VERIFY remains to be run for this checkpoint.

- Reproduced keypoint/relationship provenance mixing across source IDs. Propagated `source_id` through FrameFactExtractor facts and rejected mismatched relation evidence; source and curated suites reached 341 passed with VERIFY_OK.

- Reproduced stale keypoint relation evidence from an older frame. KeypointActionExtractor now matches relation facts only to the current UTC frame timestamp and rejects mixed observation timestamps; source and curated suites reached 344 passed with VERIFY_OK.


## 2026-09-24 — source-isolated temporal reasoning (AI scope)

- Audited the P0–P3 code boundary after the user limited work to AI algorithms. The concrete remaining issue was cross-source fact pairing in the temporal reasoners.
- Added conservative source signatures and same-source checks for medication hand/action/support facts and workshop return/missing/observation evidence. Pending workshop state now includes the source signature so same IDs from different sources do not overwrite one another.
- Added emitted-action source metadata and four temporal provenance regressions plus one keypoint metadata assertion.
- Targeted tests: `125 passed`. Full source suite: `348 passed`, 562 non-blocking deprecation warnings. Curated `VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `348 passed`.
- Synced AI source/tests/docs and updated project-local evidence records. No hardware/robot/frontend work was performed.


## 2026-09-24 — P0 pixel metadata privacy boundary

- Audited the remaining P0 path after frame-preview redaction and found detector metadata could still carry raw pixel-like arrays into `PrimitiveFact`, vision preview, job metadata, and SQLite.
- Added shared recursive sanitization and applied it at frame facts, vision preview, service job creation, and storage event/job serialization. Preserved keypoints, labels, bboxes, source IDs and shape/encoding summaries.
- Added four focused regressions plus nested sanitizer coverage. Source full suite: `352 passed`, 616 non-blocking deprecation warnings. Curated VERIFY: `VERIFY_OK`, `352 passed`.
- Synced code/tests/docs/submission and recorded the evidence boundary. No hardware, robot, frontend, camera calibration or real-model work was performed.


## 2026-09-24 — P3 software quality/degradation contract

- Added strict optional `channel_quality` metadata validation and a quality decision summary.
- Integrated usable/degraded/blocked behavior into frame-to-fact extraction, with observation-gap state reset when no usable or required channel is available.
- Added nine quality contract cases and two JSONL pipeline regressions. Full source suite: `363 passed`, 616 non-blocking warnings. Curated VERIFY: `VERIFY_OK`, `363 passed`.
- Updated P3 analysis/design/provider/temporal docs and synchronized the curated package. Real sensor timing and quality remain explicitly unverified.


## 2026-09-24 — AI algorithm completion report

- Created `workspace/docs/AI_ALGORITHM_COMPLETION_REPORT.md` as the detailed overall AI algorithm completion report and synchronized it to `workspace/submission/docs/`.
- The report consolidates the frame/detector/tracker pipeline, privacy boundary, keypoint actions, temporal reasoners, quality gate, API/storage behavior, competition/reference-material audit, test evidence and remaining real-data gates.
- After adding the report, curated `VERIFY.ps1 -SkipFrontendBuild` still returned `VERIFY_OK` / `363 passed`.

## 2026-09-24 — initialize private GitHub development repository

- Paused AI feature expansion as requested and created `https://github.com/weiyang02520-ops/aic-visual-event-platform` as a private repository with default branch `main`.
- Initialized the existing project root rather than creating a replacement project. Initial checkpoint: `9481004b94e983faa2dd8780c021b6fa6c0806a8`, message `chore: initialize AIC visual event AI development repository`.
- Kept AI source/tests, frontend source, docs, submission package and current agent-state. Excluded unpublished PDF/DOCX materials, source snapshots, rollback copies, runtime/cache/dependency/build output, model weights and secrets.
- Staged audit found 245 tracked files, no non-example `.env`, no credential/private-key patterns and no tracked file above 10 MB. Existing AI verification remains `363 passed` / `VERIFY_OK`.
- Next action is repository review and collaboration; do not extend AI functionality until the user asks.


## 2026-09-24 — initialize Master × GitHub × Codex automation
- Adopted the uploaded automation template for this private repository.
- Preserved `agent-state/`; added `.ai/` as the task/state/lock/heartbeat/review control plane.
- First bounded target: real visual person/pose provider adapter because the current baseline explicitly lacks real pose inference.
- Bootstrap is control/documentation only and does not itself claim new model capability.


## 2026-09-24 — TASK-0001 optional real vision provider

- Claimed `TASK-0001` from the latest `main` state after verifying status `READY_FOR_CODEX`, task version/hash and an empty lock. Created branch `codex/task-0001-real-vision-provider`.
- Added optional `ultralytics` extra and `UltralyticsProvider`; kept model loading lazy and unavailable when dependency/model is absent.
- Added deterministic fake-result normalization, malformed-output, unavailable-runtime, API registry and frame/fact integration tests.
- Source full suite: `368 passed`; curated verifier: `VERIFY_OK`, `368 passed`.
- Real runtime smoke was not performed because the optional package and model path are absent; no weights were downloaded.
- Pending: commit, push, PR and Master review. Do not select TASK-0002.

## 2026-09-24 — TASK-0001 PR handoff

- Commit `d819e5a44fd8854e58e8a26d25adb04632f3751a` pushed on `codex/task-0001-real-vision-provider`.
- Opened [PR #2](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/2) targeting `main`; GitHub reports `OPEN` and merge state `CLEAN`.
- Updated `.ai/CODEX_REPORT.md`, run record, state and heartbeat; released the task lock and handed control to Master.


## 2026-09-24 — TASK-0001 R1 fix

- Read Master review R1 from the latest remote branch: documented `AI_ULTRALYTICS_MODEL_PATH` was not wired into registry-created providers.
- Fixed provider environment-path wiring and added offline registry selection/status regression.
- R1 targeted tests: `10 passed`; source full suite: `369 passed`; curated VERIFY: `VERIFY_OK`, `369 passed`.
- Real model remains unverified; no weights/downloads. PR #2 remains open for Master review.

## 2026-09-24 — TASK-0001 R1 PR handoff

- R1 fix commit `e5f6180` pushed to the existing task branch and PR #2.
- Registry now wires the documented `AI_ULTRALYTICS_MODEL_PATH`; offline regression and full verification pass (`369 passed`, `VERIFY_OK`).
- State returned to `WAITING_FOR_MASTER`, `next_actor=chatgpt`, lock released. No TASK-0002 selected.
