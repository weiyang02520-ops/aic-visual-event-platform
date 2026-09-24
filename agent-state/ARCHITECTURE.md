# Architecture

## Current state

已在本资料根目录建立可运行的 AI 服务和前端骨架。AI 当前包含统一事件、SQLite、插件、来源/帧管线、CPU 检测/跟踪、关系事实和场景状态；前端当前包含 Mock/Real API 适配与多页面控制台。真实媒体、模型和机器人协议仍为后续适配边界。

## Intended boundaries from the handoff plan

- `workspace/ai-engine/`: 独立 AI 服务与插件。
- `workspace/frontend/`: 多场景前端、Mock/Real provider 和事件/证据视图。
- Makerverse：既有业务后端，原则上作为黑盒集成对象。
- livestream-rs：既有媒体/视频流底座，原则上不重写。
- `workspace/docs/`: 架构、算法、实验、比赛提交素材。
- `workspace/submission/`: 干净的最终提交包，不放 agent-state、提示词、临时日志或个人路径。

所有“当前架构”描述须以实际代码和测试为准；以上未实现部分只能称为计划或目标。
