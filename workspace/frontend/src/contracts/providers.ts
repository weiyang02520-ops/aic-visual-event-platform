export interface RepositoryHealthContract {
  status: string;
  service?: string;
  version?: string;
  [key: string]: unknown;
}

export interface DetectorProviderStatusContract {
  provider_id: string;
  version: string;
  available: boolean;
  selected: boolean;
  reason?: string | null;
  model_path?: string | null;
  object_model_path?: string | null;
  component?: string | null;
  pose_available?: boolean | null;
  object_available?: boolean | null;
  object_reason?: string | null;
}

export interface ObservationViewContract {
  source_id: string;
  timestamp: string;
  fact_type: string;
  confidence: number;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}
