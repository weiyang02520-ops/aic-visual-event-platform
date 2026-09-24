# AI Detector / Tracker Phase 3

日期：2026-09-23

## 实现

- `Detector` protocol：输入统一 `Frame`，输出 `Detection(label, confidence, bbox, metadata)`；
- `Tracker` protocol：输入检测列表，输出带稳定 `track_id`、年龄和 missed 计数的 `Track`；
- `MotionDetector`：纯 Python CPU 帧差 + 四邻域连通区域基线，只报告变化像素区域，不识别物体语义；首帧、来源切换、新分析任务及坏帧后不跨状态做帧差；输出的面积分数是启发式值，不是概率；
- `FrameFactExtractor`：每次提取建立独立的 detector session；JSONL 恢复模式遇到被跳过的坏行时发出 `observation_gap`，重置 detector/tracker/关系/关键点状态，并以新的 `continuity_segment` 继续产出事实；
- `channel_quality` 软件契约：可选通道质量元数据经过严格校验；部分通道可用时事实带 `quality_gate.degraded` 摘要，没有可用/必需通道时发出 `observation_gap` 并重置跨帧状态；这只验证软件降级，不代表真实传感器时间同步或质量标定；
- `FixtureDetector`：把机器人/相机/标注 fixture 的预计算 objects 归一化，便于端到端测试；缺少 objects 字段表示空帧，显式 objects 列表内每项都必须是带 bbox 的对象记录；保留 pose `keypoints` 与浮点 bbox，非法行、标签、几何或置信度会带记录索引报错，不会裁剪异常分数；
- 参数契约：MotionDetector 的阈值/面积和 CentroidTracker 的 missed 计数要求非布尔整数；RelationEngine/Tracker 距离与冷却要求非布尔有限实数，错误类型统一返回 ValueError。
- `CentroidTracker`：先按类别和最大距离门控，再做最大有效匹配数下的最小总距离分配，输出 track id；人物类别复用共享分类器，其他标签按大小写不敏感的完整类别匹配；交叉、遮挡和快速移动时仍可能发生 ID switch；
- `normalize_observations`：统一输出 source_id、timestamp、fact_type、confidence、subject/object 和 metadata；对相同类别与相同 bbox 的重复检测逐个分配 track，避免 dictionary 覆盖导致观察共用同一个 ID；
- FastAPI：`/api/v1/vision/preview` 支持 `fixture` 或 `motion` provider 预览。

## 不应误读的部分

MotionDetector 是可解释的算法基线，不是已经训练好的老人服药识别模型，也没有准确率结论。全局光照变化也可能被当成大面积运动。CentroidTracker 的全局分配只优化通过距离门控后的总质心距离，未实现运动模型、外观/ReID 特征或遮挡推理。两者只证明本地接口和合成行为；真正的物体/动作模型须等赛道和授权数据确定后验证。

`KeypointActionExtractor` 消费 provider/fixture 显式给出的鼻部和手腕坐标，生成同一人物/药品关系上的 `hand_to_face` 几何规则事实。它不运行姿态模型，不从灰度帧推断关键点，也没有真实视频指标。

## 验收证据

针对检测/跟踪、关系、时序推理与插件的定向测试覆盖帧差区域、来源/任务状态隔离、坏矩阵、重复 bbox、track ID 保持、门控匹配数量和全局最小距离分配、区域关系和场景事件，以及恢复间隙和显式来源隔离后的状态配对；当前全量测试为 `363 passed`，结果见根目录 `agent-state/TEST_EVIDENCE.md`。
