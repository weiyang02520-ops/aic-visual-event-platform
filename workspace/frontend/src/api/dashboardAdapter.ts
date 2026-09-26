import type { DashboardSnapshotContract, HealthCheckContract, HealthStatus, PluginContract } from "../contracts";
import type { RepositoryConnection, RepositoryHealth, UnifiedEvent } from "../types";

const healthOrder = [
  { id: "camera", label: "Camera", fallback: "等待视频源状态" },
  { id: "ai_model", label: "AI Model", fallback: "等待模型提供方状态" },
  { id: "plugin_runtime", label: "Plugin Runtime", fallback: "等待插件运行时状态" },
  { id: "backend", label: "Backend", fallback: "等待后端健康状态" },
];

function normalizeStatus(value: unknown): HealthStatus {
  const normalized = String(value ?? "").toLowerCase();
  if (["healthy", "ok", "online", "ready", "mock"].includes(normalized)) return "healthy";
  if (["offline", "error", "failed", "unavailable"].includes(normalized)) return "offline";
  return "warning";
}

function statusFromConnection(connection: RepositoryConnection, mode: "mock" | "real"): HealthStatus {
  if (connection.status === "offline") return "offline";
  if (connection.status === "loading") return "warning";
  return mode === "mock" ? "healthy" : "warning";
}

function healthChecks(health: RepositoryHealth, connection: RepositoryConnection): HealthCheckContract[] {
  const provided: Record<string, Partial<HealthCheckContract>> = health.checks && typeof health.checks === "object" ? health.checks as Record<string, Partial<HealthCheckContract>> : {};
  return healthOrder.map(({ id, label, fallback }) => {
    const item = provided[id];
    const status = item?.status ? normalizeStatus(item.status) : id === "backend" ? normalizeStatus(health.status) : statusFromConnection(connection, connection.mode);
    const detail = typeof item?.detail === "string" && item.detail ? item.detail : fallback;
    return { id, label, status, detail };
  });
}

/** Build a dashboard snapshot from adapter responses without inventing model claims. */
export function toDashboardSnapshot(health: RepositoryHealth, events: UnifiedEvent[], plugins: PluginContract[], connection: RepositoryConnection, loading: boolean): DashboardSnapshotContract {
  const checks = healthChecks(health, connection);
  const detectedPeople = typeof health.detected_people === "number" ? health.detected_people : new Set(events.map((event) => String(event.subject?.id ?? event.subject?.label ?? "")).filter(Boolean)).size;
  const exceptionCount = typeof health.exception_count === "number" ? health.exception_count : plugins.filter((plugin) => plugin.state === "degraded" || plugin.state === "error").length;
  const status: HealthStatus = loading ? "warning" : checks.some((check) => check.status === "offline") ? "offline" : checks.some((check) => check.status === "warning") ? "warning" : "healthy";
  return {
    source: connection.mode,
    stats: {
      detected_people: detectedPeople,
      event_count: events.length,
      running_plugins: plugins.filter((plugin) => plugin.enabled && plugin.state !== "disabled" && plugin.state !== "error").length,
      total_plugins: plugins.length,
      exception_count: exceptionCount,
    },
    health: checks,
    status,
  };
}
