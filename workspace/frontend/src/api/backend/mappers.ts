import type { AnalysisJobContract, PluginContract, RegisteredObjectContract, RegisteredPersonContract, RepositoryHealthContract, UnifiedEventContract } from "../../contracts";
import type { AnalysisJob, Plugin, RegisteredObject, RegisteredPerson, RepositoryHealth, UnifiedEvent } from "../../types";

export function toLegacyHealth(health: RepositoryHealthContract): RepositoryHealth {
  return { ...health };
}

export function toLegacyEvent(event: UnifiedEventContract): UnifiedEvent {
  return {
    ...event,
    // Keep per-fact provenance: the action timeline needs timestamp, source and continuity segment.
    facts: event.facts.map((fact) => ({ fact_type: fact.fact_type, confidence: fact.confidence, location: fact.location, timestamp: fact.timestamp, subject: fact.subject, object: fact.object, metadata: fact.metadata })),
    evidence: event.evidence.map((evidence) => ({ ...evidence })),
    metadata: { ...event.metadata },
  };
}

export function toLegacyObject(object: RegisteredObjectContract): RegisteredObject {
  return { ...object, reference_uris: [...object.reference_uris] };
}

export function toLegacyPerson(person: RegisteredPersonContract): RegisteredPerson {
  return { ...person, reference_uris: [...person.reference_uris] };
}

export function toLegacyPlugin(plugin: PluginContract): Plugin {
  return { ...plugin };
}

export function toLegacyJob(job: AnalysisJobContract): AnalysisJob {
  return { ...job };
}
