# AI 算法设计

## 1. 目标与边界

本模块把连续视频转换成可解释的视觉事实和场景事件，服务于智慧养老、工作室安全/物品管理以及后续机器人感知接入。当前实现优先建立稳定的输入、输出和证据契约，再替换为经过数据集验证的检测器、跟踪器和注册识别模型。

当前可以声称的是可运行的规则/CPU 基线与本地服务链路；不能声称真实摄像头准确率、身份认证能力、比赛性能或机器人实机性能。模型指标必须等授权数据、标注规范和评估脚本确定后再填写。

`workspace/source-snapshots/Makerverse/` 与 `workspace/source-snapshots/livestream-rs/` 是已固定提交的直播业务/媒体服务集成参考。当前静态审计未发现其中提供本项目所需的目标检测或人体姿态模型；本地 AI 算法实现与修改来自 `workspace/ai-engine/` 的代码审计及合成 fixture 回归，不是从这两个快照移植的识别模型。快照只支持媒体和 API 集成判断，不能作为视觉算法或识别效果证据。

### 1.1 竞赛定位与隐私边界

依据项目内 `AIC_ALGORITHM_COMPETITION_ALIGNMENT.md`，当前作品优先按 `AI+场景创新` 组织：视觉事实层服务养老辅助和工作室物品管理，机器人作为待验证的感知载体。`AI+硬件创新` 需要另行补齐硬件参数、算法运行效率、稳定性/安全性和现场演示证据；`算法模型创新` 需要真实模型、基线和指标，不能由当前 CPU/fixture 规则测试替代。四份用户提供的算法/作品 DOCX 已按可借鉴方法、证据质量和迁移边界完成审计，见 `REFERENCE_ALGORITHM_AUDIT.md`；其内主张和指标不自动视为本项目结果。

隐私优先的目标是让相机或边缘节点尽早完成骨骼化，只向上层输出关键点、轨迹和事件所需的最小字段。当前引擎只消费显式 fixture keypoints，尚未实现相机侧骨骼化、真实姿态模型或隐私模式开关；帧预览 API 现在会递归将常见 `image`、`gray`、`pixels`、`depth_map`、`rgb/bgr` 等矩阵替换为编码与尺寸摘要，但这只是传输边界的脱敏，不等同于相机源头处理。非图像语义字段（例如 fixture 中的关键点和标签）仍会保留。卡通化展示属于演示脱敏，也不等同于源头隐私保护。步态、身高比例和骨骼形态只列为后续身份研究方向，不作为当前身份认证能力。药品分区、固定位置和时间证据可以降低身份依赖，但缺少可信人物关联时仍只能输出不完整/待复核线索。

同一脱敏边界现在贯穿事实和证据链：`FrameFactExtractor` 在把 detector metadata 变成 `PrimitiveFact` 前递归替换像素、深度、热成像和 raw-frame 数组；`/api/v1/vision/preview` 对观察 metadata 使用同一规则；任务创建 metadata、SQLite job metadata 和事件 payload 写入前也会脱敏。关键点、标签、bbox、来源和形状摘要保留，原始像素值不进入事件证据。这是软件传输/存储边界的验证，不代表相机源头已经删除原始帧。

可选多模态通道使用 `metadata.channel_quality` 作为软件契约：每个通道提供布尔 `available`、有限 `[0,1]` `score`，可选 `reason`；`quality_required_channels` 可声明必须满足的通道。至少一个通道可用时继续推理并在事实 metadata 写入 `quality_gate.degraded` 摘要；没有可用通道或必需通道失效时输出 `observation_gap`、重置 detector/tracker/关系/关键点状态并停止该帧推理。字段错误直接 fail closed。当前只验证元数据和 fixture 行为，时间同步、真实音频/热成像/事件相机和通道消融仍待授权数据。

## 2. 分层管线

```text
VideoSourceAdapter
  -> FramePacket(timestamp/source_id/frame_index)
  -> DetectorProvider
  -> Tracker
  -> RelationExtractor
  -> PrimitiveFact
  -> ScenePlugin
  -> UnifiedEvent
  -> EvidenceResolver
  -> SQLite + REST + Frontend
```

