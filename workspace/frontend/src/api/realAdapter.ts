import type { Repository, RepositoryHealth } from "../types";
import type { AnalysisJobContract, EvidenceResolutionContract, SourceInspectionContract } from "../contracts";
import type { DetectorProviderStatusContract } from "../contracts";
import { requestJson } from "./httpClient";

/** Real HTTP adapter. It only maps existing backend routes; it does not add a fallback path. */
export function createRealAdapter(baseUrl: string): Repository {
  const request = <T>(path: string, options?: RequestInit) => requestJson<T>(baseUrl, path, options);
  return {
    health: () => request<RepositoryHealth>("/health"),
    listPlugins: () => request<import("../types").Plugin[]>("/api/v1/plugins"),
    togglePlugin: (id, enabled) => request<import("../types").Plugin>(`/api/v1/plugins/${id}/${enabled ? "enable" : "disable"}`, { method: "POST" }),
    listEvents: () => request<import("../types").UnifiedEvent[]>("/api/v1/events"),
    reviewEvent: (id, status) => request<import("../types").UnifiedEvent>(`/api/v1/events/${id}/review`, { method: "POST", body: JSON.stringify({ status }) }),
    createAnalysis: (source) => request<AnalysisJobContract>("/api/v1/analysis/jobs", { method: "POST", body: JSON.stringify({ source }) }),
    getAnalysis: (jobId) => request<AnalysisJobContract>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}`),
    listObjects: () => request<import("../types").RegisteredObject[]>("/api/v1/objects"),
    createObject: (name, description = "新注册对象", referenceUris = []) => request<import("../types").RegisteredObject>("/api/v1/objects", { method: "POST", body: JSON.stringify({ name, description, reference_uris: referenceUris }) }),
    listPersons: () => request<import("../types").RegisteredPerson[]>("/api/v1/persons"),
    createPerson: (name, role, referenceUris = []) => request<import("../types").RegisteredPerson>("/api/v1/persons", { method: "POST", body: JSON.stringify({ display_name: name, role, reference_uris: referenceUris }) }),
  };
}

export interface ExtendedRealAdapter extends Repository {
  listDetectorProviders(source?: string): Promise<DetectorProviderStatusContract[]>;
  resolveEvidence(sourceId: string, startedAt: string, endedAt: string, uri?: string): Promise<EvidenceResolutionContract>;
  inspectSource(source: string): Promise<SourceInspectionContract>;
}

export function createExtendedRealAdapter(baseUrl: string): ExtendedRealAdapter {
  const adapter = createRealAdapter(baseUrl);
  const request = <T>(path: string, options?: RequestInit) => requestJson<T>(baseUrl, path, options);
  return {
    ...adapter,
    listDetectorProviders: (source) => request<DetectorProviderStatusContract[]>(`/api/v1/providers/detectors${source ? `?source=${encodeURIComponent(source)}` : ""}`),
    resolveEvidence: (sourceId, startedAt, endedAt, uri) => request<EvidenceResolutionContract>(`/api/v1/evidence/resolve?source_id=${encodeURIComponent(sourceId)}&started_at=${encodeURIComponent(startedAt)}&ended_at=${encodeURIComponent(endedAt)}${uri ? `&uri=${encodeURIComponent(uri)}` : ""}`),
    inspectSource: (source) => request<SourceInspectionContract>(`/api/v1/sources/inspect?source=${encodeURIComponent(source)}`),
  };
}
