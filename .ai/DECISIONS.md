# Automation Decisions

## ADEC-001
Keep both state systems: `.ai/` is automation control; `agent-state/` is detailed history/evidence. Do not migrate/delete existing evidence.

## ADEC-002
First Worker task targets the smallest real-vision gap: optional person detection + pose keypoint provider adapter.

## ADEC-003
Use task branches + PR; Master reviews acceptance before merge; avoid concurrent direct main edits.

## ADEC-004
TASK-0001 offline adapter/integration tests must not require network/GPU/model download. Real model smoke is recorded separately when environment permits.
