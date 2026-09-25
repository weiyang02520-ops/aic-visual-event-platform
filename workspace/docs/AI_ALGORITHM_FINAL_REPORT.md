# AI 算法最终报告

最后更新：2026-09-25（TASK-0010 final audit）

## 1. 范围与结论

本报告只覆盖本团队负责的 AI 软件链路。AI 与 frontend 属于整体项目责任范围；本任务冻结的是 AI 对 frontend 的事实、事件、状态和隐私边界。机器人导航、操控、抓取、相机标定、硬件安全和现场部署属于其他团队或后续集成，不在本报告中虚构完成。

当前结果是一套可重复运行的规则/CPU/可选模型适配基线。它有完整的输入、来源、时间、连续段、身份、置信度、隐私和人工复核边界，但没有项目 mAP/F1/HOTA、医疗结论、跨摄像头 ReID 或机器人成功率。

## 2. 最终架构

```text
Camera / Video / Skeleton Input
  -> Privacy + Quality Boundary
  -> Pose Provider (person + COCO17)
  -> Semantic Object Provider (non-person labels)
  -> Combined Perception
  -> Centroid/Hungarian Tracking
  -> Spatial Relations
  -> Generic Action Primitives
  -> VisualMemory
  -> TemporalVisualMemory
  -> Scene / Medication Reasoning
  -> Reviewable UnifiedEvent / Frontend Contract
```

当前实现入口包括 Mock、JSONL fixture、可选 OpenCV 本地视频和可选 Ultralytics-compatible provider。网络流只完成来源/适配边界；没有把“已配置”写成“已连接”。

## 3. 模块、契约和失败边界

| 模块 | 输入 | 输出/状态 | 失败或降级边界 |
|---|---|---|---|
| `frame_pipeline.py` | source、timestamp、frame index、payload | `Frame`、`observation_gap` | 时间倒退、坏行、取消和不可表示时间 fail closed；gap 开新 continuity segment |
| `privacy.py` | 任意 metadata/payload | 编码和 shape 摘要 | image/gray/rgb/bgr/depth/thermal/raw-frame 等数组不进入事实、API、SQLite |
| `quality.py` | `channel_quality`、required channels | allow/degraded/block 摘要 | 无可用或必需通道失败时发 gap、重置跨帧状态 |
| `skeleton.py` | named/COCO17 points | `SkeletonObservation` | 点坐标、confidence、schema/version、source/time/track/continuity 严格校验 |
| `UltralyticsProvider` | frame image、pose model | person `Detection` + COCO17 | optional dependency/model 缺失为 unavailable；坏结果拒绝 |
| `UltralyticsObjectProvider` | frame image、object model | 非人物 label/bbox/class/confidence | person 类别过滤；无效 class/bbox/confidence fail closed；不伪造 skeleton |
| `CombinedUltralyticsProvider` | pose/object detections | 确定性 person-first detections | object component 不可用不禁用 pose；人物重复不保留，同标签非人物框不合并 |
| `CentroidTracker` | detections | track IDs、age、missed | 类别/距离门控后全局最小距离分配；无运动模型/ReID |
| `RelationEngine` | tracked entities、zones | near/pickup/putdown/motion/zone facts | 非有限几何、重复 ID、漏检和跨 gap 不生成转移 |
| `GenericActionPrimitiveExtractor` | 当前帧 skeleton/object observations | `hand_near_object`、generic `hand_to_face` | 只消费几何和 provenance；不识别药品、不推断抓取/吞咽 |
| `MedicationActionAdapter` | generic hand/face + medication relation | 兼容的带对象 hand-to-face | 同帧、同源、同连续段和同身份；保留旧 `KeypointActionExtractor` 名称 |
| `VisualMemory` | object_detected/zone facts | last-known bbox/zone/location | identity=`source+continuity+track/entity`；label 不合并身份 |
| `TemporalVisualMemory` | PrimitiveFacts | bounded recent/last/timeline records | 正整数容量；source/continuity/identity 隔离；metadata sanitizer；无 REST 端点 |
| `MedicationSequenceReasoner` | interaction + hand facts | review-only suspected/incomplete cues | 同人、同物、同源、同段、时间窗；不产生医学结论 |
| `MedicationPlanEvaluator` | plan + medication evidence | match/early/late/wrong/unresolved cues | explicit timezone/time window；重复 episode 去重；跨源/gap/歧义 fail closed |
| `WorkshopStateReasoner` | removal/zone/observation facts | removed/returned/missing candidates | 同源、同段、同区和严格时间先后；缺失要求观察证据 |
| plugins/storage/API | facts/events/evidence | `UnifiedEvent`、review state、SQLite/REST | evidence URI 不伪造；写入前脱敏；review 仅人工复核 |

