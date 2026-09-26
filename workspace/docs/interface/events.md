# Events Contract

## UnifiedEvent

Required fields: `event_id`, `plugin_id`, `plugin_version`, `event_type`, `title`, `description`, `source_id`, `started_at`, `ended_at`, `confidence`, `severity`, `review_status`, `evidence`, `facts`, `metadata`.

Optional fields: `schema_version`, `created_at`, `subject`, `object`, `location`.

`severity` values: `info | low | medium | high`. `review_status` values: `pending | confirmed | rejected`.

## PrimitiveFact

Required: `fact_type`, `timestamp`, `confidence`. Optional: `subject`, `object`, `location`, `metadata`. `metadata.source_id` and `metadata.continuity_segment` carry provenance when present.

The frontend must preserve unknown metadata for detail views and must not use label equality as identity.

## EvidenceRef

`status` may be `available`, `fixture`, `provided_unverified`, `unavailable`, `unsupported` or `designed`. Playback controls appear only when `status=available` and `uri` exists.
