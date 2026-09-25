# TASK-0008 Master Review R1

Result: CHANGES_REQUIRED

PR: #9
Head reviewed: `cfcef17a8ce407cef3e8a39aebef57374de35449`

The overall refactor direction is correct, but two current acceptance items are not yet satisfied.

### Blocker 1 — `hand_near_object` is incorrectly gated by `hand_to_face`

In `GenericActionPrimitiveExtractor.extract()`, the wrist list is currently built only from wrists satisfying:

```python
face_distance <= face_radius
```

The object-distance loop then iterates only that list. Therefore a valid wrist that is close to an arbitrary object but far from the face produces no `hand_near_object`.

This violates AC-02 and the core scene-independent action contract.

Required narrow fix:
- evaluate every valid/confident wrist against non-person object bboxes for `hand_near_object`;
- evaluate wrist-to-face independently for `hand_to_face`;
- do not make object proximity depend on face proximity;
- preserve current medication compatibility behavior.

Required regression:
- person wrist far from nose/face but close to an arbitrary non-medication object => `hand_near_object` MUST be emitted and `hand_to_face` MUST NOT be emitted.

### Blocker 2 — missing actual continuity-gap regression

TASK-0008 requires that a continuity boundary does not reuse an old action episode. The new test `test_generic_extractor_does_not_reuse_old_episode_after_source_change` verifies a source switch, not a real `observation_gap` / continuity-segment transition.

The normal `FrameFactExtractor` already recreates action extractors on discontinuity, so this may be only a missing proof rather than a design rewrite.

Required narrow fix/evidence:
- add a deterministic `FrameFactExtractor` regression with a JSONL/provider discontinuity/observation gap;
- prove a valid post-gap action can emit as a fresh episode;
- prove no pre-gap action/object association is reused across the gap.

Do not broaden scope. No frontend, tracker replacement, new scene logic, model work, or new metrics.

After the fixes:
- rerun targeted action/fact/reasoner tests;
- rerun full AI suite;
- rerun curated VERIFY;
- update CODEX_REPORT/state and return the same PR #9 for R2 review.
