# Job and Evidence Contract

## Analysis jobs

- `POST /api/v1/analysis/jobs` with `{ source, plugin_ids?, metadata? }` returns HTTP 202 and an `AnalysisJob`.
- `GET /api/v1/analysis/jobs` lists jobs.
- `GET /api/v1/analysis/jobs/{job_id}` returns one job.
- `POST /api/v1/analysis/jobs/{job_id}/stop` requests cancellation.

Job statuses are `queued`, `running`, `completed`, `failed`, `stopped`. The frontend must render terminal errors and never convert failure to completed.

## Evidence

`GET /api/v1/evidence/resolve?source_id=...&started_at=...&ended_at=...&uri=...` returns `source_id`, time window, `resolver`, `status`, optional `uri` and `reason`.
