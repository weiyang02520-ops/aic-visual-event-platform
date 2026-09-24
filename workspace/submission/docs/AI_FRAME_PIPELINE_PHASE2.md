# AI Frame Pipeline Phase 2

日期：2026-09-23

## 目的

把输入来源、抽帧、时间戳和取消语义先固定下来，使后续真实相机、livestream-rs、机器人 SDK 或本地解码器可以替换 provider，而不用改事件和插件层。

## 当前实现

- `Frame`：统一携带 `source_id`、`frame_index`、UTC `timestamp`、payload 和 provider metadata；
- `CancellationToken`：停止/取消在 provider 迭代前检查；
- `MockFrameProvider`：生成可控数量、可控时间间隔的确定性帧；
- `JsonlFrameProvider`：读取 JSONL/NDJSON 本地 fixture，支持坏行跳过或严格失败；恢复模式跳过坏行时，会在下一条有效帧的 metadata 标记 `discontinuity_before=true`、原因和被跳过的行号，避免下游把未知间隔当成连续观察；
- `OpenCVFrameProvider`：通过可选 `media` extra 读取 MP4/AVI/MOV/MKV/WEBM/M4V，按 FPS/时间戳抽帧；非有限/不可表示的 FPS 使用 25 fps fallback，异常 PTS 使用 read_index/fps 估计，仍无法形成有效时间戳时返回 FramePipelineError。payload 现在保留模型可消费的 BGR `image`，并提供 list-based `gray` helper、`shape` 和 `channels` 元数据；MotionDetector 继续只消费 `gray`，公共预览会对 BGR/gray 做摘要脱敏。模拟非法 FPS/PTS 元数据的回归与本地 AVI fixture 检查都通过；TASK-0004 进一步用真实 OpenCV 解码和真实 Ultralytics provider 贯通到 `PrimitiveFact`；模拟数据不替代真实异常码流验证；
- `FramePipeline`：按 `mock://`、本地路径/`file://` 路由 provider，未知流媒体显式拒绝；抽帧 interval_ms 严格接受非布尔非负整数且须落在 timedelta 范围内，max_frames 接受非布尔非负整数或 None，0 表示空结果；
- `FrameFactExtractor`：将本地帧经过 detector/tracker/relations 转换为统一 `PrimitiveFact`，并接入 analysis job；收到恢复间隙标记时发出 `observation_gap`，递增 `continuity_segment`，重开 detector session，并清除 tracker、关系和关键点动作的跨帧状态；间隙后的事实携带新的连续段标记；
- FastAPI：`/api/v1/sources/frames` 提供受限帧预览。

## 真实边界

RTSP、RTMP、HLS 的真实解码没有被伪造。当前环境已用 OpenCV 读取一个项目内两帧 AVI，并把真实 BGR 帧送入真实 Ultralytics provider，经过 tracker/观察归一化和 `FrameFactExtractor` 产出人物 `object_detected` facts；详细结果见 `REAL_LOCAL_VIDEO_SMOKE_TASK-0004.md`。没有 OpenCV 时会明确提示安装 `.[media]`，没有 Cargo/FFmpeg/livestream-rs 时流媒体仍返回“已配置但未连接”。这次 AVI 是由官方公开样例生成的受控冒烟输入，不替代真实摄像头、异常码流或现场视频证据。

## 验收证据

`workspace/ai-engine` 当前全量测试为 371 passed，reasoner/plugin 定向测试为 103 passed；新增回归覆盖 BGR+gray OpenCV payload、OpenCV-style frame 到 Ultralytics fake provider 的 source/timestamp/keypoint 传递、BGR/gray 公共预览脱敏，以及既有 JSONL 恢复坏行后的 observation gap、状态重置、检测 session 隔离和来源/连续段保护。TASK-0004 的真实本地视频到 facts 冒烟记录了 2 个解码帧和 8 个真实人物 facts。测试使用项目内绝对 basetemp，验收后已清理。
