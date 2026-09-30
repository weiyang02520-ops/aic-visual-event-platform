# Sentinel · AI 视觉机器人智能监护前端

面向老人用药辅助场景的 AI 视觉机器人平台前端。深色 “Robot OS” 界面，离线演示数据和真实 AI REST API 共用同一个 `Repository` 接口。

## 启动

```powershell
cd frontend
npm install
npm run dev      # http://127.0.0.1:5173
npm run build    # tsc -b + vite build
npm test         # node --test，覆盖场景引擎、推理解释、记忆索引
```

## 页面

| 路由 | 页面 | 内容 |
| --- | --- | --- |
| `#/dashboard` | AI 总览 | AI 核心状态、当前人物（卡漫头像）、当前事件与推理条、识别对象、系统状态、最近智能分析 |
| `#/monitor` | 隐私监护 | 由 COCO17 关键点驱动的卡漫人物，可切换卡漫 / 骨骼 / 融合；物品保留语义识别框；可播放、暂停、拖动的时间轴；人物状态、动作事实、识别对象、插件分析卡 |
| `#/events/:id` | 事件分析中心 | 事件卡片流 + 推理流程（发现人物 → 检测药盒 → 检测拿取 → 检测动作 → 生成判断），点击节点查看对应事实；判断卡、人工确认 / 驳回、证据状态 |
| `#/memory/:id` | AI 记忆库 | 药品 / 工具 / 生活用品画廊、最近已知位置、出现记录、认识的人；弹窗登记物品和人员 |
| `#/plugins` | 插件中心 | 平台能力架构图、已安装插件（输入事实 / 输出 / 今日事件 / 启停）、规划中的插件（标注尚未实现） |
| `#/demo` | 演示模式 | 全屏 6 幕：人物出现 → AI 识别 → 物品发现 → 动作分析 → 事件生成 → 智能提醒。`#/demo/15` 从第 15 秒开始 |
| `#/settings` | 系统设置 | 数据源、运行状态、隐私边界 |

演示模式快捷键：空格 播放 / 暂停，← → 切换幕，R 重播，F 全屏，Esc 退出。演示数据模式下，“事件生成”一幕会通过 Repository 写入一条事件，结束后可直接跳到事件分析中心查看。

## 数据源

顶部 “演示 / 实时 API” 切换数据源。

- 演示：`src/api/mockAdapter.ts` 的内存数据，加上 `src/engine/scene/mockScript.ts` 的 26 秒服药剧本。界面明确标注为演示数据，不代表模型输出。
- 实时 API：`VITE_AI_API_URL`（默认 `http://127.0.0.1:8010`）。切换时先清空旧数据；离线时保持空状态并显示原因，不回退到演示数据。额外读取 `/ready` 和 `/api/v1/providers/detectors` 展示运行状态。
- 实时隐私舞台：配置 `VITE_AI_PREVIEW_SOURCE` 后读取 `/api/v1/vision/preview`，只使用 `metadata.skeleton.keypoints` 和物品 bbox 渲染。未配置或失败时舞台保持关闭，**不会回退到原始视频**。

```powershell
$env:VITE_AI_API_URL = "http://127.0.0.1:8010"
$env:VITE_AI_PREVIEW_SOURCE = "runtime/samples/task-0004-bus.avi"
npm run dev
```

## 演示环境照片

卡漫化只针对人物，房间和物品保持原样。演示模式的背景是一张**没有人的实拍房间照片**，卡通人物叠在上面，物品只加识别框。

1. 拍一张演示房间的照片（茶几上放药盒、水杯，画面里不要有人），保存为 `public/demo-scene/living-room.jpg`。
2. 复制 `public/demo-scene/scene.example.json` 为 `scene.json`，按照片像素填：`width`/`height` 是照片尺寸，`floorY` 是人站的位置（脚底）的纵坐标，`objects` 是各物品的 `[左, 上, 宽, 高]`（`obj-01` 药盒必填，`obj-04` 水杯、`obj-06` 老花镜可选）。
3. 刷新页面。人物会自动按药盒和地面位置缩放，伸手正好落在药盒上。

没有 `scene.json` 时背景是中性网格，界面上会标注“未放环境照片”。

## 目录

```
src/
  app/       App、hash 路由、RuntimeProvider（数据源与操作）、Shell
  design/    tokens / base / ui 样式与基础组件
  engine/    纯 TS：labels、explain（事件 → 推理阶段）、memory、scene（骨骼、姿态、剧本、真实预览映射）
  render/    SceneStage、CartoonAvatar、SkeletonLayer、RoomBackdrop、ObjectGlyph
  hooks/     场景时钟、实时预览、live scene
  pages/     各页面及样式
  api/ contracts/ plugins/   Repository 适配器、冻结契约、插件展示注册表
```

## 契约边界

- 事件文案保留“疑似 / 候选 / 需复核”，始终显示“辅助判断，不是医学诊断”。
- 只有证据状态为 `available` 且带 URI 时显示回放；其余只显示时间窗和状态。
- “最近已知位置”是历史记录，不代表物品此刻在该位置。
- 骨骼缺失关节时按关节逐段降级，不补画肢体。
