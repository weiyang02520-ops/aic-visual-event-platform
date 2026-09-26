import type { RegisteredObjectContract, UnifiedEventContract } from "../contracts";
import type { RegisteredObject, UnifiedEvent } from "../types";

/**
 * Keep the registry repository compatibility shape at the UI boundary while
 * exposing the stable contract used by object-memory features.
 */
export function toObjectContract(object: RegisteredObject): RegisteredObjectContract {
  return {
    object_id: object.object_id,
    name: object.name,
    description: object.description,
    reference_uris: [...object.reference_uris],
    embedding: object.embedding ?? null,
    status: object.status,
  };
}

export function toEventContract(event: UnifiedEvent): UnifiedEventContract {
  return {
    ...event,
    facts: event.facts.map((fact) => ({ ...fact })),
    metadata: { ...event.metadata },
    evidence: event.evidence.map((evidence) => ({ ...evidence })),
  };
}

/**
 * Event payloads can identify an object by either its registry id or its
 * display label. The adapter centralises that compatibility rule so views do
 * not need to know which backend representation they received.
 */
export function eventReferencesObject(event: UnifiedEventContract, object: RegisteredObjectContract): boolean {
  const eventObject = event.object ?? {};
  const id = String(eventObject.id ?? eventObject.object_id ?? eventObject.registry_id ?? "");
  const label = String(eventObject.label ?? eventObject.name ?? "");
  return id === object.object_id || label === object.name;
}
