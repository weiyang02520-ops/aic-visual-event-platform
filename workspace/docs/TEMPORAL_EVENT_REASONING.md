# 时序事件推理：实现与验证边界

最后核验：2026-09-24

## TASK-0009：通用时序视觉记忆与用药计划复核

新增 `visual_event_ai.temporal_memory.TemporalVisualMemory`。它直接接受
`FrameFactExtractor` 返回的 `PrimitiveFact` 列表，并组合已有 `VisualMemory`：
`object_detected` 更新对象最后位置但不进入 action history；
`hand_near_object`、`hand_to_face`、`pickup_candidate`、`putdown_candidate`、
`motion`、`entered_zone`、`left_zone` 和 `object_in_zone` 作为可查询时序记录。

每条 `TemporalFactRecord` 保留 fact type、UTC timestamp、confidence、
`source_id`、`continuity_segment`、subject/object identity 与 label、zone/location、
安全几何和 provider provenance。查询支持 source、continuity、subject/object ID、
label、fact type、recent actions、last action 和 identity timeline；默认时间顺序为
chronological，`recent_actions()` 明确返回 newest-first。记录数和单身份记录数有正整数
上限，拒绝 Boolean-as-integer 配置；`observation_gap` 通过连续段隔离，label 只用于
筛选，不能合并身份。记录和元数据经过 privacy sanitizer，不保存原始像素数组。

新增 `visual_event_ai.medication_plan` 提供 JSON-friendly 的
`MedicationPlanEntry` / `MedicationPlan` 与 `MedicationPlanEvaluator`。计划条目必须
指定药品 label/identity，以及带明确时区的 UTC `scheduled_at` 或 local clock；early/late
容差拒绝布尔值、NaN 和负数。评估器只输出
`plan_match_candidate`、`early_candidate`、`late_candidate`、
`wrong_item_candidate`、`unresolved_candidate` 等 review cue，保留 source/time/
continuity/object evidence，不推断吞咽、剂量正确性或医学结论。相同 episode 的重复
动作去重；同标签并行对象、跨来源和跨 continuity/gap 证据保持 unresolved 或分开处理。

这仍是确定性 Python 规则和软件契约测试，不是药品模型准确率、医学判断或真实摄像头
验收结果。

## 当前状态

| 项 | 当前证据 | 状态 |
|---|---|---|
| 服药相关事实的时序规则 | 单元测试与养老插件接入 | `PASS_LOCAL` |
| 给定关键点的手部靠脸几何规则 | JSONL fixture 到完整事件的端到端测试 | `PASS_LOCAL` / `MOCK_ONLY` |
| 工作室物品状态转移 | 单元测试与工作室插件接入 | `PASS_LOCAL` |
| 真实视频关键点/姿态检测 | 当前无真实姿态模型输出关键点 | `BLOCKED_EXTERNAL` |
| 真实场景缺失告警质量 | 当前帧提取器未生成 `scene_observed` | `BLOCKED_EXTERNAL` |
| 真实数据集事件准确率 | 无授权标注数据集与事件级评估 | `BLOCKED_EXTERNAL` |

本模块是确定性规则基线。`PASS_LOCAL` 只表示代码、插件和合成事实的契约可验证，不表示真实摄像头或机器人上的识别效果。

## 服药相关序列

实现：`workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py` 中的 `MedicationSequenceReasoner`，由 `plugins/elderly_care/plugin.py` 调用。

完整候选必须满足：

1. 事实类型是 `object_picked`、`pickup_candidate` 或 `near`；对象标签/类别明确表示药品。中文药品标签需包含“药”，但药柜、药品柜、药架、药房和药品仓库等储存/地点标签，以及药品说明书、用药说明、药品清单、药品目录、用药记录和处方单/处方笺等文档标签都会被排除；英文 medicine cabinet/shelf、pharmacy、dispensary、drugstore、medication list、medicine instructions、package insert 和 prescription form 等也会被排除。上游显式类别为 medicine、medication 或 drug 时，可作为权威类别覆盖这些显示标签；其他英文药品类别或标签支持 medicine、medication、pill、tablet、capsule、drug。
2. 后续存在 `hand_to_face`、`hand_near_mouth` 或 `object_to_face`。
3. 主体人物 ID 相同，对象 ID 相同；ID 仅接受非空字符串或整数，不接受布尔、分数或容器值。只有对象 ID 真正缺失/空白时，才允许用非空且相同（忽略大小写）的对象标签匹配；显式但格式错误的对象 ID 不触发标签回退。
4. 手部动作在拿取/接近事实之后，并且不超过默认 45 秒；拿取、动作和可选放下事实必须属于同一 `continuity_segment`，不能跨恢复间隙配对。
5. 必需事实的置信度均达到默认 0.45；候选置信度取必需事实中的最低值，避免多条相关性未知的输出被累加成高置信度。

