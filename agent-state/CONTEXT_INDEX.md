# Context Index

## Project root

`C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料`

## Primary task specification

- `..\Codex_Master_Execution_Plan_V5_FINAL.md`

## State files

- `USER_REQUIREMENTS.md` — requirements explicitly adopted from the handoff plan
- `VERIFIED_FACTS.md` — facts checked against files, repositories, or official sources
- `DECISIONS.md` — active architecture and scope decisions
- `ARCHITECTURE.md` — current implementation architecture only
- `MASTER_STATUS.md` — phase status and next gates
- `CURRENT_TASK.md` — the one active task
- `TEST_EVIDENCE.md` — reproducible verification evidence
- `BLOCKERS.md` — unresolved blockers
- `OPEN_QUESTIONS.md` — questions requiring teacher/robot/deployment inputs
- `NEXT_SESSION.md` — continuation instructions

## Current implementation notes

- `workspace/docs/AI_FRONTEND_PHASE1.md` — AI API and React/Vite console
- `workspace/docs/AI_FRAME_PIPELINE_PHASE2.md` — source/frame provider boundary
- `workspace/docs/AI_PROVIDERS_PHASE3.md` — detector/tracker baseline
- `workspace/docs/SCENE_PLUGINS_PHASE6_7.md` — elderly/workshop plugin states
- `workspace/docs/TEMPORAL_EVENT_REASONING.md` — reasoner rules, evidence requirements, thresholds, and current input gaps
- `workspace/docs/最终文档编排蓝图.md` — final long-form document structure and evidence boundary
- `workspace/docs/EVIDENCE_RESOLVER.md` — evidence status contract and verification limits
- `workspace/docs/API_CONTRACT.md` — current AI REST endpoint contract
- `workspace/docs/SUBMISSION_READINESS_CHECKLIST.md` — final delivery gates
- `workspace/docs/LOCAL_ANALYSIS_PIPELINE.md` — local frame-to-fact analysis chain
- `workspace/docs/MODEL_PROVIDER_CONTRACT.md` — model provider, fallback and ONNX boundary
- `workspace/docs/MEDIA_PLAYBACK_ADAPTER.md` — Makerverse DTO normalization, URL classification and real-player verification boundary
- `workspace/docs/REGISTRY_EMBEDDINGS.md` — registered object/person CPU embedding and similarity-match contract
- `workspace/docs/SUBMISSION_READINESS_CHECKLIST.md` — current software/cleanliness gates and external blockers
- `workspace/docs/当前实现与证据总览.md` — current deliverables, evidence levels, verification results and external gates
- `workspace/submission/FINAL_REPORT.md` — staged-prototype report for handoff
- `workspace/submission/MANIFEST.md` — staged package contents and exclusion rules
- `workspace/docs/COMPETITION_MATERIAL_PACK.md` — formal-stage competition narrative and fusion placeholders
- `workspace/docs/latex/main.tex` — compile-oriented Chinese LaTeX skeleton
- `workspace/docs/THIRD_PARTY_NOTES.md` — dependency purpose and license review notes
- `workspace/docs/REQUIREMENT_EVIDENCE_MATRIX.md` — requirement-by-requirement evidence and remaining external gates

## Workspace layout

```text
workspace/
├─ ai-engine/
├─ frontend/
├─ docs/
└─ submission/
```

The plan file and `agent-state/` stay outside `workspace/submission/` so development records do not enter the clean submission package.
