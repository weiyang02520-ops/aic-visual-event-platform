export type Mode = "mock" | "real";
export type View = "dashboard" | "monitor" | "events" | "plugins" | "registry" | "settings";
export type Scenario = "elderly" | "workshop" | "robot" | "universal";
export type RepositoryConnectionStatus = "loading" | "online" | "offline" | "mock";

export interface RepositoryConnection {
  mode: Mode;
  status: RepositoryConnectionStatus;
  reason?: string;
}

export interface RepositoryHealth {
  status: string;
  [key: string]: unknown;
}

export type ReviewStatus = "pending" | "confirmed" | "rejected";
export type PlaybackKind = "mock" | "hls" | "http-flv" | "rtmp" | "rtsp" | "unknown";

export interface PlaybackState {
  kind: PlaybackKind;
  url: string | null;
  browserPlayable: boolean;
  label: string;
  reason: string;
}

export interface LiveSession {
  id: string;
  title: string;
  status: string;
  ingestUrl?: string | null;
  rtmpUrl?: string | null;
  httpFlvUrl?: string | null;
  hlsUrl?: string | null;
}

export interface Plugin {
  plugin_id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  state: string;
  error?: string | null;
}

export interface EvidenceRef {
  source_id: string;
  started_at: string;
  ended_at: string;
  resolver: string;
  uri?: string | null;
  status: string;
}

export interface EventFact {
  fact_type: string;
  confidence: number;
  location?: string | null;
}

export interface UnifiedEvent {
  event_id: string;
  created_at?: string;
  plugin_id: string;
  plugin_version: string;
  event_type: string;
  title: string;
  description: string;
  source_id: string;
  started_at: string;
  ended_at: string;
  confidence: number;
  severity: "info" | "low" | "medium" | "high";
  review_status: ReviewStatus;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  location?: string | null;
  evidence: EvidenceRef[];
  facts: EventFact[];
  metadata: Record<string, unknown>;
}

export interface AnalysisJob {
  job_id: string;
  source: string;
  status: string;
  progress: number;
  event_ids: string[];
}

export interface RegisteredObject {
  object_id: string;
  name: string;
  description: string;
  reference_uris: string[];
  embedding?: number[] | null;
  status: string;
}

export interface RegisteredPerson {
  person_id: string;
  display_name: string;
  role: string;
  reference_uris: string[];
  embedding?: number[] | null;
  status: string;
}

export interface RegistryMatch {
  registry_id: string;
  label: string;
  kind: "object" | "person";
  similarity: number;
  accepted: boolean;
}

export interface Repository {
  health(): Promise<RepositoryHealth>;
  listPlugins(): Promise<Plugin[]>;
  togglePlugin(pluginId: string, enabled: boolean): Promise<Plugin>;
  listEvents(): Promise<UnifiedEvent[]>;
  reviewEvent(eventId: string, status: ReviewStatus): Promise<UnifiedEvent>;
  createAnalysis(source: string): Promise<AnalysisJob>;
  getAnalysis(jobId: string): Promise<AnalysisJob>;
  listObjects(): Promise<RegisteredObject[]>;
  createObject(name: string): Promise<RegisteredObject>;
  listPersons(): Promise<RegisteredPerson[]>;
  createPerson(name: string, role: string): Promise<RegisteredPerson>;
}
