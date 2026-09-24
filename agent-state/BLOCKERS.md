# Blockers

## BLK-001 — teacher and robot documents not yet available

- Problem: 赛道最终选择、老师主文档、机器人硬件与通信协议尚未进入资料目录。
- Impact: 不能可靠确定最终场景、数据源、机器人接入方式和文档融合内容。
- Attempts: 已完成计划书审计、目录初始化、AI/前端原型、媒体 DTO 适配边界和提交暂存包；当前只差外部资料才能做最终融合。
- Workaround: 先保留通用视觉、插件化和 Mock/Real 边界，不虚构具体机器人实现。
- Need user: yes — 请把相关文档放入资料根目录。

## BLK-002 — runtime toolchain gaps

- Problem: 当前 PATH 没有 Cargo、FFmpeg、.NET SDK。
- Impact: 不能宣称 livestream-rs 构建、真实媒体解码或 Makerverse .NET 运行时已通过。
- Workaround: 已用 JSONL/Mock frame provider、CPU motion baseline、明确的 Real API/媒体适配边界和可替换 provider 继续主线；相关 provider 可在工具链到位后替换。

## BLK-003 — browser visual acceptance unavailable

- Problem: 当前没有可用的真实浏览器交互会话，无法对 Real API 点击、hash 前进/后退、事件详情回放入口、CORS 和响应式布局做视觉验收。
- Impact: 前端 TypeScript/Vite build 与 HTTP adapter smoke 已通过，但不能升级为浏览器视觉 PASS。
- Workaround: 已加入 hash 路由、条件式证据回放入口、loading/empty/error 文案和 `VERIFY.ps1`；待可用浏览器会话后按清单验收。

## BLK-004 — LaTeX compiler unavailable

- Problem: 当前 PATH 没有 XeLaTeX、LuaLaTeX 或 pdfLaTeX。
- Impact: 中文 LaTeX 骨架已创建并通过文件/括号结构检查，但未生成 PDF。
- Workaround: 保留不依赖官方模板的章节骨架；老师模板到位且编译器可用后再执行正式排版和 PDF QA。

## BLK-005 — AI temporal reasoning lacks semantic fact sources

- Problem: The project has no real pose/hand-keypoint model; motion_cpu only reports changed regions. KeypointActionExtractor can consume explicit detector metadata, but no built-in provider produces keypoints from real video. scene_observed is still absent. AnalysisService supports optional strict AI_ZONES_JSON rectangles, but the default zone list is empty and no real camera calibration coordinates exist.
- Impact: JSONL keypoint fixtures exercise the medication path and configured zone transitions are tested, but real cameras still lack pose evidence, calibrated regions, and scene observation facts. Scoped timeout and explicit-missing facts require the same zone; unscoped facts retain a global-coverage assumption that upstream must eventually verify.
- Workaround: Keep keypoint geometry and relation association strict, retain incomplete cues when keypoints are absent, validate detector/entity/zone inputs and numeric thresholds, reject malformed fixture rows/scores, use shared tracker label semantics, maintain per-object/per-zone state and region-scoped event dedup. Missing detections now clear relation position/near/zone continuity; malformed Boolean keypoint values cannot create action facts; the motion CPU baseline preserves fractional grayscale and rejects invalid pixel ranges.
- Need user: If a suitable real action/pose model, authorized sample, or camera calibration coordinates become available, confirm the model/protocol boundary; CPU/fixture algorithm audits can continue.