如果配对事实都带有显式 `metadata.source_id`，来源必须完全相同；来源值为空或非字符串的事实不会作为跨事实证据。缺失来源的旧事实按未知来源兼容，但不提供跨相机身份连续性保证。

`object_put_down` 或 `putdown_candidate` 只有在同一人物、同一药品对象并且发生在手部动作之后时，才可作为支持事实。只有拿取事实而没有匹配手部动作时，可输出 `incomplete_medication_sequence` 供人工复核。完整候选仍名为 `suspected_medication`，不表示已经服药或吞咽，也不作医学诊断。

完整推理会在时间窗内查找第一个置信度达到阈值的同人同药品动作，因此较早的低分动作不会挡住稍后的有效动作。低于阈值的可选放下事实不会作为支持证据，也不会拉低候选分数。对于不完整线索，任意已匹配的手部动作事实（即使低于完整事件阈值）会被视为该步骤存在；它不会产生完整事件，但也不会把已有动作事实描述成缺失。

“工具盒”等泛化盒子标签、对象 ID 冲突、不同人物、逆序动作、过期动作和低置信度序列不会产生完整疑似服药候选。

主体如果有显式标签，必须匹配支持的人物标签；显式的设备/物品标签即使携带稳定 ID 也会被拒绝。主体/对象身份仅接受非空字符串或整数 ID；布尔值、分数和容器值不会被字符串化成身份。为兼容旧事实格式，带合法 ID 但缺少主体标签的事实仍可参与推理；该兼容路径不适用于明确的非人物标签。

完整候选去重优先按人物/对象 ID；某实体没有 ID 时，使用其规范化非空标签区分身份。因此重复的同标签事实会合并，而同一人物、同一时间的“药盒 A”与“药盒 B”无 ID 序列仍各自保留。人物序列匹配本身仍要求同一人物 ID；标签回退只用于识别无 ID 药品对象。

### 基于显式人体关键点的动作事实

`KeypointActionExtractor` 只消费上游 detector metadata 里的 `keypoints`，不从原始图像估计关键点。约定 `nose`、`left_wrist`、`right_wrist` 的格式为 `[x_px, y_px, confidence]`，坐标必须与帧和检测框在同一像素坐标系中。

- 关键点置信度至少为 `0.5`；
- wrist 到 nose 的距离不超过人物检测框高度的 `0.2`；
- wrist 到同一人物当前接近的药品框距离不超过 `max(4 px, 人物框高度的 0.1)`；
- 输出 `hand_to_face` 时携带同一 `person track_id` 和药品 `object_id`，confidence 取人物检测、药品检测、关系与关键点置信度的最小值；
- 同一人物/药品组合只在进入阈值时输出一次，并容忍 1 个采样帧丢失关键点或关系；连续缺失超过 1 帧后重新武装。该帧数是可验证的规则默认值，不代表已经用真实视频调优。

关键点坐标、关键点置信度、动作阈值和帧索引拒绝布尔值；几何输入还必须是有限数值。无效关键点或药品框被当作缺少动作证据，不输出 `hand_to_face`；错误配置则在构造时返回 `ValueError`。JSONL→FrameFactExtractor→养老插件回归验证了布尔腕坐标不会把单独的接近线索升级为 `suspected_medication`。这是合成输入上的 fail-closed 证据，不代表真实姿态模型的质量。

无法安全转换为有限浮点值的关键点/框坐标（例如超大 JSON 整数）同样按缺少动作证据处理，不应令整条帧分析任务异常失败。

该几何规则已接入 JSONL fixture 帧管线，测试覆盖 wrist 远离 face、wrist 远离药品、关键点低置信度，以及最终 `suspected_medication` 事件。它证明“有可信关键点时能生成动作事实”的代码路径；项目当前没有真实姿态模型，因此不能声称原始视频能够产生这些关键点或报告动作准确率。

## 工作室物品状态

实现：同一模块中的 `WorkshopStateReasoner`，由 `plugins/workshop/plugin.py` 调用。

