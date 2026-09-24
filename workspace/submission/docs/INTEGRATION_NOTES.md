# Integration Notes

## Current integration state

| Boundary | Current state | Next implementation step |
|---|---|---|
| AI ↔ local video | JSONL fixture provider verified; MP4 decoder pending | add optional FFmpeg/OpenCV provider when toolchain is available |
| AI ↔ livestream-rs | source and evidence boundary designed; transport/archive resolver not implemented | define `source_id`/timestamp/live_id/segment contract from deployment |
| AI ↔ Makerverse | designed, not implemented | add REST adapter with fixture responses |
| Frontend ↔ AI | Mock and REST provider implemented; API contract tests pass; evidence status visible | browser-level Real API review and deployment base URL config |
| Frontend ↔ Makerverse | source API known, runtime unverified | implement adapter after API contract smoke test |
| Frontend ↔ media playback | Mock visual monitor only; runtime unverified | add HLS/HTTP-FLV player adapter after stream test |
| AI ↔ robot | blocked by robot documents | extract protocol, camera source and status/task semantics |

## Stable contracts to freeze before real integration

### Source identity

Every AI job and event should carry:

- `source_id` — business camera/live identity;
- `source_kind` — file, url, rtsp, hls or makerverse-live;
- `live_id` — optional Makerverse/live-stream identifier;
- `started_at`/`ended_at` — UTC timestamps;
- `frame_time` or `source_pts` when available.

### Event identity

The frontend and adapters should only consume the unified event shape from the task plan:

- event/plugin IDs and schema version;
- event type/title/description;
- source and time window;
- confidence/severity/review status;
- subject/object/location;
- facts and metadata;
- evidence references.

### Evidence resolver

The first resolver can return a typed unavailable result. A real resolver must know:

1. how a live/event timestamp maps to HLS segment time;
2. how MinIO object keys and playlists are named;
3. whether the URL is directly public or needs a signed URL;
4. what the frontend shows when retention or clock skew prevents lookup.

Do not store a guessed URL in an event and call it verified evidence.

## Low-risk delivery order

1. Build AI schemas, SQLite events, plugin discovery and a deterministic Mock detector.
2. Build frontend pages against Mock provider and demonstrate the complete event/review flow.
3. Add AI REST provider and switchable Real mode.
4. Keep JSONL fixture analysis as the verified local path; add actual MP4/local file decoding only with an available provider and record evidence.
5. Add HLS/HTTP-FLV/RTSP adapters only after toolchains are available.
6. Add Makerverse adapter using the checked live API and actual deployment endpoints.
7. Add robot adapter only from the teacher-provided robot documentation.

## Known environment blockers

- No .NET SDK: Makerverse build/test cannot run here yet.
- No Cargo: livestream-rs build/test cannot run here yet.
- No FFmpeg executable/development libraries: media E2E and transcode verification cannot run here yet.
- No teacher main document in the project root at the time of this audit.
- No robot hardware/protocol document in the project root at the time of this audit.

## Integrity rules

- Existing source snapshots are read-only references; new code belongs in `workspace/ai-engine/` and `workspace/frontend/`.
- The final submission must not include agent-state, prompts, secrets, local absolute paths, temporary logs or unverified metrics.
- Any real integration failure is recorded as failed/blocked with evidence and a Mock/Null fallback where possible.