各层只通过稳定的数据对象通信。场景插件不直接读取摄像头、模型文件或 Makerverse 内部对象；替换输入协议或 detector 时，不需要重写场景规则。

## 3. 输入与时间

`FramePacket` 至少保留 `source_id`、`timestamp`、`frame_index` 和可选的 `fps/time_base`。Mock、JSONL 和 OpenCV provider 均使用同一时间传播逻辑。抽帧策略由 `interval_ms`、`max_frames` 和 provider 能力共同决定；`interval_ms` 必须是可表示为 timedelta 的非布尔非负整数，`max_frames` 必须是非布尔非负整数或 `None`（0 表示不读取帧）；不以处理完成时间替代媒体时间。JSONL 恢复模式若跳过坏记录，会在下一帧标记 `discontinuity_before`、原因和行号，供事实管线建立新的连续观察段。

网络流、RTSP、HLS、HTTP-FLV 和 livestream-rs 的真实解码属于可替换输入适配器。当前环境没有 FFmpeg 和真实部署，因此网络输入只完成配置检查和接口边界，不会伪造帧。OpenCV provider 会校验 FPS/PTS：不可用 FPS 回退到 25 fps，异常 PTS 回退到 read_index/fps；若时间戳仍超出 datetime 可表示范围，会显式失败。模拟元数据测试验证 fallback，现有本地 AVI fixture 验证正常读取，不代表覆盖真实异常码流。

## 4. 检测与跟踪

当前 detector registry 包含：

- `motion_cpu`：基于帧差/四邻域连通区域的可解释 CPU baseline，只检测变化区域，不输出人/药盒/工具语义类别；输入灰度值必须为有限非布尔数值且在 `[0,255]`，浮点强度会保留，不会截断或裁剪；非法样本会清空历史并跳过比较；大图抽样后的检测框会映射回原始帧像素坐标，原帧尺寸/抽样步长变化时重置比较历史；每次 `FrameFactExtractor` 分析提取都会创建独立 provider session，避免并发 job 共享帧差历史；首帧不产生检测，状态在来源变化或每个新分析任务的 `frame_index=0` 时清空；区域面积分数是启发式字段，不是校准概率；
- `fixture`：用于确定性测试的检测输出；
- `onnx`：只有在输入/输出 adapter 经过验证时才允许选择，否则保持 unavailable；
- 可扩展 provider：真实模型可在不改变下游 schema 的情况下接入。

Tracker 输出 `track_id`、类别、置信度和中心/区域信息。当前 CentroidTracker 先按类别与最大质心距离门控（人物标签走共享人物分类，其他类别按大小写规范化后的完整标签匹配），再求最大匹配数下的最小总距离分配；这避免逐边贪心导致的无谓 ID 断裂，但没有运动模型、外观特征或遮挡推理，交叉目标和快速移动仍可能造成 ID switch。重复框的观察归一化会逐个分配 track。遮挡、多人、多物体和跨摄像头 ID 的真实性能需要专项数据集验证，当前测试只证明本地确定性行为。

可选的 `KeypointActionExtractor` 消费 Detector metadata 中的明确关键点坐标；它不从像素估计人体姿态。人物检测框高度用于归一化 face-to-wrist 距离，且同一手腕必须同时接近药品框，才输出 `hand_to_face`；对同一人物/药品组合只在动作进入阈值时输出一次事实，容忍 1 个采样帧的关键点丢失，超过间隔后才重新武装。提取器按 `source_id` 隔离动作 episode；一次调用混入多个来源会拒绝，避免同一人物/对象 ID 在换源后沿用旧去抖状态。

`FrameFactExtractor` 将 `source_id` 写入对象、关系、动作和观察间隙事实的 metadata；如果调用方把带来源标记的关系事实与另一来源的 keypoint observations 混合，动作提取器会拒绝该批次。没有来源 metadata 的旧构造事实保留兼容路径，但不应被当作跨来源身份证据。