- `object_removed` / `left_zone` 产生移出候选；`left_zone` 从关系事实的 subject 读取物品 ID。待归还状态按对象和区域 ID（无 ID 时按区域名）分别维护，其他区域的离开不会覆盖此前状态。
- `object_returned` 可直接产生归还候选；`entered_zone` 只有在时间戳严格晚于物品离开、并重新进入同一 `zone_id`（或同名区域）时才算归还。相同时间戳不建立先后关系，也不因输入顺序生成归还候选。人与物体分开产生的 `putdown_candidate` 不足以证明物品已归还。
- 显式 `object_missing` 可直接产生缺失候选；若要绑定待移出证据，该移出事实必须严格早于缺失事实，且带区域标注时只能绑定同一区域；同一时间戳的事实不会因输入顺序被配对。未标注区域时沿用全局事实语义。
- 超时缺失使用默认 120 秒等待时间和 0.4 最低置信度，并且必须有时间戳不早于阈值的 `scene_observed` 事实作为观察证据。若移出与观察事实都标注区域，区域必须匹配；至少一方未标注区域时，观察事实沿用全场覆盖语义。无关事实不能证明目标物品未出现。
- 缺失候选保留移出和观察事实，要求人工复核；`observation_gap` 会清空待移出状态，后续 `scene_observed` 不会跨连续段充当缺失证据。
- 即使没有显式 `observation_gap`，移出、归还/缺失和 `scene_observed` 的 `continuity_segment` 不一致时也不会跨段配对。
- 如果移出、归还/缺失或观察事实带有显式来源，工作室待处理状态按来源隔离；不同来源的同一对象 ID 不会互相归还、结案或触发超时缺失。
- 多模态质量门控导致的 `observation_gap` 与坏行恢复使用同一连续段边界；质量不足的帧不会生成对象、关系或动作事实。

工作室候选去重键包含区域 ID/规范化区域名；同一对象、同一时刻在不同区域的移出或缺失事件不会合并，同一区域的重复候选仍会去重。

上述对象状态仅在单次 `infer` 调用的事实集合内维护。跨分析任务、跨相机或持续直播的状态保存与时钟同步尚未实现。

## 时间与配置

推理前会按 UTC 对事实排序。带时区的时间统一转换为 UTC；历史无时区时间按 UTC 解释，以避免和带时区时间混排时报错。时长和置信度阈值必须是非布尔实数，且为有限有效范围；字符串、布尔值、NaN/Infinity 和越界数值都会在构造 reasoner 时返回 ValueError。

每个输入 `PrimitiveFact.confidence` 也会在 Pydantic 数值转换前验证：只接受有限、非布尔的 `[0,1]` 实数。布尔分数、数字字符串、NaN/Infinity 和越界值不会进入推理器，因此不能通过类型转换伪造达到阈值的证据。

Detection/Entity 直接构造均要求非空 ID/标签、有限非布尔数值框和 [0, 1] 置信度；FixtureDetector 保留浮点框，非法置信度在适配边界显式失败，不再裁剪。关系提取会拒绝重复实体 ID 与区域 ID，且在拒绝前不会更新时间状态。关系层也把无时区帧时间按 UTC 解释，并拒绝单次提取过程中倒退的时间戳；JSONL 乱序会使分析任务失败，而不会继续写入可能污染位置/区域状态的候选。超大 JSON 整数在 Detection、Entity、Zone、AI_ZONES_JSON 和时序阈值的浮点转换边界统一拒绝为 ValueError；reasoner 时长还需处于 timedelta 可表示范围，PrimitiveFact confidence 在推理入口复核。跨来源时钟校准与乱序缓冲仍未实现。CentroidTracker 通过距离门控后先最大化有效匹配数，再最小化总质心距离；人物标签沿用共享分类器以承受大小写/角色别名变化，其他类别使用大小写不敏感的完整标签匹配。它仍没有外观特征、运动模型或遮挡推理。

检测框与区域的 x+width 和 y+height 也必须有限；例如两个分别有限但相加溢出的值会在 Entity/Detection/Zone 边界拒绝，AI_ZONES_JSON 同样通过 Zone 校验。

帧差 detector 的可变上一帧状态按每次 `FrameFactExtractor.extract` 调用建立独立 provider session；共用服务中的并发 analysis job 不再读写同一个 MotionDetector 历史缓冲。

