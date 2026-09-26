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
    async health(): Promise<RepositoryHealth> { await wait(80); return { status: "mock" }; },
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
      if (source.includes("elderly")) {
        const event = structuredClone(events[0]);
        event.event_id = `evt-${Date.now()}`; event.created_at = now(); events = [event, ...events]; job.event_ids = [event.event_id];
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
