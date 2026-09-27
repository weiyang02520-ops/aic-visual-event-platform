import type { JsonObject, PluginContract, RegisteredObjectContract, RegisteredPersonContract, UnifiedEventContract } from "../../contracts";
import { createBackendApi } from "../backend";
import { toEventContract as toLegacyEventContract, toObjectContract } from "../objectAdapter";
import { toPluginContract } from "../pluginAdapter";
import type { Plugin, RegisteredObject, RegisteredPerson, Repository, UnifiedEvent } from "../../types";
import { toRuntimePersonContract } from "./personAdapter";
import { toRuntimeObjectContract } from "./objectAdapter";
import type { RuntimeAdapter, RuntimeSnapshot } from "./types";

function personContract(person: RegisteredPerson): RegisteredPersonContract {
  return { person_id: person.person_id, display_name: person.display_name, role: person.role, reference_uris: [...person.reference_uris], embedding: person.embedding ?? null, status: person.status };
}

function eventContract(event: UnifiedEvent): UnifiedEventContract {
  return toLegacyEventContract(event);
}

function pluginContract(plugin: Plugin): PluginContract {
  return toPluginContract(plugin);
}

function jsonObject(value: Record<string, unknown> | null | undefined): JsonObject | null {
  return value && typeof value === "object" ? value : null;
}

function mergeRuntimePersons(registered: RegisteredPersonContract[], events: UnifiedEventContract[]): RegisteredPersonContract[] {
  const merged = [...registered];
  events.forEach((event) => {
    const subject = jsonObject(event.subject);
    if (!subject) return;
    const runtimePerson = toRuntimePersonContract(subject);
    const existing = merged.find((person) => person.person_id === runtimePerson.person_id || person.display_name === runtimePerson.display_name);
    if (!existing) merged.push(runtimePerson);
  });
  return merged;
}

function mergeRuntimeObjects(registered: RegisteredObjectContract[], events: UnifiedEventContract[]): RegisteredObjectContract[] {
  const merged = [...registered];
  events.forEach((event) => {
    const object = jsonObject(event.object);
    if (!object) return;
    const runtimeObject = toRuntimeObjectContract(object);
    const existing = merged.find((item) => item.object_id === runtimeObject.object_id || item.name === runtimeObject.name);
    if (!existing) merged.push(runtimeObject);
  });
  return merged;
}

export function createRepositoryRuntimeAdapter(repository: Repository): RuntimeAdapter {
  return {
    async getSnapshot(): Promise<RuntimeSnapshot> {
      const [persons, objects, events, plugins] = await Promise.all([repository.listPersons(), repository.listObjects(), repository.listEvents(), repository.listPlugins()]);
      const eventContracts = events.map(eventContract);
      const registeredPersons = persons.map(personContract);
      const registeredObjects = objects.map((object) => toObjectContract(object));
      return {
        persons: mergeRuntimePersons(registeredPersons, eventContracts),
        objects: mergeRuntimeObjects(registeredObjects, eventContracts),
        events: eventContracts,
        plugins: plugins.map(pluginContract),
      };
    },
  };
}

export function createBackendRuntimeAdapter(baseUrl: string, timeoutMs?: number): RuntimeAdapter {
  const api = createBackendApi({ baseUrl, timeoutMs });
  return {
    async getSnapshot(): Promise<RuntimeSnapshot> {
      const [persons, objects, events, plugins] = await Promise.all([api.listPersons(), api.listObjects(), api.listEvents(), api.listPlugins()]);
      return { persons: mergeRuntimePersons(persons, events), objects: mergeRuntimeObjects(objects, events), events, plugins };
    },
  };
}

export function createRuntimeAdapter(mode: "mock" | "real", options: { repository?: Repository; baseUrl?: string; timeoutMs?: number }): RuntimeAdapter {
  if (mode === "mock" && options.repository) return createRepositoryRuntimeAdapter(options.repository);
  return createBackendRuntimeAdapter(options.baseUrl ?? "http://127.0.0.1:8010", options.timeoutMs);
}

export { toRuntimePersonContract } from "./personAdapter";
