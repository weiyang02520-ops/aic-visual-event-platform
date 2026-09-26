import type {
  AnalysisJobContract,
  EvidenceResolutionContract,
  SourceInspectionContract,
} from "./jobs";
import type { UnifiedEventContract, ReviewStatus } from "./events";
import type { DetectorProviderStatusContract, RepositoryHealthContract } from "./providers";
import type { RegisteredObjectContract, RegisteredPersonContract } from "./registry";

export interface FrontendApiAdapter {
  health(): Promise<RepositoryHealthContract>;
  listPlugins(): Promise<import("../types").Plugin[]>;
  togglePlugin(pluginId: string, enabled: boolean): Promise<import("../types").Plugin>;
  listEvents(): Promise<UnifiedEventContract[]>;
  reviewEvent(eventId: string, status: ReviewStatus): Promise<UnifiedEventContract>;
  createAnalysis(source: string): Promise<AnalysisJobContract>;
  getAnalysis(jobId: string): Promise<AnalysisJobContract>;
  listObjects(): Promise<RegisteredObjectContract[]>;
  createObject(name: string, description?: string, referenceUris?: string[]): Promise<RegisteredObjectContract>;
  listPersons(): Promise<RegisteredPersonContract[]>;
  createPerson(name: string, role: string, referenceUris?: string[]): Promise<RegisteredPersonContract>;
  listDetectorProviders?(source?: string): Promise<DetectorProviderStatusContract[]>;
  resolveEvidence?(sourceId: string, startedAt: string, endedAt: string, uri?: string): Promise<EvidenceResolutionContract>;
  inspectSource?(source: string): Promise<SourceInspectionContract>;
}