动作提取还要求一次调用中的人物/对象 observations 属于同一 UTC 帧时间，并只接受同一 UTC 时间的关系事实；旧帧的 `near` 或 `pickup_candidate` 不会被当前关键点几何借用。无时区时间按 UTC 解释，等价时区表示可以匹配。

时序 reasoner 也在证据配对处执行来源隔离：显式 `source_id` 不同的拿取/手部事实、移出/归还事实或移出/场景观察事实不会拼成同一候选；工作室待处理状态的键包含来源签名，因此同一对象 ID 在不同来源上不会互相覆盖。旧事实缺少 provenance 时按未知来源兼容，但不会由此声称跨摄像头身份连续。

关键点坐标、关键点置信度及动作阈值必须是有限的非布尔数值；药品框中的布尔值也作为无效几何处理。无法安全转换为有限浮点值的超大数值也会被忽略为缺少动作证据，不会令整条帧分析任务异常失败。无效关键点/框不会因为 Python 将 `true/false` 当作 `1/0` 而生成动作。配置类型错误则在构造 extractor 时以 `ValueError` 拒绝。JSONL 回归覆盖布尔腕坐标无法生成 `hand_to_face` 或完整疑似服药事件。

## 5. 关系事实

关系层将检测结果组合成“人—物—区域—时间”事实，例如人物接近药盒、物体进入工作台区域或主体离开观察区。事实包含来源、时间窗、置信度、位置和参与实体，供插件解释而不是直接作为高层结论。冷却状态使用结构化事件/实体键，实体 ID 中即使包含冒号等分隔符也不会把不同关系合并。

`PrimitiveFact.confidence` 在 Pydantic 转换前校验为有限、非布尔、范围 `[0,1]` 的实数；布尔值和数字字符串不会被转换成高置信度事实，非有限或越界分数也会被拒绝。

关系层与时序 reasoner 共用 `entity_labels.py` 中的人物标签判断，支持“家属”“工作人员”“老人”及大小写不敏感的英文 `person/worker/staff`；这避免关系层把人物当作普通物体后丢失接近事实。

FixtureDetector 保留有限浮点框坐标，并把原始置信度交给 Detection 验证；显式 objects 列表中的 malformed 行和非法分数会带记录索引失败，不会把坏记录当作空检测，也不会把 NaN 或越界分数裁剪成可信分数。事实提取使用去抖、冷却和最小持续时间，避免同一帧或相邻帧重复生成事件。`Entity` 要求非空且规范化的 ID/标签、有限数值框和有效置信度；`RelationEngine` 在更新时间状态前拒绝重复实体或区域 ID。它还把无时区时间按 UTC 处理，并在单次来源处理期间拒绝时间倒退的帧，避免旧帧静默改写位置/区域状态；非法距离/cooldown 阈值、非正区域大小和无效几何会被拒绝；数值配置要求非布尔实数，整数计数参数拒绝布尔值与非整数输入；超大 JSON 整数在 float/timedelta 转换边界规范化为 ValueError，时序器时长还必须落在 timedelta 可表示范围内。reasoner 在推理入口复核 PrimitiveFact.confidence，避免对象创建后的修改绕过分数校验。跨源时钟校准仍需真实部署数据补充。

检测框与区域还要求计算出的右/下边界（x+width、y+height）保持有限；分量分别有限但相加溢出的框/区域会被拒绝，避免产生无限范围或不可信中心坐标。环境区和直接构造的区域共用这一约束。

关系层只在相邻的有效观察之间保留运动、人物—物体接近和区域成员状态。实体或关系对象在某帧未检出时，关联的连续状态及其 near/pickup/putdown、motion、zone 冷却键会清除；重新出现后的完整观察可以开启新的候选，不会把跨过检测缺口的位移补成 `motion`、`putdown_candidate` 或 `left_zone`。成对距离或位移运算若得到非有限结果，对应关系/motion 事实会被丢弃，不把 Infinity 写入事件证据。这减少漏检与数值溢出造成的虚假转移，但可能漏掉完全发生在不可见间隔内的真实动作。

