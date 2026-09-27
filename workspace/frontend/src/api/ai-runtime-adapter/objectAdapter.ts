import type { JsonObject, RegisteredObjectContract } from "../../contracts";

function text(value: unknown, fallback: string) {
  return typeof value === "string" && value.trim() ? value : fallback;
}

/** Maps runtime object fields to the existing object registry contract. */
export function toRuntimeObjectContract(input: JsonObject): RegisteredObjectContract {
  const objectId = text(input.object_id ?? input.id, "runtime-object");
  const category = text(input.category, "object");
  return {
    object_id: objectId,
    name: text(input.name ?? input.label, objectId),
    description: category,
    reference_uris: [],
    embedding: null,
    status: text(input.state ?? input.status, "tracked"),
  };
}

/** Runtime bbox/state/confidence fields use the existing event object JsonObject. */
export function toObjectSubject(input: JsonObject): JsonObject {
  const object = toRuntimeObjectContract(input);
  return {
    id: object.object_id,
    label: object.name,
    category: input.category ?? object.description,
    bbox: input.bbox ?? null,
    state: object.status,
    confidence: typeof input.confidence === "number" ? input.confidence : null,
  };
}
