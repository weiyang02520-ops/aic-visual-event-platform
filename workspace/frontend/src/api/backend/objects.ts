import type { RegisteredObjectContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createObjectsApi(client: BackendApiClient) {
  return {
    list: () => client.get<RegisteredObjectContract[]>("/api/v1/objects"),
    create: (name: string, description = "新注册对象", referenceUris: string[] = []) => client.post<RegisteredObjectContract>("/api/v1/objects", { name, description, reference_uris: referenceUris }),
  };
}
