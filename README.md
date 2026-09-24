# AIC Visual Event AI Platform

面向 AIC 算法创新赛的视觉事件 AI 软件开发仓库。当前仓库保存可复现的 AI 代码、测试、算法文档、提交暂存包和 Codex 长期状态，便于 Codex、ChatGPT 与人工共同检查、修改和审查。

## 当前阶段

当前是 **AI 软件基线与规则链阶段**：

- 帧输入、CPU/fixture detector、基础跟踪、关系事实和场景插件已经接通；
- 养老辅助服药序列、工作室物品状态和证据引用规则已经有本地回归；
- 隐私 metadata 脱敏和可选 `channel_quality` 软件质量门控已经接入；
- 最新源码与提交暂存包均为 `363 passed`，`workspace/submission/VERIFY.ps1 -SkipFrontendBuild` 返回 `VERIFY_OK`；
- 结果属于 Mock、JSONL fixture、CPU baseline 和本地 API 证据，不代表真实模型准确率或机器人实机结果。

## 目录结构

当前保留原有 `workspace/` 布局，不为了 GitHub 强行重构：

```text
workspace/
├── ai-engine/       # AI 服务源码、插件、测试和本地运行配置
├── frontend/        # React/Vite 控制台源码；依赖和 dist 不入库
├── docs/            # AI 架构、算法、竞赛规则对齐和验证文档
└── submission/      # 阶段性提交暂存包和 VERIFY.ps1
agent-state/         # Codex 长期状态、事实、决策、测试证据和任务日志
```

未公开的 PDF、DOCX 比赛资料、原始参考作品、第三方源码快照、运行数据库、模型权重、Node 依赖和 rollback 备份默认不上传。相关本地资料的整理笔记保存在 `workspace/docs/`。

## AI 部分如何运行

进入 `workspace/ai-engine/` 后：

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q --basetemp "C:\path\to\aic-visual-event-platform\workspace\ai-engine\.codex-pytest-temp"
```

实际使用时应把 `--basetemp` 换成当前工作树下的绝对路径，并在验收后删除该临时目录。AI 服务入口、环境变量和 provider 说明见：

- `workspace/ai-engine/README.md`
- `workspace/docs/AI_ALGORITHM_DESIGN.md`
- `workspace/docs/MODEL_PROVIDER_CONTRACT.md`

## 测试和验收

提交暂存包的统一检查：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild
```

该脚本检查必需文件、敏感/污染文件、AI 测试和项目内 pytest 临时目录。当前结果：`VERIFY_OK`、`363 passed`。

## `agent-state/` 的作用

`agent-state/` 是开发仓库的长期上下文，不是最终比赛提交材料。它保存：

- `MASTER_STATUS.md`：当前总状态和下一道闸门；
- `CURRENT_TASK.md`：当前任务范围和已完成检查点；
- `VERIFIED_FACTS.md`：已验证事实及证据边界；
- `TEST_EVIDENCE.md`：测试命令、结果和清理记录；
- `DECISIONS.md`：架构和范围决策；
- `TASK_LOG.md`、`CHANGELOG.md`：持续工作记录；
- `NEXT_SESSION.md`：下一次 Codex 会话的恢复入口。

最终比赛提交包禁止包含 `agent-state/`，但长期开发仓库保留它用于跨会话恢复和人工审查。

## `submission/` 的作用

`workspace/submission/` 是阶段性提交暂存包，用来检查：

- AI 源码和测试是否同步；
- 文档和报告是否同步；
- 敏感信息、缓存、运行数据库、依赖目录和模型权重是否被排除；
- `VERIFY.ps1` 是否能在干净边界内完成验收。

它不是最终比赛提交包。正式提交前仍需重新确认老师材料、作品名称、赛道、真实数据、模型指标和硬件证据。

## 当前真实能力边界

当前可以声称：

- 本地 AI 软件链路可运行；
- 输入、时间、来源、连续段、置信度和隐私 metadata 有明确契约；
- 服药和物品状态规则可以在 fixture/CPU 数据上复现；
- 任务取消、事件事务、review 状态和 API 契约有回归测试；
- 可选多模态质量 metadata 可以软件层降级或拒识。

当前不能声称：

- 真实姿态/目标检测准确率；
- 真实音频、热成像或事件相机融合；
- 相机源头骨骼化已经实现；
- 真实数据集 precision、recall、F1、IDF1、HOTA；
- 真实摄像头、直播或机器人联调通过；
- 比赛最终成绩或应用效果。

## 下一阶段

本仓库初始化完成后先暂停 AI 功能扩展。后续只有在获得授权模型、真实样本、明确输入契约或新的审查意见后，才继续 P0–P3 算法工作。机器人、硬件、相机标定和现场验收另行处理。

详细完成情况见 [`workspace/docs/AI_ALGORITHM_COMPLETION_REPORT.md`](workspace/docs/AI_ALGORITHM_COMPLETION_REPORT.md)。

