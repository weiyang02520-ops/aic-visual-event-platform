# Decisions

## DEC-001
- Date: 2026-09-22
- Status: active
- Decision: 将 `C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料` 作为本项目资料根目录；开发代码放在其 `workspace/` 下。
- Reason: 用户明确指定后续任务在该文件夹内，且交接计划要求开发、状态和提交目录隔离。
- Alternatives: 继续在原工作区开发；不采用。
- Consequences: 后续命令和文件路径必须显式指向该根目录，不把临时开发文件写入 `workspace/submission/`。

## DEC-002
- Date: 2026-09-22
- Status: active
- Decision: 交接计划书作为项目规格参考，不能覆盖系统规则、开发者指令或用户后续明确变更。
- Reason: 需要区分附件中的指令性文字与当前会话用户请求。
- Alternatives: 将附件中的所有文字无条件视为最高优先级；不采用。
- Consequences: 每项重要要求需标注来源；涉及机器人、赛道和真实指标的内容必须以新文档或实测证据补充。

## DEC-003
- Date: 2026-09-22
- Status: active
- Decision: 采用根目录 `agent-state/` 加 `workspace/{ai-engine,frontend,docs,submission}/` 作为唯一目录布局。
- Reason: 计划书正文和附录存在两套目录写法；根目录状态与工作区/提交包分开更容易恢复和清洁打包。
- Alternatives: 同时保留 `workspace/agent-state/`、`ai-dev/` 或 `frontend-dev/`；不采用，避免状态和代码分叉。
- Consequences: 后续所有状态文件写入根目录 `agent-state/`；`workspace/submission/` 只放可提交成果。

## DEC-004
- Date: 2026-09-22
- Status: active
- Decision: 在最终赛道、老师主文档和机器人资料到位前，优先实现通用 AI 事件闭环与 Mock 前端，不冻结比赛专用算法或机器人能力。
- Reason: 当前赛道、评分点、数据、硬件和协议均未被证实；先冻结专用方向会造成返工或文档夸大。
- Alternatives: 直接按智慧养老服药识别和未来机器人控制定稿；不采用。
- Consequences: 比赛叙事、模型训练目标、真实指标和机器人集成属于待确认项。

## DEC-005
- Date: 2026-09-22
- Status: active
- Decision: 用户已确认 `Codex_Master_Execution_Plan_V5_FINAL.md` 是最终长期执行计划；前面的计划体检只作为内部执行风险记录，不要求用户先解决这些问题。
- Reason: 共享对话确认用户的目标是把计划书交给 Codex，自主完成 AI、前端、文档和提交材料，用户不参与普通技术选型。
- Alternatives: 继续要求用户逐项确认版本、目录和技术路线；不采用。
- Consequences: 后续 Codex 按计划书持续推进；只有外部资料、凭据、付费、硬件权限或不可逆决定缺失时才暂停请求用户输入。

## DEC-006
- Date: 2026-09-22
- Status: active
- Decision: 视频输入先通过 `FrameProvider`/`FramePipeline` 抽象；在 FFmpeg、livestream-rs 或机器人 SDK 不可用时，使用 Mock 和 JSONL fixture 完成可验证降级。
- Reason: 保留真实输入替换点，同时避免把“已配置”写成“已连接”或伪造视频帧。
- Alternatives: 在缺少运行时工具链时直接硬编码 RTSP/MP4 读取；不采用。
- Consequences: 当前 JSONL 和 Mock 只用于测试、演示和接口验收；真实媒体 provider 后续独立接入。

## DEC-007
- Date: 2026-09-22
- Status: active
- Decision: 先提供纯 CPU 的帧差 MotionDetector、质心 CentroidTracker 和关系规则基线，再替换真实深度模型。
- Reason: 模型数据、目标赛道和硬件推理环境尚未确认；可解释基线能先固定 source/timestamp/fact/event 证据链。
- Alternatives: 先下载并绑定一个未经比赛资料确认的 YOLO 模型；不采用。
- Consequences: 基线不得报告准确率，不代表老人服药识别模型；真实 Detector 只替换 provider，不改变统一事件和复核流程。

