# Project Goal

## Product goal

Build a truthful, reviewable visual-event AI platform for the competition project.

Our responsibility is deliberately limited to:

1. **AI algorithm layer**
   - privacy-aware skeleton perception;
   - semantic person/object perception;
   - tracking and spatial relations;
   - reusable action primitives;
   - object-location memory;
   - temporal visual memory;
   - medication-assistance review cues;
   - scene/plugin reasoning;
   - stable evidence/event contracts.

2. **Frontend layer**
   - present AI state truthfully;
   - visualize skeleton/privacy output;
   - show object last-known location and recent actions;
   - show medication review cues;
   - provide event review/evidence UX;
   - expose provider/source/online/offline state;
   - support scene/plugin switching;
   - produce a polished competition-demo experience.

## Explicitly outside our ownership

Unless the user later changes scope, we do NOT own:
- robot chassis/navigation;
- manipulator/grasp execution;
- ROS hardware control;
- UWB/audio/thermal/event-camera hardware integration;
- gait/ReID implementation;
- trained 2S-AGCN/GNN fall/violence runtime;
- pi0.5/MoMaGen robot policy integration;
- teammates' unrelated competition modules;
- fabricated dataset/model/hardware metrics.

We may define integration interfaces or future-work boundaries for these, but we do not implement or claim them as completed.

## Core product story

```text
Camera / Video / Skeleton Input
  -> Privacy + Quality Boundary
  -> Person Pose + COCO17 Skeleton
  -> Semantic Object Detection
  -> Tracking
  -> Spatial Relations
  -> Generic Action Primitives
  -> VisualMemory
  -> TemporalVisualMemory
  -> Scene / Medication Reasoning
  -> Reviewable Events
  -> Frontend
```

The generic AI core should answer practical questions such as:
- Where was this object last seen?
- What happened recently around this person/object?
- Was there a reviewable medication-related sequence?
- Does observed medicine/time appear compatible with a configured plan?
- What evidence supports the event?

## Truthfulness rule

DONE means implemented behavior + evidence, not merely code presence or test count.

Never claim:
- medical certainty;
- swallowing/dose correctness inferred from vision;
- cross-camera physical identity without ReID evidence;
- model accuracy that was not measured;
- hardware privacy that was not physically verified;
- robot behavior that is outside this repository.

## Final project destination

The desired end state is:

```text
AI_ALGORITHM_FROZEN
  -> polished frontend
  -> AI/frontend integration
  -> demo/evidence polish
  -> competition-ready AI + frontend package
```

The user remains the product owner and decides when to change direction, expand scope, or move to the next major phase.
