# 阶段性提交包清单

核验日期：2026-09-23

## 目录

- `ai-engine/`：独立 AI 服务源码、插件、测试和运行说明。
- `frontend/`：React/Vite 前端源码、Real API smoke 脚本和运行说明。
- `docs/`：架构、接口、算法边界、媒体适配和提交检查文档。
- `docs/TEMPORAL_EVENT_REASONING.md`：时序推理规则、输入事实要求和本地验证边界。
- `FINAL_REPORT.md`：当前阶段总结，明确已完成项和未验证项。
- `LICENSES.md`：第三方依赖清单。
- `VERIFY.ps1` / `VERIFY.md`：Windows 一键验收脚本与说明。
- `docs/REQUIREMENT_EVIDENCE_MATRIX.md`：计划要求与证据状态矩阵。

## 运行入口

```powershell
cd ai-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m pytest --basetemp=.pytest-temp -q
python -m visual_event_ai
```

另开终端：

```powershell
cd frontend
npm install
npm run build
npm run dev
```

## 实现类型

| 内容 | 类型 | 说明 |
|---|---|---|
| 统一事件、SQLite、REST、插件扫描/启停 | 真实本地实现 | 有源码测试和本地 HTTP smoke |
| Mock/JSONL/OpenCV fixture | 可运行测试实现 | 证明契约，不代表真实媒体性能 |
| motion_cpu detector、registry embedding | CPU baseline/heuristic | 可解释降级，不是训练模型准确率 |
| Makerverse DTO 与媒体 URL adapter | 真实适配代码 | 没有在线服务时不宣称播放成功 |
| ONNX provider | 安全占位 | 缺少 verified adapter 时保持 unavailable |
| Temporal event reasoners | 本地规则实现 | 已接入场景插件并通过 fixture 测试；真实动作/场景事实源待接入 |
| 机器人 adapter | 预留接口/材料占位 | 等型号、协议和实机资料 |

## 外部依赖

AI 需要 Python 和 requirements；前端需要 Node/npm；真实媒体链路还需要 .NET SDK、Cargo、FFmpeg、Makerverse/livestream-rs 部署、鉴权/CORS 和模型/数据。当前包不携带这些运行时、凭据或权重。

## 排除项

暂存包不包含 agent 状态、提示词、绝对路径、密钥、模型权重、运行数据库、Python 缓存、pytest 缓存、`node_modules`、Vite `dist` 或真实部署凭据。`docs/latex/` 是可继续融合的骨架，不代表官方模板已经确认。

## 完整性说明

这是 `STAGED_PROTOTYPE`，不是最终比赛提交包。待老师主文档、机器人资料、真实媒体/模型/实机证据到位后，必须重新生成清单、哈希和最终长篇文档。
