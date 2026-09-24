# 媒体播放与 Makerverse 边界适配器

日期：2026-09-22  
状态：代码边界已实现，真实部署联调未完成

## 1. 目的

前端不能把“拿到了一个直播对象”误认为“浏览器已经能播放视频”。本适配器把 Makerverse 的直播 DTO 统一成前端 `LiveSession`，再根据 URL 类型给出明确的播放能力和证据状态。

适配器只负责：

1. 请求 Makerverse `GET /lives/online` 和 `GET /lives/{id}/endpoint`；
2. 兼容 ASP.NET 默认 PascalCase 与网关 lowerCamelCase；
3. 展平 `PlaybackEndpoints` 中的 `RtmpUrl`、`HttpFlvUrl`；
4. 分类 `mock://`、RTMP、RTSP、HLS、HTTP-FLV 和未知地址。

它不负责伪造直播地址，也不把未验证的地址显示为“可回放”。

## 2. 已核对的 Makerverse 契约

源码快照中的 `LiveService/Controllers/LivesController.cs` 提供：

| 接口 | 返回/用途 |
|---|---|
| `GET /lives/online` | 返回在线直播业务对象 `Live[]`，只包含 `id/title/status` 等业务字段 |
| `GET /lives/{id}/endpoint` | 返回 `LivestreamEndpointDto`，包含 `IngestUrl`（视权限可能为空）和 `PlaybackEndpoints` |
| `GET /lives/{id}/segments/index.m3u8` | LiveService 的 HLS playlist 路径，是否可访问仍需真实部署验证 |

快照中的 DTO 形状为：

```json
{
  "IngestUrl": "rtmp://host/lives/id",
  "PlaybackEndpoints": {
    "RtmpUrl": "rtmp://host/lives/id",
    "HttpFlvUrl": "http://host:8081/live/id.flv"
  }
}
```

实际 JSON 是否使用 PascalCase、是否经过网关重写，以及主机、端口、鉴权和 HLS 路径，必须以运行中的部署为准。前端不硬编码快照中的端口。

## 3. URL 分类规则

| 类型 | 浏览器原生 `<video>` | 当前处理 |
|---|---:|---|
| `mock://...` | 否 | 仅离线演示，明确显示 Mock |
| `rtmp://...` | 否 | 作为 ingest/playback 元数据保留；需要网关或播放器 |
| `rtsp://...` | 否 | 需要服务端转码/网关，不能直接塞给浏览器 |
| `.m3u8` 或 `/hls/` | 取决于浏览器 | 标记为 HLS，后续接原生 HLS 或 HLS.js |
| `.flv` 或 `/flv/` | 否 | 标记为 HTTP-FLV，后续接 flv.js 或兼容播放器 |
| 其他 | 未知 | 显示“未知媒体”，不宣称可播放 |

当前前端只完成地址分类和边界适配，没有把 HLS.js、flv.js 或 WebRTC 播放器偷偷加入依赖。这样可以先完成接口和证据契约，再根据老师提供的部署地址选择真正的浏览器播放器。

## 4. 代码位置与接入示例

- 类型：`workspace/frontend/src/types.ts` 的 `LiveSession`、`PlaybackState`；
- 适配器：`workspace/frontend/src/media.ts` 的 `normalizeLiveSession`、`createMakerverseLiveAdapter`、`classifyPlaybackUrl`；
- 监控页：`workspace/frontend/src/App.tsx` 的 `MonitorLive`；
- 样式：`workspace/frontend/src/styles.css` 的 `.media-status`。

接入真实网关时：

```ts
const makerverse = createMakerverseLiveAdapter(
  import.meta.env.VITE_MAKERVERSE_API_URL,
  import.meta.env.VITE_MAKERVERSE_TOKEN,
);
const sessions = await makerverse.listOnline();
const session = sessions[0] && await makerverse.getEndpoint(sessions[0].id);
const playback = session && choosePlayback(session);
```

上述代码只能在真实地址、认证策略、CORS 和直播状态均已确认后启用。Real 模式监控页会在配置 `VITE_MAKERVERSE_API_URL` 后主动调用这两个接口；未配置、请求失败或没有在线直播时显示明确原因，而不是显示虚构视频。

## 5. 真实联调清单

- [ ] 老师/部署方提供 Makerverse API 基址、鉴权方式和 CORS 规则；
- [ ] `GET /lives/online` 返回至少一个在线 `Live`；
- [ ] `GET /lives/{id}/endpoint` 返回播放端点，记录原始 JSON；
- [ ] 用浏览器网络面板确认 HLS/HTTP-FLV 请求、状态码和跨域响应；
- [ ] 确认直播时间轴与 AI 事件 `started_at/ended_at` 能对齐；
- [ ] 播放器实测后才把前端证据状态从“已提供·未验证/待解析”改为“可回放”；
- [ ] 将真实地址、token、机器人局域网信息放入本地 `.env` 或部署密钥，不提交到仓库。

## 6. 当前证据结论

本地已通过 TypeScript 编译和 Vite production build，证明适配器边界、DTO 归一化和页面占位可打包。当前没有 Makerverse 运行实例、真实媒体 URL、FFmpeg/livestream-rs 联调结果或浏览器播放验收，因此不能声称“真实直播已接通”。
