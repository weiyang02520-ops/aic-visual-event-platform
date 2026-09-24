# Project Specification — AIC Visual Event Platform

## Summary
Competition-oriented visual-event AI platform: convert video observations into reviewable structured events. Reuse Makerverse/livestream-rs as existing foundations; focus this repository on AI, frontend, evidence linkage and final competition-document integration.

## Scenarios
- Primary: elderly-care assistance, especially suspected medication-related behavior; never medical diagnosis.
- Secondary: workshop/lab object taken/returned/last-seen.
- Future: robot/smart-home execution; robot control is not a current requirement.

## Deliverables
Independent Python AI service; plugin scene layer; multi-scenario frontend with Mock + Real AI adapter; evidence/review boundaries; clean submission; technical material for teacher/robot document fusion.

## Current Baseline
As of 2026-09-24, local software baseline exists with frame sources, CPU/fixture detection, centroid tracking, relations, temporal reasoners, plugins, SQLite, REST API, privacy guards and quality gate. 363 tests and VERIFY_OK are recorded. Real pose/object model runtime, real-camera metrics and robot validation are not proven.

## Core Requirements
AI remains independent Python; generic facts stay separate from scene plugins; plugins auto-discover/multi-run/global-toggle; unified events; store evidence references rather than duplicate video; treat existing backends as integration targets; custom objects; frontend Mock + Real; no fabricated metrics; clean submission; GitHub-persisted automation state.

## Non-Goals
Backend rewrites; ROS2/SLAM/navigation/grasping; production identity recognition; model-training platform; Kubernetes redesign; visual rule editor; medical diagnosis.

## Milestones
M0 baseline/bootstrap; M1 real vision; M2 frontend/AI integration; M3 backend evidence integration; M4 competition docs/LaTeX; M5 submission/report.

## Human Intervention
Only for teacher/final-track/robot documents, credentials/paid services, irreversible external actions or major scope changes. Ordinary technical choices belong to Master/Codex.