## 4. 算法和公式

### 4.1 框中心和点到框距离

对框 `(x, y, w, h)`，中心为 `c=(x+w/2, y+h/2)`。Tracker 使用中心欧氏距离
`d(c1,c2)=sqrt((x1-x2)^2+(y1-y2)^2)`，先按类别与最大距离门控，再在有效匹配数最大的解中最小化总距离。

点到框距离使用轴向外距离：框内对应轴距离为 0，框外取到最近边的距离，最后为 `sqrt(dx^2+dy^2)`。`hand_near_object` 使用腕点到非人物 bbox 的距离与 `max(4 px, person_height*0.1)` 比较。

### 4.2 手部靠脸

`hand_to_face` 的几何条件是腕点与 nose 的欧氏距离不超过 `person_bbox_height*0.2`，且关键点 confidence 达到默认阈值。generic extractor 可以只输出没有 object context 的动作；药品适配器只在同帧、同源、同段 object geometry 支持时补充药品对象。

### 4.3 区域包含

矩形区域用 bbox 与区域的几何包含/重叠规则产生 `object_in_zone`、`entered_zone` 和 `left_zone` 事实。区域 ID、标签、边界和 source/continuity 都保留；关系状态遇到漏检时清除，避免跨不可见间隔臆测 motion 或归还。

### 4.4 时间、去抖和连续段

事实按 timezone-aware UTC timestamp 排序。动作 episode 以 `(source, continuity, subject/object identity)` 为范围；同 episode 的重复动作在 debounce window 内不重复产生 review cue。`observation_gap` 是硬边界，前后相同 numeric track ID 不被视为同一连续证据。

### 4.5 置信度

组合事实的置信度采用必需证据中的保守最小值，不把相关性未知的分数相加。输入 confidence 先拒绝 Boolean、字符串、NaN、Infinity 和越界值。计划 review cue 保留证据置信度，但不把它变成医学概率。

### 4.6 有界视觉记忆

`VisualMemory` 保存每个 source/continuity/entity 的最后 bbox、zone、location、时间和 provenance。`TemporalVisualMemory` 只保留允许 fact types，按 `max_records` 和 `max_records_per_identity` 淘汰最旧记录；label-only 查询返回多个候选，不做 ReID。

### 4.7 用药计划时间窗

计划条目使用带显式时区的 `scheduled_at` 或 timezone-scoped local clock，并定义 early/late tolerance。令 `delta = observed_utc - scheduled_utc`：

- `delta < -early_tolerance` → `early_candidate`；
- `delta > late_tolerance` → `late_candidate`；
- 其余 → `plan_match_candidate`。

药品 identity/label 不兼容时只给 `wrong_item_candidate`；证据不足、平行同标签对象、跨源或跨段时给 `unresolved_candidate`。note/dose 只作为用户配置元数据回显，不由视觉推断。

## 5. 选择这些算法的原因