关系引擎只把连续有效观察之间的状态用于转移判断。人物或物体漏检后，会清除受影响的上一位置、人物—物体接近和区域成员状态；目标重新出现时不会仅凭缺口前后的两个框推断 `motion`、`putdown_candidate` 或 `left_zone`。回归测试覆盖“靠近—漏检—远处重现”和“区域内—漏检—区域外重现”。这能避免把不可见间隔当成已观察到的动作，代价是无法从漏检期间恢复真实发生的转移。对应关系、运动和区域的 cooldown 也随缺失实体/关系对清除，后续完整观察可重新触发候选。坐标分别有限但成对距离或位移运算溢出为非有限值时，不生成距离、near、pickup 或 motion 事实。

关系冷却键以事件类型、实体 ID 和区域 ID 组成元组，不通过分隔符拼接；包含冒号的合法 ID 不会导致不同人物/物体对或不同区域边沿共享冷却状态。

当图像矩阵为降低 CPU 负载而抽样时，MotionDetector 将连通区域框按采样步长映射回原帧像素坐标；原始分辨率/步长变化会清空上一帧状态，避免尺寸相同的抽样矩阵被误当成同一几何空间。配置区和关系距离仍使用原帧像素单位。

## 当前上游缺口

`FrameFactExtractor` 当前把 detector/tracker/关系层观察转为 `PrimitiveFact`；本地规则没有从原始图像识别手部接近面部，也没有发出明确的 `scene_observed` 事实。提取器支持 `zones` 参数，`AnalysisService` 可从可选环境变量 `AI_ZONES_JSON` 加载矩形区域；未配置时保持空列表，因此默认分析任务不会生成 `left_zone` / `entered_zone` 事实。因此：

`AI_ZONES_JSON` 使用 JSON 数组，每项包含唯一 `zone_id`、非空 `label` 和同一帧像素坐标系中的有限 `x`、`y`、正 `width`、`height`。未知字段、重复 ID 或非法尺寸会在服务启动时失败，不会静默忽略区域配置。 直接构造的 Zone 也校验并规范化 ID/标签、拒绝布尔值/字符串坐标；关系引擎在更新时间状态前拒绝重复 zone_id。外部事实中的空 zone_id 按无 ID 处理，回退到规范化区域名匹配。

- Mock/JSONL fixture 可验证完整规则链；
- 现有帧管线可产生 `near` / `pickup_candidate` 等关系事实，但没有经验证的姿态或手部动作模型来生成 `hand_to_face`；
- JSONL 帧管线可以基于 fixture 中标注的 person/medicine 目标产生不完整服药线索；缺少动作事实时不会升级为完整疑似事件；
- 区域状态 reasoner 可处理明确的区域转移事实；`AI_ZONES_JSON` API/service 路径和直接构造 `FrameFactExtractor(zones=[...])` 均有 JSONL/API 测试覆盖，但项目当前没有真实摄像头区域坐标；
- 工作室超时缺失需要上游显式提供 `scene_observed`，否则不会仅凭无关事实报警；
- 事件 precision/recall/F1、误报率、时间窗误差和吞吐仍待授权视频及人工事件标注后评估。

当前 reasoner/plugin 定向测试为 `103 passed`，AI 全量测试为 `363 passed`。新增回归覆盖恢复模式的 JSONL 坏行标记、FrameFactExtractor 的连续段重置、关系时间回归保护、显式来源隔离，以及服药/工作室推理不跨 `observation_gap` 或不一致连续段关联。证据仍是构造事实、Mock 和 JSONL/CPU fixture，不代表真实模型或摄像头准确率。

## 本地验证

定向测试命令（在 `workspace/ai-engine/` 执行）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
python -B -m pytest --basetemp=.codex-pytest-temp-reasoning -p no:cacheprovider tests/test_algorithm_reasoner.py tests/test_plugins.py -q
```

区域配置解析与服务注入定向命令（同样从 `workspace/ai-engine/` 执行）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONPATH='src'
python -B -m pytest --basetemp=.codex-pytest-temp-zone-config -p no:cacheprovider tests/test_zone_config.py tests/test_api.py -k "zone_config or environment_zone_config" -q
```

每次验证应记录当前测试实际计数、源码快照和运行命令，并在验证后清理项目内 basetemp。Fixture/Mock 结果保留 `MOCK_ONLY` 边界；真实指标只在真实授权数据集上报告。
