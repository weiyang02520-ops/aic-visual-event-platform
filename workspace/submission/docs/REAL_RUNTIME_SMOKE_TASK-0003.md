# TASK-0003：Ultralytics 真实姿态运行时冒烟证据

日期：2026-09-24  
证据等级：`REAL_RUNTIME_SMOKE`

## 结论

已在项目内的 Python 3.12 虚拟环境中安装可选 `pose` 与 `media` extras，使用官方 Ultralytics 轻量姿态模型和官方公开样例图，调用项目的 `UltralyticsProvider` 完成一次真实模型加载和 CPU 推理。模型没有经过训练、微调或准确率评测；本记录不能作为准确率、F1、mAP、吞吐、生产部署、真实摄像头或机器人验收证据。

## 运行身份

- Python：`3.12.10`
- `ultralytics`：`8.4.161`
- `torch`：`2.14.0+cpu`
- OpenCV：`5.0.0`
- 设备：CPU
- 安装方式：项目 `workspace/ai-engine/.venv` 内执行 `pip install -e ".[pose,media]"`；测试依赖随后以 `.[dev]` 安装

## 模型与样例

- 模型：`yolo11n-pose.pt`
- 官方来源：<https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n-pose.pt>
- 项目内本地路径：`workspace/ai-engine/runtime/models/yolo11n-pose.pt`（被 `.gitignore` 忽略）
- 模型 SHA-256：`869e83fcdffdc7371fa4e34cd8e51c838cc729571d1635e5141e3075e9319dc0`
- 样例：`bus.jpg`（官方公开 Ultralytics 样例）
- 官方来源：<https://github.com/ultralytics/assets/releases/download/v0.0.0/bus.jpg>
- 项目内本地路径：`workspace/ai-engine/runtime/samples/bus.jpg`（被 `.gitignore` 忽略）
- 样例 SHA-256：`c02019c4979c191eb739ddd944445ef408dad5679acab6fd520ef9d434bfbc63`

## Provider 执行结果

执行路径是 `UltralyticsProvider(model_path=...)` → `provider.detect(Frame(payload={"image": <OpenCV BGR>}))`，不是直接绕过项目适配器调用 Ultralytics API。

- 模型路径和依赖检查在加载前通过：`available=True`
- 真实模型加载后：`provider.reason() == None`
- 归一化检测数量：`4`，全部为 `person`
- 四个归一化人物检测均包含 `nose`、`left_wrist`、`right_wrist` 三个 COCO17 关键点
- 单张样例的墙钟时间约 `1.438 s`，明确标记为非基准数据；没有重复采样、预热控制或性能结论
- 原始图像像素、模型权重和推理缓存没有写入 Git 跟踪路径

## 边界与后续

这次运行证明可选依赖、官方权重、BGR 输入和现有归一化适配路径可以在 CPU 上串通。它不证明遮挡、跨帧跟踪、身份稳定性、动作/用药场景准确率、隐私源头处理或真实现场性能。后续若要做评测，需要单独登记授权视频/标注、固定模型和阈值、定义切片指标，并与本冒烟证据分开记录。
