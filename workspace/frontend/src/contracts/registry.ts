export interface RegisteredObjectContract {
  object_id: string;
  name: string;
  description: string;
  reference_uris: string[];
  embedding?: number[] | null;
  status: string;
  created_at?: string;
}

export interface RegisteredPersonContract {
  person_id: string;
  display_name: string;
  role: string;
  reference_uris: string[];
  embedding?: number[] | null;
  status: string;
  created_at?: string;
}

export interface RegistryMatchContract {
  registry_id: string;
  label: string;
  kind: "object" | "person";
  similarity: number;
  accepted: boolean;
}
