# Provider and Health Contract

## GET /health

Returns `{ status, service?, version? }`.

## GET /ready

Returns `ready`, `status`, `database`, `plugin_manager`, `detector`, `tracker`, `plugins`. `status=degraded` is a valid response and must remain visible in the UI.

## GET /api/v1/providers/detectors

Each row returns `provider_id`, `version`, `available`, `selected`, optional `reason`, `model_path`, `object_model_path`, `component`, `pose_available`, `object_available`, `object_reason`. Optional object provider availability does not imply pose failure.

## Source inspection

`GET /api/v1/sources/inspect?source=...` returns `source_id`, `kind`, `provider`, `status`, `uri`, `capabilities`, optional `reason`. Configured is not the same as connected.
