import type { RegisteredPersonContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createPersonsApi(client: BackendApiClient) {
  return {
    list: () => client.get<RegisteredPersonContract[]>("/api/v1/persons"),
    create: (name: string, role: string, referenceUris: string[] = []) => client.post<RegisteredPersonContract>("/api/v1/persons", { display_name: name, role, reference_uris: referenceUris }),
  };
}
