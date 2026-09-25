# AI Algorithm Finalization Plan

Status: ACTIVE  
Scope: AI algorithm only. Frontend feature expansion is paused until AI_ALGORITHM_FROZEN.

## Goal

Finish and freeze a coherent, privacy-aware visual-memory AI stack for the competition project.

The final algorithm story is:

```text
Video / Camera
  -> pose / skeleton perception
  -> person + object detection
  -> tracking
  -> spatial relations
  -> action primitives
  -> temporal visual memory
  -> reviewable scene events
```

The same generic fact/memory core should support medication assistance and object-location / forgotten-action use cases without making the scene plugins own raw camera/model logic.

## Scope decisions

### Required before AI freeze

1. Canonical skeleton/keypoint contract and skeleton-first privacy boundary.
2. Detection/tracking state suitable for person + object continuity.
3. Generic action primitives over skeleton + object geometry.
4. Visual-memory state for object location / recent action history.
5. Temporal reasoning built from generic facts, with medication and object-memory scenarios as consumers.
6. Final algorithm audit: inputs/outputs, formulas, thresholds, state machines, complexity, failure/degradation rules, alternatives and limitations.
7. Full source tests and curated VERIFY_OK.

### Explicitly not required for AI freeze

- collecting a real dataset;
- reporting project mAP / F1 / HOTA / IDF1;
- gait identity recognition;
- trained 2S-AGCN/GNN violence/fall classifier and audio-fusion runtime;
- pi0.5 or other robot manipulation policy;
- robot execution/control;
- cartoon-avatar frontend rendering;
- frontend visual redesign;
- production deployment.

These may be documented as future extensions, but must not be represented as implemented.

## Work packages

### A1 — Skeleton-first core
Status: COMPLETE after TASK-0006 (canonical COCO17 + skeleton-only upper-pipeline contract).
- canonical COCO17 keypoint names/schema;
- full-keypoint normalization from the real Ultralytics pose adapter;
- validated skeleton observation helper/contract;
- skeleton-only upper-pipeline regression proving raw RGB is not required after pose extraction;
- preserve existing nose/wrist medication-action semantics.

### A2 — Detection, tracking and object memory
Status: COMPLETE after TASK-0007 (generic object_in_zone + conservative VisualMemory identity boundary).
- audit current Centroid/Hungarian tracker and object continuity;
- define object state / last-known-location memory independent of scene plugin;
- only add a new tracker adapter if it materially improves architecture without forcing dataset claims;
- document ByteTrack/Kalman as an alternative if not implemented.

### A3 — Generic action primitives
Status: COMPLETE after TASK-0008 R1/R2 (scene-independent hand/object and hand/face primitives with medication compatibility isolated above the generic layer).
- normalize reusable skeleton/object actions such as hand_near_object, object_picked/carried/put_down and hand_to_face;
- keep confidence, source, UTC timestamp and continuity segment provenance;
- avoid scene-specific conclusions at this layer.

### A4 — Competition-document AI alignment
Status: ACTIVE.

#### A4.1 — Real semantic object perception
Status: ACTIVE via TASK-0009 v2.
- preserve the proven person/pose path;
- add a real-model-compatible semantic non-person object provider;
- combine person skeleton + semantic objects into the existing tracker/relation/action/memory pipeline;
- support custom medicine/tool labels by contract without claiming trained custom weights.

#### A4.2 — Temporal visual memory
Status: PENDING after semantic object perception.
- maintain queryable recent object-location and action-history state;
- medication and object-memory plugins consume generic facts/memory;
- do not merge evidence across source, discontinuity or incompatible identities.

#### A4.3 — Schedule-aware medication review logic
Status: PENDING after temporal memory.
- accept a deterministic JSON medication-plan contract;
- compare observed medication identity/time against the configured plan;
- emit only reviewable plan-match / early / late / wrong-item / unresolved cues;
- never infer dosage ingestion or medical correctness from vision alone.

#### A4.4 — Skeleton abnormal-action extension boundary
Status: DOCUMENTED EXTENSION, not an AI-freeze implementation requirement.
- reserve a provider/interface boundary for skeleton-sequence classifiers such as 2S-AGCN;
- current implementation must not claim fall/violence accuracy or audio-fusion capability without model/data evidence.

### A5 — Algorithm freeze
- audit dead/redundant/test-only paths;
- update algorithm architecture/design/completion documents to current real-pose runtime state;
- record formulas, parameters, decision logic, complexity, alternatives, failure cases and future work;
- final verification;
- mark AI_ALGORITHM_FROZEN only when all required work packages are accepted.

## Freeze rule

After A5 passes, AI architecture and public contracts are considered frozen for frontend integration. Any later AI change must be a concrete bug fix or a separately approved new algorithm requirement.
