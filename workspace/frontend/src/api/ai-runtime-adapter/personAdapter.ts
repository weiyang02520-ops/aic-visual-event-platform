import type { JsonObject, RegisteredPersonContract } from "../../contracts";

function text(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

/** Maps runtime identity fields to the existing person registry contract. */
export function toRuntimePersonContract(input: JsonObject): RegisteredPersonContract {
  const personId = text(input.person_id ?? input.id, "runtime-person");
  const identityStatus = text(input.identity_status ?? input.status, "unknown");
  return {
    person_id: personId,
    display_name: text(input.display_name ?? input.label, personId),
    role: identityStatus,
    reference_uris: [],
    embedding: null,
    status: text(input.privacy_mode, "privacy-protected"),
  };
}

/** Runtime pose/action fields remain in the existing event subject JsonObject. */
export function toPersonSubject(input: JsonObject): JsonObject {
  const person = toRuntimePersonContract(input);
  return {
    id: person.person_id,
    label: person.display_name,
    identity_status: person.role,
    privacy_mode: person.status,
    pose: input.pose ?? null,
    action: input.action ?? null,
    confidence: typeof input.confidence === "number" ? input.confidence : null,
  };
}
