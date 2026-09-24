# 部署与演示说明

## 1. AI 服务（本地）

```powershell
cd ai-engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
python -m visual_event_ai
```

默认监听 `127.0.0.1:8010`。首次运行会初始化本地 SQLite runtime；运行目录不应复制到最终提交包。

## 2. AI 测试

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
python -B -m pytest --basetemp=.codex-pytest-temp-deployment -p no:cacheprovider -q
```

截至 2026-09-24，当前源码和提交暂存包均已验证 `363 passed`。新回归覆盖关系/动作输入缺口后的 cooldown 复位、有限坐标运算溢出防护、超大 JSON 整数几何/置信度/阈值统一 ValueError、非整数/布尔/负抽帧参数拒绝、OpenCV 非有限/超范围 FPS/PTS fallback、帧差灰度/抽样框原帧坐标、bbox/区域有限边界及并发 job 状态隔离、极大关键点值不使帧任务失败与带冒号 ID 的关系冷却键隔离、注册 embedding/API 输入校验、无 ID 药品标签级候选去重、明确非人物主体/药品储存设施/药品说明书文档标签拒绝服药推理；另有 PrimitiveFact 身份 ID/置信度严格校验、运行中帧提取取消、JSONL 恢复坏行后的 observation gap 与连续段状态隔离回归；相同时间戳的移出/返回事实无论输入顺序都不会误推归还；终态锁、事件与 completed 状态原子提交以及完成任务幂等重跑也有回归覆盖。弃用警告来自当前 Python/FastAPI 组合，不改变测试结果；fixture/CPU 结果不代表真实模型性能。

## 3. 前端

```powershell
cd frontend
npm install
npm run dev
```

可选 `.env`：

```text
VITE_AI_API_URL=http://127.0.0.1:8010
VITE_MAKERVERSE_API_URL=
VITE_MAKERVERSE_TOKEN=
```

无 AI 地址时使用 Mock；配置 AI 地址后切换 Real。Makerverse 地址为空时 Monitor 明确显示待接入。

## 4. 演示路径

1. 打开 Dashboard，确认插件、事件和证据卡片；
2. 切换场景并进入 Monitor；
3. 点击“运行一次事件分析”，等待 Real job 轮询或观察 Mock 事件；
4. 在 Events 使用关键词/状态筛选，打开详情抽屉；
5. 查看事实、时间窗和 resolver 状态，确认或驳回 pending 事件；
6. 在 Plugins 切换插件，重新运行任务观察事件变化；
7. 在 Registry 登记对象/人员，验证列表和 API 契约。

## 5. Real API smoke

AI 服务启动后，在前端目录执行 `npm run smoke:real`。这只检查 HTTP adapter，不验证浏览器视觉交互、CORS、HLS、Makerverse 或机器人。

## 6. 可选区域配置

服务可通过环境变量 `AI_ZONES_JSON` 配置区域矩形。每项包含 `zone_id`、`label`、`x`、`y`、`width`、`height`，坐标须与 detector bbox 共用帧像素坐标系；未设置时默认为空数组，不产生区域事实。配置错误会在启动时失败。当前没有真实摄像头区域坐标，部署前需要现场校准。

## 7. 外部部署

真实部署需要 .NET SDK、Cargo、FFmpeg、Makerverse/livestream-rs 配置、媒体存储、鉴权/CORS、模型权重、机器人资料和安全审批。凭据只能放在本地密钥或环境变量中。
