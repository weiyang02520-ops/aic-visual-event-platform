import type { PluginContract, RegisteredObjectContract, RegisteredPersonContract, UnifiedEventContract } from "../../contracts";

/** Runtime data is composed only from the existing frontend contracts. */
export interface RuntimeSnapshot {
  persons: RegisteredPersonContract[];
  objects: RegisteredObjectContract[];
  events: UnifiedEventContract[];
  plugins: PluginContract[];
}

export interface RuntimeAdapter {
  getSnapshot(): Promise<RuntimeSnapshot>;
}
