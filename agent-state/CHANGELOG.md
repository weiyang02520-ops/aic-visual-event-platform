# Changelog

## 2026-09-22

- 初始化项目资料根目录、workspace 隔离目录和 agent-state。
- 记录长期任务计划书的来源、边界和当前阻塞。
- 完成两个仓库静态审计与源码快照。
- 完成 AI REST/SQLite/插件/MOCK/来源检查骨架；测试从 4 扩展到 15 passed。
- 完成 React/Vite 多页面控制台、Mock/Real provider 和 production build。
- 完成帧管线、CPU 检测/跟踪、关系事实、养老/工作室场景状态增强及对应文档。

## 2026-09-23

- 集成可解释时序 reasoner 到养老/工作室插件，保守约束身份、物品、时间、区域与缺失证据。
- 加强帧差 detector 状态隔离、坏矩阵处理、重复 bbox 跟踪映射和 embedding 输入校验。
- 支持 `FrameFactExtractor` 配置区域，并验证 JSONL fixture 中物品离开/回到同一分区的事件链。
- AI 全量测试增加至 66 项；真实动作模型与授权数据指标仍待上游输入。
- CentroidTracker 改为带距离门控的最大匹配数/最小总距离分配，修复贪心导致的可避免 ID 断裂。
- RelationEngine 对时间做 UTC 归一化并拒绝倒序帧，防止旧帧污染区域/关系状态。
- AI 全量测试更新为 71 passed；真实跟踪/动作精度仍需数据集验证。
- 关系层与时序 reasoner 共用人物标签分类，修复“家属”/英文大小写变体导致接近事实丢失。
- AI 全量测试更新为 73 passed；提交暂存副本同步验收通过。
- 从 detector 提供的显式 pose keypoints 中提取 `hand_to_face` 几何规则事实，并以 JSONL AnalysisService 测试验证完整事件链。
- AI 全量测试更新为 77 passed；关键点规则为 CPU 几何基线，不包含真实姿态模型。
- 加入跨人物 near-relation 拒绝测试，并断言 keypoint 触发事件保持 pending / review-only；AI 全量测试增加到 78 passed。
- KeypointActionExtractor 对单帧关键点丢失增加去抖，长间隔后重新武装；AI 与 submission 全量测试更新为 79 passed。
- RelationEngine 几何输入与阈值配置增加严格校验；AI 全量测试更新为 93 passed，fixture/CPU evidence boundary 保持不变。

- 区域配置入口完成端到端接线：严格解析 AI_ZONES_JSON 并传入 AnalysisService；新增配置/API 回归，源码与提交测试均为 101 passed；提交验收强制项目内 pytest basetemp 并清理。

- 修复工作室跨区域状态覆盖：同一对象按区域分别保留待归还记录，只有回到对应区域才解除；新增跨区往返回归，AI 与提交包全量测试为 102 passed。

- 修复超时缺失证据跨区误关联：移出与观察都标注区域时必须匹配；错区观察不能结案，同区观察按时触发。AI 全量测试更新为 103 passed。

- 显式 object_missing 带区域信息时只关联同区域的待移出事实，防止同一物品不同区域记录串证；AI 全量测试与提交验收更新为 104 passed。

- 直接构造 Zone 与 JSON 配置共用核心输入约束：规范 ID/标签，拒绝非法坐标和重复区域 ID；空事实 ID 回退位置标签，防止跨区误配。全量测试更新为 119 passed。

- Entity 入口增加身份、框和置信度严格校验及规范化；RelationEngine 拒绝重复实体 ID 且不污染时间状态。源码与提交测试更新为 136 passed。

- FixtureDetector 不再截断浮点框或裁剪非法置信度；增加 50.8 px 阈值边界和 NaN/越界分数回归，源码与提交测试为 145 passed。

- CentroidTracker 类别门控复用共享人物标签分类，大小写和已支持人物别名变化不再切断 track ID；增加 JSONL 到事实链连续性测试，测试总数 148 passed。

- FixtureDetector 保留亚像素框坐标并拒绝非法置信度，避免阈值误触发和 NaN 被裁剪成高分；API 回归确认失败任务不落库，测试总数 149 passed。

- FixtureDetector 区分空帧与 malformed objects：无 objects 字段表示空帧，显式错误列表/记录带索引失败；API 验证失败任务不落事件。测试总数 154 passed。

- WorkshopStateReasoner 事件去重加入区域范围，同一时刻同一物品在不同区域的移出/缺失候选不再互相合并；全量测试更新为 155 passed。

