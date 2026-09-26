import type { RegisteredObjectContract, UnifiedEventContract } from "../../contracts";

export interface ObjectMemoryItem {
  object: RegisteredObjectContract;
  category: string;
  relatedPluginNames: string[];
  relatedEvents: UnifiedEventContract[];
  lastSeen: string | null;
}
