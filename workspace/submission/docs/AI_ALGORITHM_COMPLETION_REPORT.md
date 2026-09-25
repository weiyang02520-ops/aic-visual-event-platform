# AIC 机器人智能识别项目
# AI 算法工作完成总览

**报告日期：** 2026-09-24  
**工作目录：** 项目资料根目录  
**本报告范围：** AI 算法源码、算法测试、算法文档、提交暂存包中的对应 AI 文件和 `agent-state`。  
**明确不纳入本报告的工作：** 机器人控制、硬件接线、相机标定、现场视频验收、真实传感器部署和前端视觉改造。

---

## 1. 总结结论

当前已经完成的是一套**可以在本地运行、可重复测试、边界明确的 AI 软件基线**，主要覆盖：

1. 帧输入、时间戳、来源和中断控制；
2. CPU 帧差检测、fixture 检测和基础跟踪；
3. 人物—物体—区域关系事实；
4. 关键点驱动的手部靠脸动作规则；
5. 养老辅助服药序列和工作室物品状态推理；
6. 隐私元数据脱敏和事件证据存储边界；
7. 可选多模态通道的软件质量门控和降级；
8. REST API、SQLite、插件、任务取消和提交包验收；
9. AIC 竞赛规则、参考作品和当前 AI 证据边界的整理。

当前最新验收结果：

| 项目 | 结果 |
|---|---|
| 源码全量测试 | **414 passed** |
| `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` | **VERIFY_OK** |
| 提交暂存包 AI 测试 | **414 passed** |
| 非阻塞警告 | 616 条 Python 3.14 / FastAPI / Starlette 弃用提示 |
| AI 源码/测试相关文件同步 | 45 个相关文件哈希一致 |
| 文档比对 | 47 个文档参与比对，唯一差异是已知的 `PHASE0_AUDIT.md` |
| 证据等级 | `MOCK_OR_LOCAL`、fixture、CPU baseline、本地 API |

这些结果证明软件契约和规则链可以运行，**不等于真实摄像头、真实姿态模型、真实多模态传感器或机器人实机已经通过验收**。

---

## 2. 当前 AI 软件架构

```text
Frame Source
  ├─ Mock
  ├─ JSONL fixture
  └─ optional OpenCV local video
        ↓
Frame(timestamp / source_id / frame_index / metadata)
        ↓
Detector Provider
  ├─ motion_cpu
  ├─ fixture
  └─ ONNX placeholder with explicit fallback
        ↓
CentroidTracker
        ↓
Observation normalization
        ↓
RelationEngine
  ├─ person-object distance
  ├─ near / pickup / putdown
  ├─ zone entry / exit
  └─ motion and continuity state
        ↓
FrameFactExtractor
  ├─ privacy metadata sanitization
  ├─ source / timestamp / continuity propagation
  ├─ quality gate
  └─ explicit keypoint action extraction
        ↓
PrimitiveFact
        ↓
Scene Plugins
  ├─ elderly_care
  └─ workshop
        ↓
Temporal Reasoners
        ↓
UnifiedEvent + EvidenceRef
        ↓
SQLite + REST API + review status
```

核心原则是把**检测、跟踪、关系事实、时序推理、事件和证据**分层。真实模型将来可以替换 detector 或 pose provider，但下游事件规则不需要跟着重写。

---

## 3. 已完成的输入和帧管线

### 3.1 输入来源

已实现并测试：

- `MockFrameProvider`：生成确定性的本地测试帧；
- `JsonlFrameProvider`：读取带时间戳、payload 和 metadata 的 JSONL/NDJSON fixture；
- `OpenCVFrameProvider`：可选读取本地 AVI、MP4、MOV、MKV、WEBM、M4V；
- 未配置的 RTMP、RTSP 等来源会返回受控错误，不伪造帧。

JSONL 是测试和集成 fixture，不被当作真实摄像头或 FFmpeg 解码结果。

### 3.2 帧参数和时间戳校验

以下输入已经做了 fail-closed 处理：