- 时序、关系、帧差检测和跟踪器构造器统一拒绝布尔/字符串阈值并规范错误为 ValueError；相关测试总数 173 passed。

- RelationEngine 在实体漏检后清除旧位置、人物—物体接近和区域成员状态；新增 JSONL 集成回归验证不跨观察缺口推断运动、放下或区域离开。源码与提交包均 180 passed，提交验收通过；36 个 AI 源码/测试/配置文件哈希匹配。
- AI 算法文档明确 Makerverse/livestream-rs 是媒体与控制集成参考，本地 AI 逻辑基于 AI 引擎和合成 fixture；不把仓库快照当作识别模型或真实性能证据。

- 关键点动作入口拒绝布尔几何/置信度和错误配置类型，避免 malformed JSON 数值生成 `hand_to_face`；JSONL→养老插件测试确认不会形成完整疑似事件。
- MotionDetector 保留浮点灰度并拒绝布尔、非有限、越界和非数值像素，避免截断/裁剪造成伪运动。源码与提交包均 203 passed，提交验收通过。

- 注册特征路径拒绝布尔/数字字符串和无效灰度/阈值，保留小数特征并使用抗溢出范数；空或全零登记向量返回 400 且不落库。源码与暂存包均 223 passed，验收通过。

- MedicationSequenceReasoner 无对象 ID 时改用规范化标签参与候选去重；同一标签的重复事实合并，不同药品标签各自保留。养老插件端到端回归通过，源码与暂存包均 226 passed。

- MedicationSequenceReasoner 拒绝显式标注为设备/非人物的服药主体，即使存在 ID；保留无标签 ID 旧事实兼容。Reasoner 与养老插件回归通过，源码和暂存包均 228 passed。

- PrimitiveFact 在类型转换前拒绝布尔、字符串、非有限和越界 confidence，避免伪造达到阈值的服药证据。源码与暂存包均 235 passed，验收通过。

- 时序推理 ID 解析拒绝布尔、分数和容器值被字符串化成身份；真正缺失/空白 ID 仍按约定使用标签回退。源码与暂存包均 241 passed，验收通过。

- 服药序列推理会跳过低置信度早期动作继续查找后续达阈值动作，并忽略低置信度可选放下证据，避免它压低完整事件。源码与暂存包均 243 passed，验收通过。

- 共享药品标签分类排除药柜、药架、药房等储存/地点对象，防止将拿取设施误当成药品本体；显式药品类别保留优先权。源码与暂存包均 252 passed。

- MotionCPUProvider 为每次帧提取创建独立状态会话，防止并发来源交错时互相清空帧差历史；帧管线集成回归通过。源码与暂存包均 254 passed。

- Detection/Entity/Zone 及关键点 bbox 拒绝分量有限但右/下边界相加溢出的几何；AI_ZONES_JSON 经相同区域校验。源码与暂存包均 259 passed。

- RelationEngine 冷却状态改用结构化 ID 元组，修复合法冒号 ID 造成的 near/pickup/zone event 键碰撞；源码与暂存包均 261 passed。

- KeypointActionExtractor 将无法转换为有限浮点的极大坐标视为缺失动作证据，避免溢出异常终止帧管线；源码与暂存包均 265 passed。

- AnalysisService 的 job CancellationToken 现在传入帧抽取管线并在帧边界检查，stop 不再等待整个源提取结束；取消任务不调用插件、不落库部分事件。源码与暂存包均 266 passed。

- MotionDetector 对抽样图像的区域框映射回原帧像素，并在源图尺寸/stride变化时清空帧历史；源码与暂存包均 268 passed。

- AnalysisService now serializes stop and completion per job, commits events plus completed status in one SQLite transaction, and returns the existing result for completed-job reruns; regression coverage brings source and curated suites to 270 passed.

- WorkshopStateReasoner now requires a strictly earlier removal timestamp before using it as return/missing evidence; equal-time facts no longer create input-order-dependent transitions. Added four permutation cases; full suites now return 274 passed.

- Shared medicine-object classification now excludes common medicine documentation/list labels, preventing an instruction leaflet from becoming a suspected medication target; explicit upstream medicine categories remain authoritative. Added 14 regressions; full suites return 288 passed.

- RelationEngine now drops event cooldowns when their entity/pair/zone evidence disappears and skips non-finite pair distances/displacements; five regressions bring the full suite to 293 passed.

