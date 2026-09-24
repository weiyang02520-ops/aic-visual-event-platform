# Phase 0 审计报告

审计日期：2026-09-22

## 项目资料根目录

`C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料`

当前已建立：

- `workspace/ai-engine/`
- `workspace/frontend/`
- `workspace/docs/`
- `workspace/submission/`
- `workspace/source-snapshots/Makerverse/`
- `workspace/source-snapshots/livestream-rs/`
- `agent-state/`

## 工具链事实

| Tool | Result | Evidence |
|---|---|---|
| Git | available, 2.53.0.windows.2 | `git --version` |
| Python | available, 3.14.4 | `python --version` |
| Node.js | available, v24.15.0 | `node --version` |
| npm | available, 11.12.1 | `npm --version` |
| .NET host | installed, but no SDK found | `dotnet --version` reports no .NET SDKs |
| Cargo | missing from PATH | `Get-Command cargo` |
| FFmpeg | missing from PATH | `Get-Command ffmpeg` |

当前可以先推进 Python AI、TypeScript/Node 前端和静态文档；Makerverse .NET 构建、livestream-rs Rust 构建、真实媒体测试需要补齐 SDK/toolchain，并可能需要 Docker、FFmpeg 开发库和 MinIO 等外部依赖。

## 仓库基线

### Makerverse

- Source: `workspace/source-snapshots/Makerverse/`
- Remote: `https://github.com/Stars-sea/Makerverse.git`
- HEAD: `88423bc5e3b64dac1670180999b08e4cae36e5df`
- Working tree: clean
- Role: .NET Aspire business platform; AccountService, ActivityService, LiveService, SearchService, gateway and infrastructure orchestration.
- Key source anchors:
  - `Makerverse.AppHost/AppHost.cs`
  - `LiveService/Controllers/LivesController.cs`
  - `LiveService/Protos/livestream.proto`
  - `Makerverse.AppHost.Tests/`

### livestream-rs

- Source: `workspace/source-snapshots/livestream-rs/`
- Remote: `https://github.com/Stars-sea/livestream-rs.git`
- HEAD: `8b463533c5d218701482389dcdcf53eb18f5388f`
- Working tree: clean
- Version: workspace package `0.4.0`, Rust edition `2024`
- Role: media plane; RTMP/RTSP ingest, HTTP-FLV/RTMP playback, HLS TS/playlist persistence to MinIO/S3, gRPC control plane.
- Key source anchors:
  - `Cargo.toml`
  - `proto/livestream.proto`
  - `src/config.rs`
  - `crates/livestream-transport/`
  - `crates/livestream-pipeline/`
  - `crates/livestream-media/`

## Phase 0 outcome

- [x] Current project root and state files verified.
- [x] Source snapshots added without modifying upstream repositories.
- [x] Commit baselines recorded.
- [x] Toolchain limitations recorded.
- [ ] Build and runtime tests — blocked by missing .NET SDK, Cargo and FFmpeg.
- [ ] Teacher document and robot document audit — pending files.

## Execution decision

Continue with a standalone Python AI skeleton and a Mock-first frontend. Keep the existing repositories as read-only integration references until toolchains and teacher/robot documents are available. Do not claim real stream or hardware verification from this static audit.
