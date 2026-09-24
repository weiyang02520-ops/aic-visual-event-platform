# 本地帧到分析任务链路

日期：2026-09-22

当前 `POST /api/v1/analysis/jobs` 不再只支持 Mock 事实：

1. `mock://...` 继续使用确定性场景 fixture；
2. `.jsonl/.ndjson` 使用 `JsonlFrameProvider` + `FixtureDetector`；
3. `.mp4/.avi/.mov/.mkv/.webm/.m4v` 使用可选 `OpenCVFrameProvider` + `MotionDetector`；
4. `CentroidTracker` 保持 track id；
5. `RelationEngine` 产生关系事实；
6. `FrameFactExtractor` 将观察和关系转换为 `PrimitiveFact`；
7. 统一插件继续消费 facts 并写入 SQLite 事件。

如果本地输入是 RTMP/RTSP/HLS，当前任务会明确返回失败，因为 livestream-rs/FFmpeg 适配器尚未配置；这比生成一个看似完成但无法回看的事件更符合证据要求。

## 当前验收

- 本地 JSONL analysis job 已在测试中完成，`fact_count` 可核验；
- OpenCV 临时 AVI 已真实读取 2 帧；
- 该阶段记录时全套 AI 测试为 20 passed；当前回归已扩展到 28 passed（增加模型 provider、注册特征匹配、任务停止和 API 覆盖）。
- 真实媒体与机器人输入仍需外部工具链和资料。
