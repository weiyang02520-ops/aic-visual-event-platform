import type { IsoTimestamp, JsonObject } from "./common";

export type ReviewStatus = "pending" | "confirmed" | "rejected";
export type Severity = "info" | "low" | "medium" | "high";

export interface EvidenceRefContract {
  source_id: string;
  started_at: IsoTimestamp;
  ended_at: IsoTimestamp;
  resolver: string;
  uri?: string | null;
  status: string;
  reason?: string | null;
}

export interface PrimitiveFactContract {
  fact_type: string;
  timestamp: IsoTimestamp;
  confidence: number;
  subject?: JsonObject | null;
  object?: JsonObject | null;
  location?: string | null;
  metadata?: JsonObject;
}

export interface UnifiedEventContract {
  event_id: string;
  schema_version?: string;
  plugin_id: string;
  plugin_version: string;
  event_type: string;
  title: string;
  description: string;
  source_id: string;
  started_at: IsoTimestamp;
  ended_at: IsoTimestamp;
  confidence: number;
  severity: Severity;
  review_status: ReviewStatus;
  subject?: JsonObject | null;
  object?: JsonObject | null;
  location?: string | null;
  evidence: EvidenceRefContract[];
  facts: PrimitiveFactContract[];
  metadata: JsonObject;
  created_at?: IsoTimestamp;
}
