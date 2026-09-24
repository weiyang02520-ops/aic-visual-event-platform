# User Requirements

> 这些要求来自用户交接的长期任务计划书；若用户后续明确修改，以最新明确要求为准。

| ID | Requirement | Source | Status | Notes |
|---|---|---|---|---|
| REQ-001 | 后续项目工作目录为本资料文件夹 | user | active | 以本文件所在目录为项目资料根目录 |
| REQ-002 | AI 作为独立项目，Python 优先 | handoff plan | adopted | 不重写 Makerverse 或 livestream-rs |
| REQ-003 | 前端需要支持可完整演示的 Mock，并预留 Real API | handoff plan | adopted | 后端联调可后置 |
| REQ-004 | AI 采用通用视觉底座与可插拔场景能力 | handoff plan | adopted | 养老为主场景，工作室为辅助场景 |
| REQ-005 | AI 事件统一格式，保存事件与证据时间窗，不重复保存视频 | handoff plan | adopted | 不把“疑似”写成医学诊断或确定事实 |
| REQ-006 | 机器人是实际应用与后续融合方向，不是当前假设的完整控制系统 | handoff plan | adopted | 等老师和机器人文档确认协议与能力 |
| REQ-007 | 代码、测试、文档和提交包必须区分；不得伪造实验结果 | handoff plan | adopted | 未验证内容必须标注为设计目标、Mock 或待验证 |
| REQ-008 | 用户不参与普通技术选型，希望把任务交给 Codex 自主调查、实现、测试、整理和交付 | user/shared conversation | active | 只有外部资料、账号、付费、硬件权限或不可逆决定才需要打扰用户 |


## 2026-09-24 Automation collaboration update
- REQ-AUTO-001: GitHub is the shared long-term collaboration surface for ChatGPT Master and Codex Worker.
- REQ-AUTO-002: Important task state must be persisted in repository files; do not depend on long chat context.
- REQ-AUTO-003: Master plans/reviews; Codex executes bounded Task Packets; ordinary implementation details should not repeatedly interrupt the user.