## DEC-008
- Date: 2026-09-22
- Status: active
- Decision: 本地 JSONL/OpenCV 帧通过 `FrameFactExtractor` 进入 analysis job；RTMP/RTSP/HLS 仍必须经过显式流媒体 provider。
- Reason: 让“输入→检测/跟踪→关系→PrimitiveFact→插件”成为实际链路，同时保留真实流媒体未联调的证据边界。
- Alternatives: 只在 API 层展示帧，不接入分析任务；不采用。
- Consequences: 本地文件任务可以得到可核验的 fact_count；没有配置流媒体 provider 时任务明确失败，不生成假事件。

## DEC-009
- Date: 2026-09-23
- Status: active
- Decision: 当前接管任务只推进 AIC 项目 AI 算法、对应测试、AI 算法文档和 `agent-state/`。
- Reason: 用户明确限定当前主线为 AI 识别算法分析与可验证实现，并要求不修改其他工作区。
- Alternatives: 同时推进前端视觉和长篇比赛文档；不采用。
- Consequences: 不触碰 `workspace/frontend/`、Makerverse、livestream-rs 或其他工作区；真实数据/模型/机器人结论仍待对应证据。

## DEC-010
- Date: 2026-09-23
- Status: active
- Decision: 将时序推理候选保留为人工复核的规则假设；药品完整序列要求同一人物/对象的先后事实，工作室归还要求同一对象回到原区域，缺失超时要求 `scene_observed`。
- Reason: 普通盒子、物品 ID 冲突、`putdown_candidate` 和任意不相关事实都不能证明服药、归还或物品缺失。
- Alternatives: 用近邻关系或任意后续事件推断高层状态；不采用。
- Consequences: 当上游动作或场景观察事实缺失时，插件不生成完整高层事件；本地规则测试不能替代真实模型/数据评估。

## DEC-011
- Date: 2026-09-23
- Status: active
- Decision: 当前及后续 AI 任务只能创建、修改或清理 `C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料` 根目录之内的文件；测试临时目录也必须放在该根目录内并在验收后清理。
- Reason: 用户明确限定允许变动的唯一文件目录。
- Alternatives: 在系统临时目录或其他 workspace 写入中间产物；不采用。
- Consequences: 未来测试通过项目内 `--basetemp` 运行；提交副本、AI 文档和状态记录均留在此项目根目录。

## DEC-012
- Date: 2026-09-23
- Status: active
- Decision: 关系抽取和时序推理共用一个人物标签分类函数，统一处理中文家庭/工作人员标签及英文大小写变体。
- Reason: 不同层使用不一致的人物标签会把“家属”等目标当普通物体，导致关系事实缺失，后续时序插件无法推理。
- Alternatives: 在关系层和事件 reasoner 中各维护独立标签集合；不采用。
- Consequences: 新增人物类别时应更新共享分类器和跨层回归测试。

## DEC-013
- Date: 2026-09-23
- Status: active
- Decision: `hand_to_face` 的本地规则只消费 provider/fixture 显式提供的 `nose`、`left_wrist`、`right_wrist` keypoints；必须满足关键点置信度、人物框归一化近脸距离和 wrist-to-medication-box 距离，且只在连续动作进入阈值时发一条事实。
- Reason: 不能把通用帧差或物体检测伪装成姿态估计；同一个人的脸部动作还需关联到同一药品对象才能进入服药时序规则。
- Alternatives: 从像素变化推断手部/服药动作，或只依据人物近药盒和手部近脸分别组合；不采用。
- Consequences: 该规则仅是显式 keypoints 的 CPU geometry baseline；真实关键点仍需 verified pose/action provider 和授权视频评估。

