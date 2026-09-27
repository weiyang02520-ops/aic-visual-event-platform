import type { EvidenceRefContract, JsonObject, PrimitiveFactContract, UnifiedEventContract } from "../../contracts";
import { toObjectSubject } from "./objectAdapter";
import { toPersonSubject } from "./personAdapter";

export interface RuntimeReasoningStep {
  fact_type: string;
  confidence?: number;
  location?: string | null;
  metadata?: JsonObject;
}

export interface RuntimeEventInput {
  event_id: string;
  plugin_id: string;
  plugin_version?: string;
  event_type: string;
  title: string;
  description?: string;
  source_id: string;
  timestamp: string;
  persons?: JsonObject[];
  objects?: JsonObject[];
  reasoning_chain?: RuntimeReasoningStep[];
  evidence?: EvidenceRefContract[];
  confidence?: number;
  severity?: UnifiedEventContract["severity"];
  review_status?: UnifiedEventContract["review_status"];
  location?: string | null;
  metadata?: JsonObject;
}

/** Converts runtime observations into the existing UnifiedEventContract envelope. */
export function toEventContract(input: RuntimeEventInput): UnifiedEventContract {
  const persons = input.persons ?? [];
  const objects = input.objects ?? [];
  const reasoning = input.reasoning_chain ?? [];
  const facts: PrimitiveFactContract[] = reasoning.map((step) => ({
    fact_type: step.fact_type,
    confidence: step.confidence ?? input.confidence ?? 0,
    location: step.location ?? input.location ?? null,
    metadata: step.metadata,
  }));
  return {
    event_id: input.event_id,
    plugin_id: input.plugin_id,
    plugin_version: input.plugin_version ?? "runtime",
    event_type: input.event_type,
    title: input.title,
    description: input.description ?? "AI runtime 事件，等待人工复核。",
    source_id: input.source_id,
    started_at: input.timestamp,
    ended_at: input.timestamp,
    confidence: input.confidence ?? 0,
    severity: input.severity ?? "info",
    review_status: input.review_status ?? "pending",
    subject: persons[0] ? toPersonSubject(persons[0]) : null,
    object: objects[0] ? toObjectSubject(objects[0]) : null,
    location: input.location ?? null,
    evidence: input.evidence ?? [],
    facts,
    metadata: {
      ...(input.metadata ?? {}),
      runtime_persons: persons.map(toPersonSubject),
      runtime_objects: objects.map(toObjectSubject),
      reasoning_chain: reasoning,
    },
  };
}
