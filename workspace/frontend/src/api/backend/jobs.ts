import type { AnalysisJobContract, RepositoryHealthContract } from "../../contracts";
import type { BackendApiClient } from "./client";

export function createJobsApi(client: BackendApiClient) {
  return {
    health: () => client.get<RepositoryHealthContract>("/health"),
    create: (source: string) => client.post<AnalysisJobContract>("/api/v1/analysis/jobs", { source }),
    get: (jobId: string) => client.get<AnalysisJobContract>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}`),
  };
}
