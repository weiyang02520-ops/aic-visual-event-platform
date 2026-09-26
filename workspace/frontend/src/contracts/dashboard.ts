import type { HealthCheckContract, HealthStatus } from "./providers";

export interface DashboardStatsContract {
  detected_people: number;
  event_count: number;
  running_plugins: number;
  total_plugins: number;
  exception_count: number;
}

export interface DashboardSnapshotContract {
  source: "mock" | "real";
  stats: DashboardStatsContract;
  health: HealthCheckContract[];
  status: HealthStatus;
}
