# 前端系统设计

## 1. 信息架构

前端为统一控制台，视图包括 Dashboard、Monitor、Events、Event Detail、Plugins、Registry 和 Settings。当前使用轻量 hash 路由（如 `#events`）保留刷新和浏览器前进/后退语义，不引入额外路由运行时。场景选择只影响展示文案和筛选，不复制后端算法；AI 插件全局状态与 UI 场景模式保持概念分离。

## 2. Repository 抽象

`Repository` 统一提供 health、插件、事件、复核、分析任务、对象和人员 API。Mock repository 使用确定性内存数据；Real repository 使用 `VITE_AI_API_URL` 请求 FastAPI。切换数据源时 App 先清空上一来源的数据，再并行请求 `/health` 和首屏资源；Real 请求失败进入 offline 状态并保留空列表，不回退到 Mock。分析任务在 Real 模式按 `job_id` 轮询终态后刷新事件，停止状态不会显示为完成。

## 3. Monitor 与媒体

Makerverse adapter 请求在线直播和 endpoint，归一化 PascalCase/lowerCamelCase DTO 及嵌套 `PlaybackEndpoints`。`classifyPlaybackUrl` 区分 HLS、HTTP-FLV、RTMP、RTSP、Mock 和 unknown。浏览器可直接播放的媒体类型才进入播放器；缺少基址、鉴权、在线直播、CORS 或可验证 URI 时显示明确原因。

当前没有真实 Makerverse 地址和浏览器网络验收，因此 Monitor 的 Real 播放状态仍是待接入/待解析。页面不伪造 HLS 地址、不显示虚假的“正在播放”。

## 4. 事件中心

事件表支持关键词、状态筛选、置信度、来源和证据状态。详情抽屉显示描述、事实、时间窗、来源、位置和 resolver 状态，并对 pending 事件提供确认/驳回。只有 evidence 状态为 `available` 且存在 URI 时才显示“打开证据回放”链接；证据没有可验证 URI 时，只显示时间窗与状态，不提供误导性回放链接。

## 5. 注册页

对象/人员页面提供名称登记和状态展示。当前 UI 保存名称与可选引用位；embedding 匹配 API 已在后端存在，但真实多图上传、质量门控、删除和隐私加密仍待数据与产品要求确定。

## 6. 状态与错误

所有 Real 请求都有 loading、空列表和 offline 错误状态。复核、插件启停、分析任务和登记操作在 offline/loading 时直接提示并停止，不会调用 Mock repository。Mock 事件明确标注为演示/fixture。机器人区域当前为 adapter 占位，不把尚未提供的型号、控制协议或动作能力写入界面。

## 7. 构建与验收

```powershell
npm install
npm run build
npm run dev
```

构建使用 TypeScript `tsc -b` 与 Vite。当前 build 已通过；浏览器点击、响应式截图和真实媒体网络面板需要真实浏览器会话与部署地址后补验。