JSONL 恢复模式的坏记录属于更强的观察间隙：`FrameFactExtractor` 会输出 `observation_gap`，创建新的 detector session，重置 tracker、关系和关键点动作状态，并把间隙后的事实放入新的 `continuity_segment`。服药序列的拿取与手部动作、工作室移出与后续观察都要求属于同一连续段；因此恢复后的首帧不会借用坏记录前的轨迹、冷却或待处理移出状态。未知间隔内发生的真实动作会被保守地视为缺少证据。

## 6. 注册特征匹配

当前注册流程保存对象/人员名称和可选 embedding。CPU baseline embedding 由 4×4 网格均值加 16-bin 强度直方图组成，并进行 L2 归一化；灰度矩阵只接受有限、非布尔且位于 `[0,255]` 的数值，不对越界强度进行裁剪。向量归一化拒绝布尔值、数字字符串、非有限值、全零向量和维度错误；范数计算可处理大有限数值。匹配阈值也必须是 `[0,1]` 内的有限非布尔实数。API 请求校验会在类型转换前拦截布尔值和数字字符串；空/全零登记向量返回明确的 `400`，不保存记录。它用于验证“参考特征可以进入事实链”的软件契约，不是人脸识别、医疗判断或安全身份认证。

`PrimitiveFact.metadata.registry_matches` 保存最多前五个候选及 `accepted` 标记；前端和文档必须显示 heuristic 状态。生产替换方案包括经授权的图像质量检查、专用 embedding 模型、隐私保护存储、拒识阈值和人工复核。

## 7. 事件生成

场景插件把事实序列映射为统一事件：

- `event_id`、`event_type`、`title`、`description`；
- `source_id`、`started_at`、`ended_at`、`location`；
- `confidence`、`severity`、`review_status`；
- `facts`、`evidence`、`metadata`；
- 插件 ID 和版本，用于解释规则来源。

养老插件使用“疑似服药”语义，不能改写为医疗确认；工作室插件使用物品在工作区出现/离开/缺失等状态。事件先进入 `pending`，由人工确认或驳回，不把启发式结果变成绝对事实。

养老和工作室插件调用独立的时序推理器；规则、默认阈值和输入事实要求见 `TEMPORAL_EVENT_REASONING.md`。推理器返回候选事件及其原始事实，插件据此生成统一事件，避免只测试一个未进入主链路的算法模块。

## 8. 时序事件推理

`MedicationSequenceReasoner` 要求药品对象、人物和时序动作互相匹配，置信度取必要事实中的最低值。药品目标分类排除药柜、药架、药房等储存/地点标签，也排除药品说明书、用药记录、药品清单和处方单等非药品本体标签；只有上游显式类别为 medicine/medication/drug 时才允许覆盖这些显示标签。它会在时间窗内继续查找达到阈值的匹配手部动作；早到但置信度不足的动作不会掩盖后续有效动作。低置信度的可选放下事实不会拖低完整候选分数。主体有显式标签时必须属于支持的人物类别；明确标为设备或其他非人物的主体，即使带 ID 也不能进入服药序列。ID 只接受非空字符串或整数（不含布尔值）；分数、列表等值不能作为身份。无标签但带稳定 ID 的旧事实仍按兼容契约处理。它可以输出待复核的完整疑似序列，也可以将只有拿取事实的序列标为不完整线索。通用“盒子”标签、人物 ID 不同、药品对象 ID 冲突或超出时间窗时，不输出完整疑似事件。

候选事件去重优先使用有效实体 ID；没有可用 ID 时回退到规范化标签。动作事实关联更严格：显式但格式错误的对象 ID 不能用标签回退来配对。因而同一无 ID 药品序列的重复证据会合并，不同药品标签的候选不会因共享空 ID 而互相吞并。

