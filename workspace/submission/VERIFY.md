# 提交包一键验收

在 Windows PowerShell 中从本目录运行：

```powershell
.\VERIFY.ps1
```

脚本会：

1. 检查核心源码、测试、材料包和 LaTeX 主文件是否存在；
2. 检查 `__pycache__`、`.pyc`、`node_modules`、`dist`、`.pytest_cache`、运行数据库、`.env` 和个人绝对路径；
3. 运行 AI `pytest` 回归并清理测试产生的 runtime；
4. 如果前端依赖已安装，运行 `npm run build` 并清理 `dist`；
5. 输出 `VERIFY_OK` 或明确失败原因。

提交包默认不包含 Node 依赖，因此首次验收前需要在 `frontend/` 执行 `npm install`。若只检查 AI 与清洁度，可使用 `.VERIFY.ps1 -SkipFrontendBuild`。

该脚本不会启动真实 Makerverse、livestream-rs 或机器人，也不会把 Mock/CPU 测试结果解释成真实部署证据。