- `interval_ms` 必须是非布尔、非负整数，并且能转换成有效 `timedelta`；
- `max_frames` 必须是非布尔、非负整数或 `None`；
- 时间戳统一按 UTC 比较；
- 无时区时间按 UTC 兼容处理；
- JSONL 时间倒退会失败，不继续污染关系状态；
- OpenCV 非法 FPS 使用有界 fallback；
- OpenCV 非法 PTS 使用读取序号和 FPS 估计；
- 无法表示的时间范围会返回 `FramePipelineError`。

### 3.3 中断和坏帧恢复

- 每个分析任务有独立 `CancellationToken`；
- 帧 provider 在帧边界检查取消；
- 停止任务后不继续运行插件，也不落库部分事件；
- JSONL 坏行恢复时产生 `observation_gap`；
- gap 后建立新的 `continuity_segment`；
- detector、tracker、relation 和 keypoint 状态在间隙后重置；
- 时序推理不允许跨 gap 拼接证据。

---

## 4. 已完成的检测和跟踪基线

### 4.1 `motion_cpu` 帧差检测

这是可解释的 CPU baseline，不是训练好的目标检测模型。已完成：

- 读取灰度矩阵并计算变化区域；
- 四邻域连通区域提取；
- 灰度值必须是有限、非布尔、位于 `[0,255]` 的数值；
- 保留浮点灰度，不做错误截断；
- 非法像素会清空历史并跳过比较；
- 首帧不产生运动事实；
- 来源切换或分析任务切换时清空历史；
- 抽样图像的检测框映射回原始帧像素坐标；
- 原始尺寸或抽样步长变化时清空比较历史；
- 每个 `FrameFactExtractor` job 使用独立 detector session。

输出的面积分数是启发式分数，不是经过校准的概率。

### 4.2 `fixture` 检测 provider

fixture provider 用于把预计算对象接入完整规则链，已经完成：

- 标签非空校验；
- bbox 四个坐标校验；
- 宽高必须为正；
- 坐标和右/下边界必须有限；
- confidence 必须是有限 `[0,1]` 的非布尔数值；
- malformed 对象行带行号失败；
- 不把非法对象行静默当成空检测；
- 显式 keypoints 和 embedding metadata 可以进入后续契约测试。

### 4.3 `CentroidTracker`

当前跟踪器已经从简单逐边匹配改为：

1. 按类别和最大质心距离做门控；
2. 在有效匹配数最大时，再最小化总距离；
3. 使用共享人物标签分类，支持 `家属`、`工作人员`、`老人` 和大小写不敏感的英文人物别名；
4. 其他类别使用大小写规范化后的完整标签匹配；
5. 重复 bbox 逐个分配 track，避免字典覆盖导致多个观察共享一个 track ID；
6. 目标漏检后清除相关连续状态，避免跨缺口制造运动或区域事件。

当前没有运动模型、外观特征、ReID、遮挡恢复或跨摄像头身份识别。交叉、快速移动和多人遮挡的真实 ID switch 尚未测量。

---

## 5. 已完成的隐私和输入契约

### 5.1 共享像素元数据脱敏

新增共享 `visual_event_ai/privacy.py`，递归识别并替换以下类型的字段：

- `image`、`image_data`、`raw_image`；
- `gray`、`grayscale`；
- `pixels`、`raw_pixels`、`pixel_data`、`pixel_values`；
- `rgb`、`bgr`；
- `depth`、`depth_map`；
- `thermal`、`thermal_map`；
- `infrared`；
- `frame_data`、`raw_frame`。

原始数组被替换为编码和 shape 摘要，非像素字段保留。已覆盖：

- `/api/v1/sources/frames` 帧预览；
- `/api/v1/vision/preview` 观察 metadata；
- detector metadata 到 `PrimitiveFact` 的转换；
- 分析任务创建 metadata；
- SQLite job metadata；
- SQLite event payload；
- 事件中的事实 metadata。

这证明了软件 API 和存储边界的脱敏，**不证明相机源头已经删除原始帧**。

### 5.2 关键输入类型保护

已拒绝或安全降级：

