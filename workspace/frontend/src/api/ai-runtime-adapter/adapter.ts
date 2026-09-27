import type { PluginContract, RegisteredObjectContract, RegisteredPersonContract, UnifiedEventContract } from "../../contracts";
import { createBackendApi } from "../backend";
import { toEventContract as toLegacyEventContract, toObjectContract } from "../objectAdapter";
import { toPluginContract } from "../pluginAdapter";
import type { Plugin, RegisteredObject, RegisteredPerson, Repository, UnifiedEvent } from "../../types";
import { toRuntimePersonContract } from "./personAdapter";
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

export function createRepositoryRuntimeAdapter(repository: Repository): RuntimeAdapter {
  return {
    async getSnapshot(): Promise<RuntimeSnapshot> {
      const [persons, objects, events, plugins] = await Promise.all([repository.listPersons(), repository.listObjects(), repository.listEvents(), repository.listPlugins()]);
      return {
        persons: persons.map(personContract),
        objects: objects.map((object) => toObjectContract(object)),
        events: events.map(eventContract),
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
      return { persons, objects, events, plugins };
    },
  };
}

export function createRuntimeAdapter(mode: "mock" | "real", options: { repository?: Repository; baseUrl?: string; timeoutMs?: number }): RuntimeAdapter {
  if (mode === "mock" && options.repository) return createRepositoryRuntimeAdapter(options.repository);
  return createBackendRuntimeAdapter(options.baseUrl ?? "http://127.0.0.1:8010", options.timeoutMs);
}

export { toRuntimePersonContract } from "./personAdapter";
