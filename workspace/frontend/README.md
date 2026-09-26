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

如果要让 Real 模式发现 Makerverse 在线直播会话，可额外配置：

```powershell
$env:VITE_MAKERVERSE_API_URL = "http://127.0.0.1:5000"
$env:VITE_MAKERVERSE_TOKEN = "仅放在本地环境，不提交到仓库"
```

页面会调用 `/lives/online` 和 `/lives/{id}/endpoint`。隐私监护页不会把发现到的原始媒体地址直接当作隐私画面播放；Real 模式只有在后续接入明确的骨骼/卡漫渲染输出后才显示监护画面，否则保持“隐私渲染流未接入”的 fail-closed 状态。

页面通过 `src/repository.ts` 的 `Repository` 接口访问数据，Mock/Real 切换不会散落在页面业务逻辑中。

Real 模式切换时会先清空上一数据源的事件、插件、对象和人员，再请求 `/health` 与首屏数据。连接状态会显示为“连接中”“Real API 在线”或“Real API 离线”；失败时保留空状态和简短错误原因，不把 Mock 数据当作 Real 数据展示。复核、插件启停、分析任务和登记操作在 Real API 未在线时会直接提示失败，不会回退到 Mock。

Real 模式创建分析任务后会按 `job_id` 轮询 `/api/v1/analysis/jobs/{id}`，直到 `completed`、`failed` 或 `stopped`，再刷新事件中心；这对应 AI API 的 `202 Accepted` 异步任务语义。

Makerverse 媒体边界在 `src/media.ts`：它归一化 `/lives/online` 与 `/lives/{id}/endpoint` 的 DTO，并区分 Mock、RTMP、RTSP、HLS 和 HTTP-FLV。当前只完成地址分类和接口边界，真实播放器需要在部署地址、CORS、鉴权和浏览器实测确认后再接入；详见 `workspace/docs/MEDIA_PLAYBACK_ADAPTER.md`。

AI 服务启动后，可以在另一个终端执行 `npm run smoke:real`，检查前端 Real API 所依赖的 health、plugins、events、objects、persons 和 evidence 路径。

## 页面

- 首页：保留原有总览能力；
- 隐私监护：当前重点页面。左侧“插件功能”可折叠，插件启停会同步控制监控画面中的检测提示、右侧插件卡片和最近动作时间线；
- 隐私显示仅提供“卡漫模式 / 骨骼模式”，人物做卡漫/骨骼呈现，物品仍按语义检测结果显示；
- 右侧“当前状态”固定存在，其他卡片由已启用插件动态生成，不再写死用药/物品模块；
- 最近动作时间线按当前事实和插件动态生成，数量不是固定 4 项；
- 事件中心：事件筛选、置信度、人工确认/驳回；
- 插件管理：插件状态与全局启停；
- 对象与人员：自定义对象和人员注册；
- 系统设置：数据源、场景和证据边界说明。

Mock 模式使用明确的演示场景来展示“真实环境背景 + 人物卡漫/骨骼 + 物品检测”的产品逻辑。Real API 在线不代表隐私渲染流已经可用；隐私监护页不会自动回退到原始视频。真实骨骼/卡漫视频输出、媒体播放器和机器人协议仍需后续按实际接口验证。
