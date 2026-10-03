import assert from "node:assert/strict";
import test from "node:test";
import type { UnifiedEventContract } from "../../contracts";
import { toLegacyEvent } from "./mappers.ts";
import { BackendApiClient } from "./client.ts";
import { createEventsApi } from "./events.ts";

const event: UnifiedEventContract = {
  event_id: "evt-1",
  schema_version: "1.0",
  plugin_id: "workshop",
  plugin_version: "0.1.0",
  event_type: "object_removed",
  title: "Object removed",
  description: "An object left its zone.",
  source_id: "camera-01",
  started_at: "2026-01-01T00:00:00.000Z",
  ended_at: "2026-01-01T00:00:05.000Z",
  confidence: 0.9,
  severity: "medium",
  review_status: "confirmed",
  location: "workbench",
  evidence: [{
    source_id: "camera-01",
    started_at: "2026-01-01T00:00:00.000Z",
    ended_at: "2026-01-01T00:00:05.000Z",
    resolver: "makerverse-minio",
    uri: "/api/v1/events/evt-1/evidence",
    status: "available",
    reason: null,
  }],
  facts: [{ fact_type: "object_removed", confidence: 0.9, location: "workbench", metadata: { source_id: "camera-01" } }],
  metadata: { source_id: "camera-01" },
  created_at: "2026-01-01T00:00:05.000Z",
};

async function withFetch(handler: typeof fetch, run: () => Promise<void>): Promise<void> {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = handler;
  try {
    await run();
  } finally {
    globalThis.fetch = originalFetch;
  }
}

test("review uses Makerverse PATCH 204 then GET and keeps snake_case event/evidence fields", async () => {
  const calls: Array<{ url: string; method: string; body: string | undefined }> = [];
  await withFetch(async (input, init) => {
    calls.push({ url: String(input), method: init?.method ?? "GET", body: typeof init?.body === "string" ? init.body : undefined });
    if (init?.method === "PATCH") return new Response(null, { status: 204 });
    return new Response(JSON.stringify(event), { status: 200, headers: { "Content-Type": "application/json" } });
  }, async () => {
    const client = new BackendApiClient({ baseUrl: "https://makerverse.test/" });
    const result = await createEventsApi(client).review("evt/1", "confirmed");

    assert.deepEqual(calls[0], {
      url: "https://makerverse.test/api/v1/events/evt%2F1/review",
      method: "PATCH",
      body: JSON.stringify({ status: "confirmed" }),
    });
    assert.equal(calls[1].url, "https://makerverse.test/api/v1/events/evt%2F1");
    assert.equal(calls[1].method, "GET");
    assert.equal(result.event_id, "evt-1");
    assert.equal(result.review_status, "confirmed");
    assert.equal(result.evidence[0].source_id, "camera-01");
    assert.equal(result.evidence[0].started_at, "2026-01-01T00:00:00.000Z");
  });
});

test("event mapper preserves backend snake_case provenance fields", () => {
  const mapped = toLegacyEvent(event);
  assert.equal(mapped.event_id, "evt-1");
  assert.equal(mapped.source_id, "camera-01");
  assert.equal(mapped.facts[0].fact_type, "object_removed");
  assert.equal(mapped.facts[0].metadata?.source_id, "camera-01");
  assert.equal(mapped.evidence[0].source_id, "camera-01");
  assert.equal(mapped.evidence[0].started_at, "2026-01-01T00:00:00.000Z");
  assert.equal(mapped.evidence[0].uri, "/api/v1/events/evt-1/evidence");
});
