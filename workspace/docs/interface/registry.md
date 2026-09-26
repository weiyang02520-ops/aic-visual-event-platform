# Registry Contract

## Objects

- `GET /api/v1/objects`
- `POST /api/v1/objects` with `{ name, description?, reference_uris?, embedding? }`
- `DELETE /api/v1/objects/{object_id}`

Response includes `object_id`, `name`, `description`, `reference_uris`, optional `embedding`, `status`, `created_at`. `reference_uris` are references; this v1 contract does not upload local files.

## Persons

- `GET /api/v1/persons`
- `POST /api/v1/persons` with `{ display_name, role?, reference_uris?, embedding? }`
- `DELETE /api/v1/persons/{person_id}`

## Registry match

`POST /api/v1/registry/match` accepts `kind` plus `embedding` or `gray`, and returns `registry_id`, `label`, `kind`, `similarity`, `accepted`. The CPU baseline is not cross-camera identity verification.