- Unrepresentable large-number conversions across AI geometry/configuration boundaries now fail as ValueError; reasoner durations are bounded to timedelta's representable range and PrimitiveFact confidence is rechecked before inference. Added boundary regressions; full suite reaches 311 passed.

- FramePipeline now validates interval_ms and max_frames as strict non-Boolean integer inputs, bounds the interval to timedelta, and consistently supports a zero-frame limit; full suites return 321 passed.

- OpenCVFrameProvider now handles invalid FPS/PTS metadata with bounded fallbacks and raises FramePipelineError for unrepresentable sampling/timestamps instead of leaking OverflowError; added eight regression cases, full suites 329 passed.

- JSONL recover mode now marks the next valid frame after a malformed record with discontinuity metadata. FrameFactExtractor emits `observation_gap`, starts a new continuity segment, recreates the detector session, and resets tracker/relation/keypoint state; medication and workshop reasoners reject cross-gap evidence. Added six regressions; source and curated submission suites return 334 passed with VERIFY_OK.
- Curated VERIFY now passes an absolute project-local `.codex-pytest-temp-verify` path to pytest and removes only that verified child plus generated runtime after the run.

- Added AIC rule alignment from the two user-provided PDFs: candidate `AI+场景创新`, exact score mapping, submission-file constraints, originality/privacy requirements, and the distinction between camera-side skeletonization as a target and the current fixture-only keypoint path. Updated the competition, experiment, readiness, and AI algorithm docs without changing source behavior.

- Frame preview API now redacts top-level raw pixel matrices (`image`, `gray`, `pixels`, `raw_pixels`) into encoding/shape summaries; added a JSONL API regression. Full source and curated submission suites return 335 passed with VERIFY_OK.

- WorkshopStateReasoner now requires matching continuity segments when pairing pending removals with returns, explicit missing facts, or timeout scene observations, even if an upstream caller omits the gap fact. Added two regressions; full source and curated submission suites return 337 passed with VERIFY_OK.

- Frame preview redaction now recursively handles normalized image/pixel/depth/thermal/raw-frame keys, including hyphenated and camelCase names; nested privacy regression added. Full source and curated submission suites return 338 passed with VERIFY_OK.
- Added an audit of four user-provided DOCX reference works; their methods and metrics remain source-specific and are not treated as current project evidence.

- Added a staged AI algorithm analysis plan covering privacy/schema, detector/pose/tracking, temporal scenes, multimodal quality gating, and real hardware validation. External document metrics remain unverified.

- KeypointActionExtractor now resets episode state on source changes and rejects mixed-source observations; added source-isolation regressions. Source suite reaches 340 passed.

- FrameFactExtractor now propagates source provenance to facts, and KeypointActionExtractor rejects explicitly mismatched relation sources; added a provenance regression. Full source and curated suites return 341 passed with VERIFY_OK.

- KeypointActionExtractor now requires same-frame UTC relation evidence and rejects mixed observation timestamps; added stale-relation and timezone regressions. Full source and curated suites return 344 passed with VERIFY_OK.


## 2026-09-24 — source provenance isolation for P1/P2 reasoners

- Prevented explicit source IDs from being mixed when forming medication sequences or workshop return/missing evidence.
- Isolated pending workshop state by source and preserved source metadata on generated `hand_to_face` facts.
- Added local regressions; source and curated suites now pass `348` tests.
- Updated AI analysis plan to mark P4 hardware/robot validation out of the current user scope; P0–P3 remain code/contract work only.


## 2026-09-24 — shared P0 pixel-metadata privacy boundary

- Centralized recursive redaction for image/pixel/depth/thermal/raw-frame metadata.
- Applied the same boundary to detector facts, vision preview, job metadata, and SQLite event/job payloads.
- Added contract regressions; source and curated suites now pass `352` tests with `VERIFY_OK`.
- Kept the evidence label at fixture/CPU/local software only; camera-side skeletonization and hardware remain outside the current user scope.


## 2026-09-24 — software multimodal quality gate

- Added a strict optional `channel_quality` contract with usable/degraded/blocked decisions.
- Blocked frames emit `observation_gap` and reset cross-frame AI state; degraded frames continue with a safe quality summary.
- Added fixture regressions and raised source/curated verification to `363 passed` with `VERIFY_OK`.
- Kept hardware, robot, camera calibration and real sensor evidence out of scope.


## 2026-09-24 — AI completion report

- Added the detailed AI algorithm completion report and synchronized the submission copy.
- Recorded the final `363 passed` / `VERIFY_OK` evidence and the distinction between local software proof and real model/data/hardware evidence.
