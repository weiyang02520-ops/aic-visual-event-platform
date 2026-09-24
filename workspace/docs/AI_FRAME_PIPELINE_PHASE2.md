# AI Frame Pipeline Phase 2

日期：2026-09-23

## 目的

把输入来源、抽帧、时间戳和取消语义先固定下来，使后续真实相机、livestream-rs、机器人 SDK 或本地解码器可以替换 provider，而不用改事件和插件层。

## 当前实现

- `Frame`：统一携带 `source_id`、`frame_index`、UTC `timestamp`、payload 和 provider metadata；
- `CancellationToken`：停止/取消在 provider 迭代前检查；
- `MockFrameProvider`：生成可控数量、可控时间间隔的确定性帧；
- `JsonlFrameProvider`：读取 JSONL/NDJSON 本地 fixture，支持坏行跳过或严格失败；恢复模式跳过坏行时，会在下一条有效帧的 metadata 标记 `discontinuity_before=true`、原因和被跳过的行号，避免下游把未知间隔当成连续观察；
- `OpenCVFrameProvider`：通过可选 `media` extra 读取 MP4/AVI/MOV/MKV/WEBM/M4V，按 FPS/时间戳抽帧；非有限/不可表示的 FPS 使用 25 fps fallback，异常 PTS 使用 read_index/fps 估计，仍无法形成有效时间戳时返回 FramePipelineError。模拟非法 FPS/PTS 元数据的回归与本地 AVI fixture 检查都通过；模拟数据不替代真实异常码流验证；
- `FramePipeline`：按 `mock://`、本地路径/`file://` 路由 provider，未知流媒体显式拒绝；抽帧 interval_ms 严格接受非布尔非负整数且须落在 timedelta 范围内，max_frames 接受非布尔非负整数或 None，0 表示空结果；
- `FrameFactExtractor`：将本地帧经过 detector/tracker/relations 转换为统一 `PrimitiveFact`，并接入 analysis job；收到恢复间隙标记时发出 `observation_gap`，递增 `continuity_segment`，重开 detector session，并清除 tracker、关系和关键点动作的跨帧状态；间隙后的事实携带新的连续段标记；
- FastAPI：`/api/v1/sources/frames` 提供受限帧预览。

## 真实边界

RTSP、RTMP、HLS 的真实解码没有被伪造。当前环境已用 OpenCV 生成并读取一个 16x12、2 帧 AVI fixture，证明本地 provider 可运行；没有 OpenCV 时会明确提示安装 `.[media]`，没有 Cargo/FFmpeg/livestream-rs 时流媒体仍返回“已配置但未连接”。后续适配器只需实现 `FrameProvider.iter_frames`。

## 验收证据

`workspace/ai-engine` 当前全量测试为 363 passed，reasoner/plugin 定向测试为 103 passed；新增回归覆盖 JSONL 恢复坏行后的 observation gap、状态重置、检测 session 隔离，以及不跨连续段或显式来源配对服药动作、归还和工作室缺失。HTTP smoke 已返回 3 个连续 Mock 帧，index 0–2，source_id 和 provider metadata 保留。测试使用项目内绝对 basetemp，验收后已清理。