## DEC-014
- Date: 2026-09-23
- Status: active
- Decision: 几何关系组件拒绝非有限/无效 bbox、confidence、zone 尺寸和 near/motion/cooldown 配置。
- Reason: 无效几何参数会静默抑制关系或制造不可信事实，且缺少数据时不能靠测试约定猜测意图。
- Alternatives: 将异常配置当成“没有关系/没有区域”继续运行；不采用。
- Consequences: 调用方必须提供正尺寸区域、有限有效置信度和距离阈值；错误配置显式失败。

## DEC-015
- Date: 2026-09-23
- Status: active
- Decision: Optional workshop regions enter through AI_ZONES_JSON, a strict JSON array of pixel rectangles; the default is empty and invalid entries fail app startup.
- Reason: Silent fallback on misspelled or invalid geometry could make zone facts disappear without an operator noticing. Keeping the default empty avoids inventing camera calibration.
- Alternatives: Hard-code generic camera regions or silently ignore malformed entries; not adopted.
- Consequences: Deployment must provide coordinates in the detector frame pixel coordinate system and calibrate them against the actual camera before treating zone events as real-scene evidence.

## DEC-016
- Date: 2026-09-23
- Status: active
- Decision: Workshop removal state is keyed by tracked object and zone scope; an entered_zone fact can resolve only the matching zone's pending removal.
- Reason: A single object-level slot let leaving a second zone overwrite the first zone's pending return and suppress a valid return event.
- Alternatives: Keep only the newest zone and lose earlier pending state, or allow entry into any zone to resolve the removal; neither preserves same-zone semantics.
- Consequences: A zone transition remains tied to the exact zone_id, or to the normalized zone label when IDs are absent; real camera calibration remains a separate evidence requirement.

## DEC-017
- Date: 2026-09-23
- Status: active
- Decision: If both the removal fact and scene_observed fact declare a region, timeout evidence must refer to the same zone ID or normalized zone label. If either is unscoped, preserve the existing global-observation contract.
- Reason: A localized observation from an unrelated region cannot establish absence from the item's last region; keeping unscoped compatibility avoids changing existing upstream fact semantics without an observation-coverage contract.
- Alternatives: Let any localized observation prove every pending absence, or require same-zone evidence even for legacy unscoped facts; neither is adopted.
- Consequences: Future scene-observation providers should declare coverage explicitly; current fixture results do not validate camera coverage.

## DEC-018
- Date: 2026-09-23
- Status: active
- Decision: An explicit object_missing with a zone ID or location may consume only pending removal state from that same zone. Unscoped object_missing keeps its prior global behavior.
- Reason: Choosing the newest removal for the object can attach a missing event at one location to a removal at another.
- Alternatives: Always consume the newest zone regardless of explicit scope, or force a zone on every legacy missing fact; neither is adopted.
- Consequences: Upstream producers should attach zone scope whenever the missing assertion is localized; real camera calibration remains unverified.

## DEC-019
- Date: 2026-09-23
- Status: active
- Decision: Zone IDs and labels are non-empty strings normalized by trimming; coordinates are finite numeric values (booleans and numeric strings are rejected), dimensions are positive, and one RelationEngine input cannot contain duplicate IDs. A blank zone_id on external facts falls back to normalized location matching.
- Reason: Empty or duplicate IDs collapse independent region histories, while permissive coordinate coercion lets malformed inputs reach geometry logic.
- Alternatives: Trust JSON-parser validation while leaving direct constructors permissive; not adopted because tests and adapters also instantiate Zone directly.
- Consequences: Callers supplying zones programmatically receive the same validation boundary; physical coordinate calibration remains separate.