- 布尔值伪装的数字；
- 数字字符串；
- NaN、Infinity 和超大不可表示整数；
- 越界 confidence；
- 负数或无效区域尺寸；
- bbox 右/下边界溢出；
- 错误 entity ID、zone ID 和重复 ID；
- 乱序时间戳；
- 错误 embedding 矩阵；
- 空向量和全零向量；
- 非法灰度矩阵；
- 无效关键点坐标和关键点 confidence。

---

## 6. 已完成的关键点和动作规则

`KeypointActionExtractor` 只消费上游显式给出的 keypoints，不从像素推断姿态。

### 6.1 关键点格式

支持的关键点格式为：

```text
nose       -> [x_px, y_px, confidence]
left_wrist -> [x_px, y_px, confidence]
right_wrist -> [x_px, y_px, confidence]
```

规则包括：

- 关键点 confidence 默认至少 `0.5`；
- wrist 到 nose 的距离不超过人物 bbox 高度的 `0.2`；
- 同一 wrist 还必须接近同一药品 bbox；
- 输出 confidence 取人物、药品、关系和关键点 confidence 的最小值；
- 同一人物/药品组合一次动作 episode 只输出一次；
- 容忍一个采样帧的关键点缺失；
- 连续缺失超过阈值后重新武装；
- 源切换时清空 episode 和 frame-index 状态；
- 一次调用混合多个 source 会拒绝；
- 观察必须处在同一 UTC frame timestamp；
- 旧帧 `near` / `pickup_candidate` 不能借给当前 keypoints；
- 输出动作事实保留 `source_id`。

生成的 `hand_to_face` 只是一条待复核的几何动作事实，不是医学判断。

---

## 7. 已完成的关系事实和场景推理

### 7.1 RelationEngine

关系层负责把检测和跟踪结果转成：

- 人物—物体距离；
- `near`；
- `pickup_candidate`；
- `putdown_candidate`；
- `motion`；
- `left_zone`；
- `entered_zone`；
- 连续观察状态。

已完成：

- 人物标签共享；
- zone scope 校验；
- 时间统一按 UTC；
- source 内时间倒退保护；
- 检测缺口清除相关位置、关系和区域状态；
- 不跨漏检帧推断 motion、putdown 或 left-zone；
- cooldown 使用结构化 tuple key，修复冒号 ID 冲突；
- 非有限距离和位移不生成事实；
- 同一时刻不同区域的状态不会互相覆盖；
- 重复实体和区域 ID 在状态更新前失败。

### 7.2 养老辅助 `MedicationSequenceReasoner`

完整 `suspected_medication` 候选需要：

1. 明确的药品对象；
2. 同一人物和同一对象的 `object_picked`、`pickup_candidate` 或 `near`；
3. 时间窗内后续 `hand_to_face`、`hand_near_mouth` 或 `object_to_face`；
4. 同一连续段；
5. 必需事实 confidence 达到阈值；
6. 显式 source ID 相同，不能跨来源配对。

已实现的保护：

- 药柜、药架、药房等储存设施不当作药品；
- 药品说明书、药品清单、处方等文档不当作药品；
- 显式 `medicine/medication/drug` 类别可以覆盖显示标签；
- 显式非人物主体不会进入服药推理；
- 布尔、分数、容器等异常 ID 不会被字符串化；
- 只有真实缺失对象 ID 时才允许按标签去重；
- 不同无 ID 药品标签不会互相吞并；
- 低置信度早期动作不会挡住后续有效动作；
- 低置信度可选放下事实不会压低完整候选；
- 只有拿取没有手部动作时输出 `incomplete_medication_sequence`；
- 所有完整事件保留人工复核语义，不写成医疗诊断。

### 7.3 工作室/实验室 `WorkshopStateReasoner`

已实现：

- `object_removed` / `left_zone` 产生移出状态；
- `entered_zone` 必须严格晚于移出并回到同一区域才能形成归还；
- 相同时间戳不按输入顺序推断归还；
- `putdown_candidate` 单独不能证明物品归还；
- `object_missing` 可作为显式缺失候选；
- 超时缺失必须有明确 `scene_observed`；
- 带区域的缺失只能匹配同一区域的待移出状态；
- `observation_gap` 后清空待移出状态；
- 不同 `continuity_segment` 不配对；
- 显式不同 source ID 不配对；
- 同一对象在不同区域的待处理状态分别维护；
- 缺失事件保留原始证据并要求人工复核。

