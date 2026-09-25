# Development Direction

Status: ACTIVE  
Control mode: USER-LED / MANUAL DISPATCH  
Owner: user  
Master role: planning, repository state management, task design, review, merge and truthfulness control  
Codex role: bounded implementation and verification

---

## 1. Working model

This project is no longer fully autonomous.

The workflow is:

```text
User chooses direction
  -> ChatGPT Master checks repository
  -> Master writes one large bounded Task Packet
  -> Codex implements + verifies + opens one PR
  -> User asks Master to review
  -> Master reviews/merges or returns precise fixes
  -> STOP
  -> wait for user to choose/approve next direction
```

Master must NOT automatically dispatch the next major task after a successful review unless the user explicitly says something equivalent to:
- continue;
- next;
- keep going;
- do the next stage;
- proceed with the plan.

Master may maintain a roadmap and suggested next tasks, but the user retains phase-transition authority.

---

## 2. Task sizing policy

Default Task Packets should be substantial enough that the user can leave and do other work.

### Normal target

- approximately **60–180 minutes** of meaningful implementation/verification;
- usually **3–6 tightly related subgoals**;
- one coherent architectural boundary;
- one branch;
- one PR;
- one final verification pass;
- one Master review.

### Prefer bundling

Bundle work when subgoals:
- touch the same architectural area;
- share the same tests;
- naturally depend on each other;
- can be reviewed as one coherent change.

Examples:
- provider + integration + tests + docs;
- frontend page + state model + API adapter + empty/error states;
- timeline UI + filters + detail drawer + evidence status;
- privacy visualization + skeleton rendering + settings + truthful labels.

### Split only when

Split a task if:
- a human decision is required;
- an external dependency is missing;
- a model/hardware asset is unavailable;
- a risky public contract would otherwise make review too broad;
- one subgoal could invalidate all later work;
- the resulting PR would become too difficult to audit.

Codex should not stop after a tiny helper if the remaining package is locally implementable.

---

## 3. Current phase — AI Finalization

Current target:
- finish TASK-0010;
- Master reviews it only when the user asks;
- if accepted, set `AI_ALGORITHM_FROZEN`.

AI freeze means:
- public AI contracts are stable enough for frontend integration;
- future AI changes are bug fixes or explicit new requirements;
- frontend work may rely on the documented contracts.

AI freeze does NOT mean:
- custom medicine detector accuracy has been proven;
- robot/hardware integration is complete;
- real-world benchmark metrics exist.

---

## 4. Next major phase — Frontend

After AI freeze, frontend becomes the primary development focus.

The frontend should not be a generic admin panel. It should visibly demonstrate the AI capabilities and the privacy/visual-memory story.

### F1 — Product shell and information architecture

Build a clean competition-demo shell with:
- clear navigation;
- scenario/plugin switch;
- global AI/source/provider status;
- Real vs Mock state clearly distinguished;
- loading/offline/error states;
- consistent visual language;
- responsive layout.

Main sections should converge toward:
- Overview / Dashboard;
- Live / Monitor;
- Event Center;
- Visual Memory;
- Medication Review;
- People / Objects;
- Plugins / Scenarios;
- Settings / Privacy / Providers.

Do not build decorative pages with no real data contract.

### F2 — Skeleton privacy visualization

Implement the user-visible privacy story:
- consume canonical COCO17 skeleton data;
- render a clean skeleton or cartoon/avatar layer;
- never imply that physical camera-side RGB deletion is verified when it is not;
- provide clear privacy-mode labels;
- distinguish:
  - current/local RGB -> pose -> skeleton;
  - target edge skeleton-only mode.

The UI may use a stylized avatar, but it must remain driven by skeleton/keypoint state rather than fabricated generative animation.

### F3 — Visual Memory experience

Make the generic memory capability visible:
- searchable object list;
- last-known location;
- last-seen timestamp;
- source/camera;
- confidence/provenance;
- object history/timeline;
- candidate handling for same-label objects;
- explicit unknown/unresolved state.

The UI must not merge separate identities just because labels match.

### F4 — Recent action / event experience

Expose temporal visual memory:
- recent actions;
- person/object-scoped timeline;
- action type filters;
- source and continuity segmentation;
- hand_near_object;
- hand_to_face;
- pickup_candidate / putdown_candidate;
- zone transitions;
- evidence details.

