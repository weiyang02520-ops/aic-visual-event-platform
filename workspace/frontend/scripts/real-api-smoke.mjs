const baseUrl = process.env.VITE_AI_API_URL || "http://127.0.0.1:8010";

async function request(path, options) {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`${path}: ${response.status} ${response.statusText}`);
  return response.json();
}

const health = await request("/health");
const plugins = await request("/api/v1/plugins");
const events = await request("/api/v1/events");
const objects = await request("/api/v1/objects");
const persons = await request("/api/v1/persons");
const evidence = await request(
  "/api/v1/evidence/resolve?source_id=mock%3A%2F%2Ffrontend-smoke&started_at=2026-01-01T00%3A00%3A00Z&ended_at=2026-01-01T00%3A00%3A05Z",
);
const detectors = await request("/api/v1/providers/detectors?source=camera.mp4");
const registry = await request("/api/v1/registry/match", {
  method: "POST",
  body: JSON.stringify({ kind: "all", embedding: [1, 0] }),
});

console.log(JSON.stringify({
  baseUrl,
  health: health.status,
  plugins: plugins.length,
  events: events.length,
  objects: objects.length,
  persons: persons.length,
  evidence: evidence.status,
  selectedDetector: detectors.find((item) => item.selected)?.provider_id || null,
  registryMatches: registry.length,
}, null, 2));