---

## 8. 已完成的 P3 软件质量门控

新增 `visual_event_ai/quality.py`，支持可选的：

```json
{
  "channel_quality": {
    "rgb": {"available": true, "score": 0.92},
    "thermal": {"available": true, "score": 0.20, "reason": "occluded"}
  },
  "quality_required_channels": ["rgb"]
}
```

行为如下：

| 输入情况 | 行为 |
|---|---|
| 没有 `channel_quality` | 保持旧的 Mock/fixture/CPU 路径 |
| 至少一个通道可用 | 继续推理 |
| 部分通道不可用 | 继续推理并写入 `quality_gate.degraded` 摘要 |
| 没有可用通道 | 生成 `observation_gap`，重置跨帧状态，跳过当前帧 |
| 必需通道不可用 | 同上，拒绝当前帧推理 |
| 字段格式错误 | `QualityContractError`，fail closed |

该接口只验证软件降级机制。真实音频、热成像、事件相机、时钟同步、质量标定和通道消融尚未接入。

---

## 9. embedding 和注册特征

当前注册特征是 CPU heuristic，用于验证“参考特征进入事实链”的软件路径：

- 灰度矩阵转换为 4×4 网格均值和 16-bin 强度直方图；
- 向量执行 L2 归一化；
- 严格拒绝布尔、数字字符串、非有限值、空向量和全零向量；
- 匹配 threshold 必须是有限非布尔 `[0,1]` 数值；
- API 返回候选相似度和 `accepted`；
- 空/全零注册向量不会落库。

它不是人脸识别、身份认证、跨摄像头 ReID 或医疗身份判断。

---

## 10. Provider 和真实模型边界

`DetectorProviderRegistry` 当前包含：

| Provider | 状态 | 说明 |
|---|---|---|
| `motion_cpu` | 可用 | 可解释帧差 CPU baseline |
| `fixture` | 可用 | JSONL 预计算对象和显式 keypoints |
| `onnx` | 明确 unavailable | 没有验证过的具体模型输入/输出 adapter |

即使指定了模型路径或安装了 `onnxruntime`，ONNX provider 也不会因为“文件存在”而自动变成可用。项目没有擅自下载或接入未经验证的 YOLO、AlphaPose、HRNet、MediaPipe、2S-AGCN、ByteTrack 或其他模型。

---

## 11. 任务、API 和存储能力

### 11.1 任务生命周期

任务状态包括：

- `queued`；
- `running`；
- `completed`；
- `failed`；
- `stopped`。

已完成：

- 每个 job 独立取消令牌；
- 帧边界停止；
- 停止后不运行插件、不落库部分事件；
- stop 和 completion 使用终结锁；
- 事件批次和 completed 状态在同一 SQLite 事务提交；
- 已完成任务重复执行不会重复生成事件。

### 11.2 API 契约

已覆盖的主要接口类别：

- `/health`、`/ready`；
- source inspect 和 frame preview；
- vision preview；
- detector provider 状态；
- plugin 列表和开关；
- analysis job 创建、查询、列表和停止；
- event 查询和 review；
- evidence resolve；
- object/person registry 和 embedding match；
- `AI_ZONES_JSON` 区域配置。

### 11.3 Evidence 和 SQLite

- 事件保存 source、时间窗、插件、事实和 evidence ref；
- 未配置真实 resolver 时明确返回 unavailable 或 designed 状态；
- 不猜测 HLS segment、签名 URL 或 MinIO 对象键；
- SQLite 写入前对 metadata 做像素脱敏；
- 事件保留人工 review 状态；
- 证据 URI 不被伪装成已验证回放。

---

## 12. AIC 竞赛材料和参考资料完成情况

### 12.1 官方 PDF 规则

已阅读项目根目录的两份 PDF，并单独整理规则来源和用户转写的区别：

- `关于举办第八届AIC算法创新赛道竞赛的通知2604291.pdf`；
- `2026AIC算法创新赛赛题规则汇总260506-1.pdf`。