- **Centroid/Hungarian vs ByteTrack/Kalman**：当前方法依赖少、可解释、易在 CPU/fixture 验证，并且全局分配比逐边贪心更稳定；ByteTrack/Kalman 需要模型/数据门控和真实 ID 指标，保留为未来对照，不宣称当前性能优胜。
- **规则时序 vs GNN/2S-AGCN**：当前规则能显式表达来源、时间窗、连续段和人工复核边界，适合没有授权数据的阶段；学习型时序模型需要标注动作、训练/验证切分和回放指标，本阶段不实现。
- **COCO17 pose vs richer keypoint models**：COCO17 是稳定、通用且已有 provider/schema 合同；增加更丰富关节前必须扩展版本化 schema 和证据测试。
- **组合 provider vs 单一模型**：pose 与语义 object 可独立配置和降级，保留已验证 pose path；单一模型会把 object 模型缺失和 pose 缺失耦合起来。
- **source-local identity vs ReID**：显式 source/continuity/track 适合安全 fail-closed；跨摄像头 ReID 需要数据、隐私授权和误匹配评估，因此不在当前实现。

## 6. 竞赛材料映射

| 竞赛/参考概念 | 当前真实状态 |
|---|---|
| skeleton privacy | 软件 skeleton-only 上层契约和 metadata 脱敏已实现；物理 edge/camera 源头输出未验证 |
| YOLO object recognition | Ultralytics-compatible semantic object adapter/composition 已实现；自定义 medicine weights/accuracy 未提供 |
| object management | generic relations + VisualMemory + TemporalVisualMemory 已实现，保留 source/continuity identity |
| medication monitoring | MedicationSequenceReasoner + MedicationPlanEvaluator 输出 review-only cues，不代表服药/吞咽 |
| ByteTrack/Kalman | 未来可对照方案，当前 tracker 是 Centroid/Hungarian |
| 2S-AGCN/fall/violence | extension boundary，当前没有 trained runtime |
| cartoon rendering | frontend presentation responsibility，AI 不输出视觉成品 |
| gait recognition | future research；不提供 identity claim |
| robot/VLA/grasp/navigation | out of current AI scope，无执行证据 |

## 7. 证据表

| 证据 | 等级 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| 官方 Ultralytics pose smoke / `REAL_RUNTIME_SMOKE` | REAL_RUNTIME_SMOKE | adapter 能在记录的环境中产生 person/COCO17 输出 | 场景准确率、药品识别、摄像头验收 |
| local-video → pose → fact smoke | REAL_RUNTIME_SMOKE | BGR 本地帧通过 provider/tracker/fact path | 真实部署吞吐、现场稳定性 |
| skeleton-only/privacy/quality tests | LOCAL_ONLY / software contract | 上层不需要 raw pixels，质量失败会开 gap | 相机源头物理删除 |
| provider/object/action/memory/reasoner tests | LOCAL_ONLY / fixture/CPU | schema、边界、source/time/continuity 和 fail-closed 行为 | mAP/F1/HOTA/IDF1、医学结论 |
| final acceptance matrix | LOCAL_ONLY / software contract | 16 项 AI freeze 回归矩阵 | 真实模型或硬件结果 |
| full source + curated VERIFY | LOCAL_ONLY | 代码和提交包可重复验证、无污染 | 真实数据集指标 |

## 8. 限制与后续工作

- 没有授权数据集和事件标注，因此没有检测/跟踪/事件精度、延迟、IDF1/HOTA 或模型对照数字。
- 没有 custom medicine detector weights；标签兼容是 schema/规则能力，不是药品识别准确率。
- 没有跨摄像头身份、gait/ReID、2S-AGCN、音频融合或真实 edge skeleton-only 输出。
- 没有机器人执行、导航、抓取、通信安全或硬件现场证据。
- 当前 quality gate 是软件元数据契约；真实音频/热成像/事件相机的同步和消融待外部资料。
- frontend 只能依赖 `FRONTEND_AI_INTEGRATION_CONTRACT.md` 中的字段和 review 语义，不应把 candidate 当作 certainty。