`WorkshopStateReasoner` 将移出、归还和缺失作为状态转移。`entered_zone` 只有在时间戳严格晚于物品离开、且回到同一分区时才代表归还；相同时间戳不建立先后关系，也不因输入顺序生成归还候选。显式 `object_returned`、`object_missing` 可独立产生候选；若与待移出状态配对，移出事实必须严格更早。人与物体拉开距离产生的 `putdown_candidate` 不能证明归还。缺失超时必须由明确的 `scene_observed` 事实证明已经过了观察时间；带区域标注的 `object_missing` 只能配对同一区域的待移出证据；未标注区域的显式缺失仍沿用全局语义。任意其他事实不能充当缺失证据。两个推理器都按 UTC 排序，兼容把旧的无时区事实按 UTC 解释，并拒绝无效阈值配置。工作室超时缺失只使用与移出区域匹配的带区域观察；至少一方未标注区域时保留显式全场观察语义。

这些规则已接入对应场景插件，并通过 Mock/fixture 单元测试验证。`FrameFactExtractor` 可从显式 pose keypoints 生成 `hand_to_face`，但内置 `motion_cpu` 不提供关键点，项目尚无真实姿态模型；缺少关键点时仍只产出不完整线索。`AnalysisService` 可通过 `AI_ZONES_JSON` 接收矩形区域，`create_app()` 启动时严格解析并注入服务；未设置或设为 `[]` 时不生成区域事实。非法 JSON、未知字段、重复 `zone_id`、非有限坐标和非正宽高会显式报错。直接构造的 Zone 也要求非空 ID/标签、有限数值几何和正尺寸，关系引擎拒绝重复 zone_id；空 zone_id 事实按未标注 ID 处理并回退到区域名，避免把不同位置合并。坐标必须使用 detector bbox 对应的帧像素坐标系，但当前未提供真实相机的区域校准；`scene_observed` 事实源仍未实现。WorkshopStateReasoner 按对象 ID 与 zone_id/区域名分别保留待归还状态；另一个区域的离开不会覆盖原区域，进入事件只匹配同一区域，事件去重也保留区域范围。因此真实视频完整服药序列、实景区域转移和缺失超时仍需补齐上游模型/配置；本地通过不代表真实视频识别准确率。

即使调用方没有附带 `observation_gap`，`WorkshopStateReasoner` 也会要求移出、归还/缺失和 `scene_observed` 的 `continuity_segment` 一致；不一致时只保留显式事实本身，不跨段结案。这样可以防止聚合器、省略 gap 标记或跨任务拼接事实时重新引入状态串联。

## 9. 任务与停止语义

分析任务以 `job_id` 追踪状态。状态至少包括 `queued`、`running`、`completed`、`failed` 和 `stopped`。每个 job 持有独立的 `CancellationToken`，并传给 `FrameFactExtractor` 和帧 provider；提取器在每帧处理前检查取消，内置 provider 在帧循环中也会检查。取消响应在帧边界生效，取消异常会归类为 `stopped`，不运行插件或落库部分事件。事件批次和 job 的 `completed` 状态在一个 SQLite 事务中提交，并与 stop 请求互斥：若 stop 先取得终结锁，事件批次不会写入；若完成事务已先取得锁，job 会完成，随后到达的 stop 返回已完成状态。完成的 job 重复执行会直接返回原结果，不重复生成事件。已经进入同步媒体库单次 read 的调用无法被强制中断，需等 read 返回。

## 10. 伪代码

```text
for frame in source.frames(config):
    if stop_requested: return STOPPED
    observations = detector.detect(frame)
    tracks = tracker.update(observations, frame.timestamp)
    facts = relations.extract(tracks, frame)
    for plugin in enabled_plugins:
        events += plugin.evaluate(facts)
    evidence.attach_time_window(events, frame.timestamp)
persist(events)
return COMPLETED
```

## 11. 评估接口

真实评估至少应报告检测 precision/recall、跟踪 IDF1/HOTA、事件级 precision/recall/F1、时间窗误差、端到端延迟、CPU/GPU 资源和停止响应时间。当前仓库没有授权数据集和真实评估结果，所有数值栏位必须保持“待测”。实验方案见 `EXPERIMENT_PLAN.md`。
