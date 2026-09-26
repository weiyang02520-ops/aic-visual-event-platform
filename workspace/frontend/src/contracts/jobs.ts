export interface AnalysisJobContract {
  job_id: string;
  source: string;
  status: string;
  progress: number;
  event_ids: string[];
  error?: string | null;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, unknown>;
}

export interface SourceInspectionContract {
  source_id: string;
  kind: string;
  provider: string;
  status: string;
  uri: string;
  capabilities: string[];
  reason?: string | null;
}

export interface EvidenceResolutionContract {
  source_id: string;
  started_at: string;
  ended_at: string;
  resolver: string;
  status: string;
  uri?: string | null;
  reason?: string | null;
}
