# AI + 前端 Phase 1 交付记录

日期：2026-09-22

## 已交付

### AI Engine

`workspace/ai-engine/` 是独立 Python 服务，当前已具备：

- 统一视觉事件模型、SQLite 事件/任务/对象/人员存储；
- `plugins/*/manifest.json` 自动发现、逐插件启停和故障隔离；
- 养老与工作室两个确定性 Mock 插件；
- analysis job、事件复核、对象/人员登记 REST API；
- `SourceResolver` 来源边界：Mock、本地文件、流媒体 URI 和未知来源；
- `/api/v1/sources/inspect` 只报告路由与状态，不伪造视频解码或网络连接。
- `FramePipeline` 提供带 timestamp/source_id 的 Mock 和 JSONL fixture 帧，支持抽帧间隔、取消和坏行恢复；真实 MP4/RTSP 解码仍由显式 provider 接入。

### Frontend

`workspace/frontend/` 是 React + Vite 控制台，包含：

- Mock / Real API 数据源切换；
- 总览、实时监控、事件中心、插件能力、对象与人员、系统设置；
- 事件确认/驳回、插件启停、Mock 分析任务触发；
- 养老、工作室、机器人预留、通用视觉四个场景入口；
- 深色 teal 运维控制台视觉系统和响应式布局。

## 验证

```powershell
cd ai-engine
$env:PYTHONPATH = "src"
python -m pytest -q  # 15 passed

cd "..\frontend"
npm install
npm run build       # TypeScript + Vite passed
npm run dev -- --host 127.0.0.1 --port 4173
```

## 边界

本阶段不声称真实模型准确率、真实摄像头取帧、livestream-rs 联调或机器人实机通过。JSONL 是可复现的测试输入，不等价于 FFmpeg、RTSP 或相机解码。拿到老师主文档和机器人协议后，下一阶段按来源适配器、模型 provider、证据 resolver 和实机验收链补齐。
