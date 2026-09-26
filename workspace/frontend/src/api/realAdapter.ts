import type { Repository } from "../types";
import type { AnalysisJobContract, EvidenceResolutionContract, SourceInspectionContract } from "../contracts";
import type { DetectorProviderStatusContract } from "../contracts";
import { BackendApiClient, createBackendApi, toLegacyEvent, toLegacyHealth, toLegacyJob, toLegacyObject, toLegacyPerson, toLegacyPlugin } from "./backend";

/** Real HTTP adapter. It only maps existing backend routes; it does not add a fallback path. */
export function createRealAdapter(baseUrl: string, options?: { timeoutMs?: number }): Repository {
  const api = createBackendApi({ baseUrl, timeoutMs: options?.timeoutMs });
  return {
    health: async () => toLegacyHealth(await api.health()),
    listPlugins: async () => (await api.listPlugins()).map(toLegacyPlugin),
    togglePlugin: async (id, enabled) => toLegacyPlugin(await api.togglePlugin(id, enabled)),
    listEvents: async () => (await api.listEvents()).map(toLegacyEvent),
    reviewEvent: async (id, status) => toLegacyEvent(await api.reviewEvent(id, status)),
    createAnalysis: async (source) => toLegacyJob(await api.createAnalysis(source)),
    getAnalysis: async (jobId) => toLegacyJob(await api.getAnalysis(jobId)),
    listObjects: async () => (await api.listObjects()).map(toLegacyObject),
    createObject: async (name, description = "新注册对象", referenceUris = []) => toLegacyObject(await api.createObject(name, description, referenceUris)),
    listPersons: async () => (await api.listPersons()).map(toLegacyPerson),
    createPerson: async (name, role, referenceUris = []) => toLegacyPerson(await api.createPerson(name, role, referenceUris)),
  };
}

export interface ExtendedRealAdapter extends Repository {
  listDetectorProviders(source?: string): Promise<DetectorProviderStatusContract[]>;
  resolveEvidence(sourceId: string, startedAt: string, endedAt: string, uri?: string): Promise<EvidenceResolutionContract>;
  inspectSource(source: string): Promise<SourceInspectionContract>;
}

export function createExtendedRealAdapter(baseUrl: string, options?: { timeoutMs?: number }): ExtendedRealAdapter {
  const adapter = createRealAdapter(baseUrl, options);
  const client = new BackendApiClient({ baseUrl, timeoutMs: options?.timeoutMs });
  return {
    ...adapter,
    listDetectorProviders: (source) => client.get<DetectorProviderStatusContract[]>(`/api/v1/providers/detectors${source ? `?source=${encodeURIComponent(source)}` : ""}`),
    resolveEvidence: (sourceId, startedAt, endedAt, uri) => client.get<EvidenceResolutionContract>(`/api/v1/evidence/resolve?source_id=${encodeURIComponent(sourceId)}&started_at=${encodeURIComponent(startedAt)}&ended_at=${encodeURIComponent(endedAt)}${uri ? `&uri=${encodeURIComponent(uri)}` : ""}`),
    inspectSource: (source) => client.get<SourceInspectionContract>(`/api/v1/sources/inspect?source=${encodeURIComponent(source)}`),
  };
}
