# Sentinel 视觉事件控制台

面向 Makerverse/livestream-rs + 独立 AI 服务的前端原型。当前版本优先保证离线 Mock 演示完整，再通过同一组 `Repository` 方法切换真实 AI REST API。

## 启动

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 `http://127.0.0.1:5173`。

## Real API

默认 Real API 地址为 `http://127.0.0.1:8010`，也可以设置：

```powershell
$env:VITE_AI_API_URL = "http://127.0.0.1:8010"
npm run dev
```

如果要让 Real 模式监控页读取 Makerverse 在线直播，可额外配置：

```powershell
$env:VITE_MAKERVERSE_API_URL = "http://127.0.0.1:5000"
$env:VITE_MAKERVERSE_TOKEN = "仅放在本地环境，不提交到仓库"
```

页面会调用 `/lives/online` 和 `/lives/{id}/endpoint`；未配置、请求失败或没有在线直播时显示明确原因，不会伪造播放画面。

页面通过 `src/repository.ts` 的 `Repository` 接口访问数据，Mock/Real 切换不会散落在页面业务逻辑中。

Real 模式创建分析任务后会按 `job_id` 轮询 `/api/v1/analysis/jobs/{id}`，直到 `completed`、`failed` 或 `stopped`，再刷新事件中心；这对应 AI API 的 `202 Accepted` 异步任务语义。

Makerverse 媒体边界在 `src/media.ts`：它归一化 `/lives/online` 与 `/lives/{id}/endpoint` 的 DTO，并区分 Mock、RTMP、RTSP、HLS 和 HTTP-FLV。当前只完成地址分类和接口边界，真实播放器需要在部署地址、CORS、鉴权和浏览器实测确认后再接入；详见 `workspace/docs/MEDIA_PLAYBACK_ADAPTER.md`。

AI 服务启动后，可以在另一个终端执行 `npm run smoke:real`，检查前端 Real API 所依赖的 health、plugins、events、objects、persons 和 evidence 路径。

## 页面

- 总览：指标、监控预览、最近事件、交付进度；
- 实时监控：视频源占位、视觉框、信号和机器人 adapter 占位；
- 事件中心：事件筛选、置信度、人工确认/驳回；
- 事件来源旁显示证据状态（fixture、已提供未验证、可回放或待解析）；
- 插件能力：插件状态与全局启停；
- 对象与人员：自定义对象和人员注册；
- 系统设置：数据源、场景和证据边界说明。

当前视频画面和机器人状态属于 Mock/接口占位，真实媒体播放和机器人协议等待工具链、老师文档和硬件资料验证。
