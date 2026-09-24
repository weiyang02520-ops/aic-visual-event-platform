# TASK-0004：真实本地视频到事实链路冒烟证据

日期：2026-09-24  
证据等级：`REAL_RUNTIME_SMOKE`

## 结论

已把官方公开 `bus.jpg` 样例写成项目内忽略的两帧 AVI，只为验证本地视频解码路径，然后通过完整链路运行：

```text
runtime/samples/task-0004-bus.avi
→ FramePipeline
→ OpenCVFrameProvider
→ BGR payload
→ DetectorProviderRegistry / UltralyticsProvider
→ CentroidTracker / normalize_observations
→ FrameFactExtractor
→ object_detected PrimitiveFact
```

真实模型和真实 OpenCV 解码都参与了运行。该记录仍是冒烟证据，不是准确率、性能、场景事件、生产部署、真实摄像头或机器人验收。

## 输入与运行身份

- 来源类型：项目内短 AVI；由已授权的官方公开 `bus.jpg` 生成两帧，仅用于触发 OpenCV 解码器
- 视频路径：`workspace/ai-engine/runtime/samples/task-0004-bus.avi`（被 `.gitignore` 忽略）
- 视频 SHA-256：`81b361f0dce039984d680d063c9f0d4e6fb2b907e2941bf73f8f87f571b07549`
- 模型：`yolo11n-pose.pt`
- 模型 SHA-256：`869e83fcdffdc7371fa4e34cd8e51c838cc729571d1635e5141e3075e9319dc0`
- `ultralytics`：`8.4.161`
- `torch`：`2.14.0+cpu`
- OpenCV：`5.0.0`
- 设备：CPU

## 链路结果

- `OpenCVFrameProvider` 解码帧数：`2`
- 每帧 payload 都包含模型输入用的 BGR `image`
- `FrameFactExtractor` 产出人物 `object_detected` facts：`8`（每帧 4 个）
- 每个真实人物 fact 保留 provider 的 `nose`、`left_wrist`、`right_wrist` keypoints
- `source_id` 保留为 `runtime/samples/task-0004-bus.avi`
- 所有人物 fact 的时间戳均为带时区的 UTC 时间；两帧分别落在 `13:14:13.487530+00:00` 和 `13:14:14.487530+00:00`
- OpenCV 解码耗时约 `0.078 s`，完整模型到 facts 链路约 `3.074 s`；均为单次粗略诊断值，不是性能基准
- 事实 metadata 未携带原始像素；模型权重、样例视频、虚拟环境和运行缓存均未进入 Git

## 验证边界

这次运行证明本地 AVI 能通过 OpenCV 产生 BGR 帧，真实 Ultralytics provider 能被 registry 选中并完成推理，tracker/观察归一化/fact pipeline 能产出带来源、时间戳和关键点的 `object_detected` 事实。它没有验证检测准确率、跨帧身份稳定性、遮挡、动作/用药场景事件、摄像头源头隐私处理或机器人行为。