Use wording that preserves candidate/observation semantics.

### F5 — Medication review experience

Expose reviewable medication assistance:
- suspected medication event;
- configured medication plan;
- plan_match_candidate;
- early_candidate;
- late_candidate;
- wrong_item_candidate;
- unresolved_candidate;
- source/time/evidence details;
- human confirmation/rejection.

Never display these cues as medical certainty.

### F6 — Event/evidence workflow

Polish:
- event filters/search;
- review state;
- event details;
- evidence resolver status;
- playback link only when evidence is truly available;
- human confirm/reject;
- empty/error/loading states;
- clear timestamps/source identity.

### F7 — Demo mode

Provide a deterministic demo path so the project can be shown even without all real backend/hardware dependencies.

Demo mode should:
- use truthful fixture/mock data;
- clearly say it is demo/fixture data;
- exercise the same frontend contracts as Real mode;
- show the core story end-to-end:
  skeleton/privacy -> object/action -> memory -> event/review.

No fake Real labels.

---

## 5. Integration phase

Only after the frontend demonstrates the AI contracts cleanly:

### I1 — Existing backend adapter validation

Validate the already intended reuse boundaries:
- Makerverse for business/live/session context;
- livestream-rs for media;
- AI service remains independent;
- avoid backend rewrites.

### I2 — Evidence/playback integration

Connect evidence references to available media endpoints where contracts support it.

Never duplicate the video archive inside the AI service.

### I3 — Optional robot handoff

Only define or consume robot integration contracts if teammates provide a concrete interface.

Our AI/frontend scope should expose actionable structured information, not take ownership of ROS/robot control.

---

## 6. Competition presentation direction

The competition-facing story should emphasize:

### Core innovation 1 — privacy-aware skeleton perception

```text
RGB at perception boundary
  -> skeleton
  -> upper AI works on semantic/structural data
```

Target future mode:
```text
camera/edge -> skeleton only -> upper AI
```

Do not claim hardware-side privacy verification unless later proven.

### Core innovation 2 — visual memory

The platform remembers:
- where an object was last seen;
- when it was seen;
- what interactions happened recently;
- what source/continuity segment the evidence belongs to.

### Core innovation 3 — generic action reasoning

Low-level actions are scene-independent:
- hand_near_object;
- hand_to_face;
- pickup_candidate;
- putdown_candidate;
- motion;
- zone transitions.

Scene logic composes them later.

### Core innovation 4 — reviewable medication assistance

The system provides evidence and review cues instead of pretending to make medical decisions.

---

## 7. Future extensions — not current commitments

Keep these as clearly separated future work unless the user explicitly promotes one into scope:
- ByteTrack/Kalman tracker adapter;
- gait identity;
- cross-camera ReID;
- 2S-AGCN/GNN abnormal-action classifier;
- audio fusion;
- richer pose models;
- custom medicine/tool training;
- edge-camera skeleton-only deployment;
- pi0.5/MoMaGen manipulation;
- robot navigation/grasp execution.

---

## 8. Definition of done by phase

### AI done

AI is done when:
- TASK-0010 passes Master review;
- final AI report exists;
- public frontend-facing AI contract exists;
- full suite + curated verifier pass;
- truthfulness audit passes;
- Master explicitly marks `AI_ALGORITHM_FROZEN`.

### Frontend done

Frontend is done when:
- the core AI story is visible and understandable;
- Real/Mock/error/offline states are truthful;
- skeleton/privacy visualization works;
- visual memory is usable;
- action timeline is usable;
- medication review is usable;
- event/evidence review is usable;
- deterministic demo path works;
- production build passes.

### Our responsibility done

Our responsibility is complete when:
- AI is frozen;
- frontend is polished and integrated with the stable AI contract;
- evidence/demo flow is coherent;
- AI/frontend documentation is competition-ready;
- remaining robot/hardware items are clearly handed off rather than silently assumed complete.

---

## 9. Master planning rule

When the user says “continue”, Master should:
1. read current remote state;
2. review pending PR first if one exists;
3. if review passes, merge it;
4. stop if the user only requested review;
5. if the user requested continued development, create the largest safe coherent next Task Packet from this roadmap;
6. prefer a complete vertical slice over small utility tasks;
7. never broaden into teammate-owned robot/hardware scope without user instruction.

This document is the durable development direction unless the user later changes it.
