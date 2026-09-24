# Visual Event AI

独立的 Python 视觉事件分析服务。第一版先提供可运行的通用事件契约、插件自动发现、SQLite 历史和 deterministic Mock 输入，后续再接本地视频、HLS/RTSP、livestream-rs 和真实模型。

## 启动

```powershell
cd ai-engine
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# 如果需要 MP4/AVI/MKV 本地读取：
.\.venv\Scripts\python.exe -m pip install -e ".[media]"
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m visual_event_ai
```

服务默认监听 `http://127.0.0.1:8010`。

服务使用 Python 标准 logging/HTTP server 日志记录插件加载、分析任务创建/开始/停止/完成/失败和插件异常。日志只包含 job_id、source 标识、插件 ID、数量和状态，不输出原始图像、embedding 内容或凭据。

## 最小演示

```powershell
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/api/v1/plugins
curl -X POST http://127.0.0.1:8010/api/v1/analysis/jobs `
  -H "Content-Type: application/json" `
  -d '{"source":"mock://elderly-medication"}'
curl http://127.0.0.1:8010/api/v1/events
```

可用 Mock source：

- `mock://elderly-medication` — 产生疑似服药相关事件；
- `mock://workshop-tool` — 产生物品离开登记区域事件。

## API

- `GET /health`, `GET /ready`
- `GET /api/v1/sources/inspect?source=...`（只做来源路由/可用性检查，不解码视频）
- `GET /api/v1/sources/frames?source=...`（Mock/JSONL fixture 帧预览；真实媒体需显式 provider）
- `GET /api/v1/vision/preview?source=...&detector=fixture|motion`（检测、跟踪和统一观察结果预览）
- `GET /api/v1/evidence/resolve?...`（保守解析证据引用，不猜测 HLS/MinIO URL）
- `GET /api/v1/providers/detectors?source=...`（检测 provider 可用性和 fallback 状态）
- `POST /api/v1/registry/match`（登记对象/人员的 CPU baseline 特征匹配；不等同于人脸识别）
- `GET /api/v1/plugins`
- `POST /api/v1/plugins/{id}/enable`
- `POST /api/v1/plugins/{id}/disable`
- `POST/GET /api/v1/analysis/jobs`
- `GET /api/v1/analysis/jobs/{id}`
- `POST /api/v1/analysis/jobs/{id}/stop`
- `GET /api/v1/events`
- `GET /api/v1/events/{id}`
- `POST /api/v1/events/{id}/review`
- `GET/POST/DELETE /api/v1/objects`
- `GET/POST/DELETE /api/v1/persons`

## 插件

服务启动时扫描 `plugins/*/manifest.json`。插件实现 `build_plugin(manifest)` 和 `evaluate(facts, source_id)`，插件加载失败会进入 `error` 状态，不会拖垮整个服务。新增插件只需新增目录、manifest 和入口文件，核心服务无需改动。

养老和工作室插件已接入 `algorithm_reasoner.py` 中的时序规则，并在事件中保留推理所用事实。阈值、身份/对象匹配、缺失观察和真实视频输入边界见 `../docs/TEMPORAL_EVENT_REASONING.md`。

## Provider 与关系基线

`FramePipeline` 将 source 路由到 Mock/JSONL provider；`MotionDetector`、`FixtureDetector`、`CentroidTracker` 和 `RelationEngine` 位于独立模块，可被真实模型或机器人适配器替换。当前 `/api/v1/vision/preview` 是预览接口，不是最终生产推理吞吐基准。

可选真实视觉 provider：

```powershell
python -m pip install -e ".[pose]"
$env:AI_DETECTOR_PROVIDER = "ultralytics"
$env:AI_ULTRALYTICS_MODEL_PATH = "C:\path\to\verified-pose-model.pt"
```

`ultralytics` provider 只归一化 person bbox/confidence 和 COCO17 `nose`、`left_wrist`、`right_wrist` keypoints；缺少依赖、模型文件或合法输入时明确 unavailable/fail closed。当前仓库不包含模型权重；fake-result 和本地 frame/fact contract tests 已覆盖 adapter，真实模型运行和准确率仍未验证。

注册对象/人员可保存一个数值 embedding；`embeddings.py` 提供灰度矩阵 baseline、归一化和余弦相似度匹配。它是可解释的 CPU heuristic，默认保留 unknown/ambiguous，不宣称人脸识别或比赛准确率。

## 可选区域配置

`AnalysisService` 默认不配置区域。启动服务前可设置 `AI_ZONES_JSON`，值为 JSON 数组；每项包含唯一 `zone_id`、非空 `label`、有限数值 `x` / `y` 和正数 `width` / `height`。这些矩形使用 detector bbox 对应的帧像素坐标系。例如 PowerShell：

```powershell
$env:AI_ZONES_JSON = '[{"zone_id":"shelf-a","label":"工具架 A","x":0,"y":0,"width":120,"height":80}]'
```

未设置或设为 `[]` 时不产生区域事实；非法 JSON、缺失/未知字段、重复 ID 或无效几何会在服务启动时显式失败。`.env.example` 仅供参考，服务不会自动读取 `.env` 文件。项目没有真实相机区域校准数据。

## 真实性边界

当前 Mock 事件用于演示和测试，不代表模型准确率，也不代表真实老人、真实摄像头、真实机器人或真实 livestream-rs 联调已经完成。AI 事件使用“疑似”和“待复核”表述；视频证据 resolver 目前只保留结构和时间窗，真实 HLS/MinIO 定位属于后续集成任务。

来源抽象已先行：`mock://` 进入确定性演示 provider；`rtmp://`、`rtsp://`、`http(s)://` 进入 livestream-rs 适配边界；本地文件进入 local-file-provider。该层不会把“已配置”误报为“已连接”，也不会在缺少 FFmpeg 时伪造帧分析结果。

本地 JSONL/OpenCV 帧现在会进入 analysis job 的检测、跟踪、关系和 `PrimitiveFact` 链；如果没有可用 OpenCV，请安装 `.[media]`，或使用 JSONL fixture。

OpenCV 本地视频帧的 payload 同时提供模型输入用的 BGR `image` 和 MotionDetector 使用的 list-based `gray` helper，并附带 `shape` / `channels`。像素只在瞬时帧/推理路径中存在；公共预览、事实 metadata、job metadata 和 SQLite 事件写入会走递归像素摘要脱敏。

若检测 provider 在人物对象中提供 `nose`、`left_wrist`、`right_wrist` 关键点，`KeypointActionExtractor` 可按几何距离生成启发式 `hand_to_face` 事实，并绑定同一人物附近的药品框；它容忍一个采样帧的关键点缺失以避免重复动作边缘。当前只有 fixture 输入验证此路；项目没有内置姿态模型，也不会从普通像素帧伪造关键点。
