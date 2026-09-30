import type { AnalysisJob, Plugin, RegisteredObject, RegisteredPerson, Repository, RepositoryHealth, ReviewStatus, UnifiedEvent } from "../types";
import { createMockEvents, mockObjects, mockPersons, mockPlugins } from "./mockData";

const wait = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));
const now = () => new Date().toISOString();

/** Stateful fixture adapter. The UI can consume it through the same contract as Real API. */
export function createMockAdapter(): Repository {
  let plugins = structuredClone(mockPlugins);
  let events = createMockEvents();
  const jobs = new Map<string, AnalysisJob>();
  let objects = structuredClone(mockObjects);
  let persons = structuredClone(mockPersons);
  return {
    async health(): Promise<RepositoryHealth> {
      await wait(80);
      const running = plugins.filter((plugin) => plugin.enabled && plugin.state !== "disabled").length;
      return {
        status: "healthy",
        service: "mock-adapter",
        detected_people: 1,
        exception_count: 0,
        checks: {
          camera: { status: "healthy", detail: "Mock 摄像头源已准备" },
          ai_model: { status: "warning", detail: "Mock 推理 fixture，未连接真实模型" },
          plugin_runtime: { status: running ? "healthy" : "warning", detail: `${running} 个插件处于运行状态` },
          backend: { status: "healthy", detail: "Mock adapter 在线" },
        },
      };
    },
    async listPlugins() { await wait(); return structuredClone(plugins); },
    async togglePlugin(pluginId, enabled) {
      await wait();
      plugins = plugins.map((plugin) => plugin.plugin_id === pluginId ? { ...plugin, enabled, state: enabled ? "running" : "disabled" } : plugin);
      const result = plugins.find((plugin) => plugin.plugin_id === pluginId);
      if (!result) throw new Error("plugin not found");
      return structuredClone(result);
    },
    async listEvents() { await wait(); return structuredClone(events); },
    async reviewEvent(eventId, status) {
      await wait();
      events = events.map((event) => event.event_id === eventId ? { ...event, review_status: status } : event);
      const result = events.find((event) => event.event_id === eventId);
      if (!result) throw new Error("event not found");
      return structuredClone(result);
    },
    async createAnalysis(source) {
      await wait(320);
      const job: AnalysisJob = { job_id: `mock-job-${Date.now()}`, source, status: "completed", progress: 1, event_ids: [] };
      // Same rule as the backend PluginManager: disabled plugins do not evaluate, so they emit nothing.
      const enabled = (id: string) => plugins.some((plugin) => plugin.plugin_id === id && plugin.enabled && plugin.state !== "disabled");
      if (source.includes("elderly") && enabled("elderly_care")) {
        const template = events.find((item) => item.event_type === "suspected_medication") ?? events[0];
        const event = structuredClone(template);
        const endedAt = Date.now();
        event.event_id = `evt-${endedAt}`; event.created_at = now(); event.review_status = "pending";
        event.started_at = new Date(endedAt - 20_000).toISOString(); event.ended_at = new Date(endedAt).toISOString();
        event.evidence = event.evidence.map((item) => ({ ...item, started_at: new Date(endedAt - 23_000).toISOString(), ended_at: new Date(endedAt + 3_000).toISOString() }));
        events = [event, ...events]; job.event_ids = [event.event_id];
      }
      jobs.set(job.job_id, structuredClone(job)); return job;
    },
    async getAnalysis(jobId) { await wait(); const job = jobs.get(jobId); if (!job) throw new Error("job not found"); return structuredClone(job); },
    async listObjects() { await wait(); return structuredClone(objects); },
    async createObject(name, description = "新注册对象", referenceUris = []) {
      await wait(); const item: RegisteredObject = { object_id: `obj-${Date.now()}`, name, description, reference_uris: referenceUris, status: "active" };
      objects = [item, ...objects]; return structuredClone(item);
    },
    async listPersons() { await wait(); return structuredClone(persons); },
    async createPerson(name, role, referenceUris = []) {
      await wait(); const item: RegisteredPerson = { person_id: `person-${Date.now()}`, display_name: name, role, reference_uris: referenceUris, status: "active" };
      persons = [item, ...persons]; return structuredClone(item);
    },
  };
}