## DEC-020
- Date: 2026-09-23
- Status: active
- Decision: Entity requires a non-empty trimmed ID and label, finite numeric bbox coordinates with positive size, and finite numeric confidence in [0, 1]. RelationEngine rejects duplicate entity IDs before advancing timestamp/zone state.
- Reason: Invalid direct inputs previously reached arithmetic with TypeError or shared one temporal state slot across duplicate IDs.
- Alternatives: Rely on detector normalization alone and keep direct Entity construction permissive; not adopted because tests, adapters, and CPU fixtures also instantiate entities directly.
- Consequences: Valid coordinate/confidence values are stored as floats; duplicate IDs in one frame are configuration errors.

## DEC-021
- Date: 2026-09-23
- Status: active
- Decision: Detection boxes retain finite subpixel coordinates; Detection validates non-empty labels, positive geometry, and finite confidence in [0, 1]. FixtureDetector passes raw scores to this contract and fails malformed rows with their index instead of coercing/clamping them.
- Reason: Integer truncation changed relation distances at the 50 px near threshold, and NaN could be clamped to confidence 1.0.
- Alternatives: Keep integer pixel boxes and clamp out-of-range scores; not adopted because it hides malformed scores and alters threshold decisions.
- Consequences: Existing CPU motion detections remain valid integer-valued inputs stored as floats; JSONL fixtures retain fractional precision.

## DEC-022
- Date: 2026-09-23
- Status: active
- Decision: Tracker class compatibility uses the shared person classifier for supported person aliases; other labels match case-insensitively as full category strings, and person/object categories never match each other.
- Reason: Raw label equality split a single person track when detector output changed case or used a supported person alias, breaking downstream same-person temporal evidence.
- Alternatives: Keep raw equality or merge all labels in a broad person/medicine superclass; neither preserves the intended category and identity boundary.
- Consequences: This stabilizes the CPU centroid tracker for label variation but does not add appearance-based identity or real tracking accuracy.

## DEC-023
- Date: 2026-09-23
- Status: active
- Decision: Fixture detection preserves floating pixel boxes and sends scores unchanged through strict Detection validation; invalid fixture rows fail with their object index.
- Reason: Integer truncation altered near-threshold relation decisions, and clamping NaN/infinite/out-of-range scores could manufacture plausible confidence.
- Alternatives: Truncate to integer pixels and clamp scores to [0, 1]; not adopted because both operations hide or alter source evidence.
- Consequences: Existing integer CPU detections remain supported as numeric coordinates, while malformed fixture analysis fails before event persistence.

## DEC-024
- Date: 2026-09-23
- Status: active
- Decision: FixtureDetector returns no detections when the objects field is absent; when objects is explicitly present, it must be a list of object records with four-coordinate bboxes, and malformed rows fail with their index.
- Reason: Silently dropping malformed detections lets an analysis job appear successful while omitting possible events.
- Alternatives: Continue skipping malformed rows, or reject all payloads without objects; not adopted because the former hides data loss and the latter breaks valid empty frames.
- Consequences: Fixture JSONL producers must distinguish an intentionally empty frame from malformed object data.

## DEC-025
- Date: 2026-09-23
- Status: active
- Decision: Workshop candidate deduplication includes region scope for object_removed, object_returned, and object_missing events.
- Reason: The reasoner tracks pending object state per zone; deduplicating only by object and timestamp discarded distinct same-frame region transitions and their evidence.
- Alternatives: Collapse all same-object same-time changes to one generic event; not adopted because it breaks per-zone state evidence.
- Consequences: Overlapping zones may produce multiple reviewable events when the same track exits multiple named regions at once; no real-scene alert-rate metric is available.

## DEC-026
- Date: 2026-09-23
- Status: active
- Decision: Numeric thresholds require non-boolean Real values; count/area settings require non-boolean integral values. Invalid types and invalid ranges raise ValueError before algorithm state is initialized.
- Reason: Python treats bool as int, while math.isfinite/string comparisons can leak TypeError; silent acceptance makes configuration semantics inconsistent across algorithms.
- Alternatives: Coerce strings and booleans, or rely on type hints only; not adopted.
- Consequences: Callers must parse configuration to typed numbers before constructing detectors, trackers, relations, or temporal reasoners.