当前项目被整理为 `AI+场景创新` 候选方向，重点对应“忘记物品放在哪里、忘记之前发生过什么操作”的养老和工作室场景。评分映射已经记录为：创新性 20、需求分析 15、解决方案可行性 20、项目实施 15、测试与验证 10、应用效果 15、总结与展望 5。

已明确：本地 363 个测试只能支撑软件链路和规则契约，不能直接变成真实应用效果、模型精度或硬件验收证据。

### 12.2 四份 DOCX 参考作品

已审计：

1. `智隐云眸最新V1.docx`；
2. `物联网应用类作品技术文档【终稿】002.docx`；
3. `面向复杂实验室环境的多模态感知 (1).docx`；
4. `MoMaGen.docx`。

从中提取的只是可借鉴方法：

- 隐私优先和骨骼化；
- 姿态、动作和时序结构；
- 目标检测、跟踪和关键点质量；
- 多模态质量门控；
- 失败样本、消融和 sim-to-real 的验证思想；
- 约束和硬/软证据门槛。

文档中的模型名称、准确率、硬件参数、专利描述、实机结果和目标指标没有被当作当前项目的实测结果。

---

## 13. 当前真实完成度和证据边界

### 已经可以声称

- AI 软件工程链路可以在本地启动和测试；
- Mock、JSONL、CPU detector、关系层、时序推理器和插件可以组合运行；
- 输入类型、来源、时间、连续段、置信度和隐私 metadata 有明确保护；
- 任务停止、SQLite 写入和事件 review 有可验证的行为；
- 质量不足的可选通道可以软件层降级或拒识；
- 提交暂存包可以通过 `VERIFY.ps1 -SkipFrontendBuild`。

### 不能声称

- 真实人体姿态识别准确率；
- 真实药品检测准确率；
- ByteTrack、Kalman、ReID 或步态识别已经接入；
- 真实音频、热成像或事件相机已经融合；
- 相机源头已经完成骨骼化并删除原始图像；
- 真实数据集上的 precision、recall、F1、IDF1、HOTA；
- 真实部署延迟、吞吐、GPU 占用或稳定性；
- 机器人已经收到事件并安全执行动作；
- 比赛最终赛道、最终名次或应用效果已经确认。

---

## 14. 如果后续获得真实 AI 数据，下一步顺序

### P0：真实输入和隐私来源

- 固定真实模型输出 schema；
- 明确原始帧是否在相机/边缘节点删除；
- 记录 source、timestamp、frame index、confidence、track 和 quality metadata；
- 验证网络、日志、SQLite、证据和回放各层的原始帧保留策略。

### P1：检测、姿态和跟踪

- 记录模型版本、类别表和输入尺寸；
- 按遮挡、漏检、多人交叉和光照切片；
- 评估关键点质量和 ID switch；
- 在同一数据集、同一门控和同一指标下对照 CentroidTracker、ByteTrack、Kalman 或其他方案；
- 不用参考文档里的指标替代本项目实测。

### P2：场景和事件评估

- 建立养老和工作室标注协议；
- 运行时序回放；
- 报告事件级 precision、recall、F1、误报、漏报、拒识和延迟；
- 保留失败样例和人工复核记录。

### P3：多模态质量和时间同步

- 把真实传感器映射到 `channel_quality`；
- 验证时间对齐、缺失、漂移和故障注入；
- 做单通道、多通道和去除某通道的消融；
- 重新确认低质量通道不会伪造事件证据。

### P4：硬件和机器人

本项目当前不执行该阶段，除非用户另行要求并提供相应硬件、协议和授权资料。

---

## 15. 关键文件索引

### AI 源码

