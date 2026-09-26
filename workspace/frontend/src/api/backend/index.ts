import type { FrontendApiAdapter } from "../../contracts";
import { BackendApiClient, type BackendClientOptions } from "./client";
import { createEventsApi } from "./events";
import { createJobsApi } from "./jobs";
import { createObjectsApi } from "./objects";
import { createPersonsApi } from "./persons";
import { createPluginsApi } from "./plugins";
import { prepareBackendWebSocket } from "./websocket";

export function createBackendApi(options: BackendClientOptions): FrontendApiAdapter & { websocket: typeof prepareBackendWebSocket } {
  const client = new BackendApiClient(options);
  const events = createEventsApi(client);
  const jobs = createJobsApi(client);
  const objects = createObjectsApi(client);
  const persons = createPersonsApi(client);
  const plugins = createPluginsApi(client);
  return {
    health: jobs.health,
    listPlugins: plugins.list,
    togglePlugin: plugins.toggle,
    listEvents: events.list,
    reviewEvent: events.review,
    createAnalysis: jobs.create,
    getAnalysis: jobs.get,
    listObjects: objects.list,
    createObject: objects.create,
    listPersons: persons.list,
    createPerson: persons.create,
    websocket: prepareBackendWebSocket,
  };
}

export { BackendApiClient } from "./client";
export { prepareBackendWebSocket } from "./websocket";
export * from "./mappers";