- `workspace/ai-engine/src/visual_event_ai/frame_pipeline.py`
- `workspace/ai-engine/src/visual_event_ai/providers.py`
- `workspace/ai-engine/src/visual_event_ai/model_providers.py`
- `workspace/ai-engine/src/visual_event_ai/relations.py`
- `workspace/ai-engine/src/visual_event_ai/fact_pipeline.py`
- `workspace/ai-engine/src/visual_event_ai/keypoint_actions.py`
- `workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py`
- `workspace/ai-engine/src/visual_event_ai/privacy.py`
- `workspace/ai-engine/src/visual_event_ai/quality.py`
- `workspace/ai-engine/src/visual_event_ai/embeddings.py`
- `workspace/ai-engine/src/visual_event_ai/service.py`
- `workspace/ai-engine/src/visual_event_ai/storage.py`
- `workspace/ai-engine/src/visual_event_ai/app.py`

### 测试

- `workspace/ai-engine/tests/test_frame_pipeline.py`
- `workspace/ai-engine/tests/test_providers.py`
- `workspace/ai-engine/tests/test_model_providers.py`
- `workspace/ai-engine/tests/test_relations.py`
- `workspace/ai-engine/tests/test_fact_pipeline.py`
- `workspace/ai-engine/tests/test_keypoint_actions.py`
- `workspace/ai-engine/tests/test_algorithm_reasoner.py`
- `workspace/ai-engine/tests/test_plugins.py`
- `workspace/ai-engine/tests/test_embeddings.py`
- `workspace/ai-engine/tests/test_privacy.py`
- `workspace/ai-engine/tests/test_quality.py`
- `workspace/ai-engine/tests/test_api.py`
- `workspace/ai-engine/tests/test_core.py`

### AI 文档和状态

- `workspace/docs/AI_ALGORITHM_DESIGN.md`
- `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md`
- `workspace/docs/TEMPORAL_EVENT_REASONING.md`
- `workspace/docs/MODEL_PROVIDER_CONTRACT.md`
- `workspace/docs/REFERENCE_ALGORITHM_AUDIT.md`
- `workspace/docs/AIC_ALGORITHM_COMPETITION_ALIGNMENT.md`
- `agent-state/MASTER_STATUS.md`
- `agent-state/CURRENT_TASK.md`
- `agent-state/TEST_EVIDENCE.md`
- `agent-state/VERIFIED_FACTS.md`
- `agent-state/NEXT_SESSION.md`

---

## 16. 最终判断

当前项目已经从“只有资料和想法”推进到“有分层 AI 软件、可解释规则、失败边界、测试证据和提交暂存包”的阶段。

当前最重要的成果不是宣称某个模型达到了某个准确率，而是把以下边界固定了：

- 什么输入可以进入算法；
- 什么输入必须拒绝；
- 什么事实可以拼成事件；
- 什么事实必须降级为不完整线索；
- 哪些状态不能跨来源、跨时间或跨 gap 继承；
- 哪些像素和敏感 metadata 不能进入 API、日志式事件证据和 SQLite；
- 哪些结果只是 fixture/CPU 本地验证；
- 哪些能力必须等真实模型、真实数据或外部资料到位后再声称。

因此，按当前用户限定的 AI 代码范围，软件侧阶段性目标已经完成；后续只有在获得新的真实 AI 数据、模型输入契约或明确需求时，才需要继续扩大算法实现。

## TASK-0010 final-audit addendum (2026-09-25)

TASK-0009 v3 is now included in the current AI baseline. The implemented path is
`privacy/quality boundary -> pose + semantic-object providers -> combined perception ->
Centroid/Hungarian tracking -> relations -> generic action primitives -> VisualMemory ->
TemporalVisualMemory -> medication/workshop review reasoners -> UnifiedEvent/frontend contract`.
The semantic object model remains optional and no custom medicine weights or metrics are claimed.

The current source and curated submission suites are **414 passed** before the TASK-0010
acceptance-matrix additions; the final TASK-0010 run records the larger final count. The
curated verifier is the source of truth for submission hygiene. Evidence is separated into
REAL_RUNTIME_SMOKE (official pose adapter/local-video smoke) and LOCAL_ONLY/software-contract
fixtures. Frontend, robot, camera-edge skeletonization, dataset accuracy, ReID, gait,
2S-AGCN and audio-fusion claims remain outside this AI result.

See `AI_ALGORITHM_FINAL_REPORT.md` for the final module/formula/evidence audit and
`FRONTEND_AI_INTEGRATION_CONTRACT.md` for the frozen handoff contract.
