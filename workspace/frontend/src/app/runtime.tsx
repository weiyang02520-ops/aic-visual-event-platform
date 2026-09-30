import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createMockRepository, createRealRepository } from "../repository";
import { createRuntimeAdapter, toLegacyEvent, toLegacyObject, toLegacyPerson } from "../api";
import { createInsightsApi, type ReadinessContract } from "../api/insights";
import type { DetectorProviderStatusContract } from "../contracts";
import type { Mode, Plugin, RegisteredObject, RegisteredPerson, Repository, RepositoryConnection, RepositoryHealth, ReviewStatus, UnifiedEvent } from "../types";

export const AI_API_URL = import.meta.env.VITE_AI_API_URL ?? "http://127.0.0.1:8010";

export interface Runtime {
  mode: Mode;
  setMode: (mode: Mode) => void;
  repo: Repository;
  connection: RepositoryConnection;
  loading: boolean;
  health: RepositoryHealth;
  readiness: ReadinessContract | null;
  detectors: DetectorProviderStatusContract[] | null;
  events: UnifiedEvent[];
  plugins: Plugin[];
  objects: RegisteredObject[];
  persons: RegisteredPerson[];
  analyzing: boolean;
  /** Whether mutating actions may run. Real mode requires an online API; there is no Mock fallback. */
  canMutate: boolean;
  review: (event: UnifiedEvent, status: ReviewStatus) => Promise<void>;
  togglePlugin: (plugin: Plugin) => Promise<void>;
  runAnalysis: (source?: string) => Promise<UnifiedEvent | null>;
  createObject: (name: string, description: string, references: string[]) => Promise<boolean>;
  createPerson: (name: string, role: string, references: string[]) => Promise<boolean>;
  toast: string | null;
  notify: (message: string | null) => void;
}

const RuntimeContext = createContext<Runtime | null>(null);

function errorMessage(error: unknown): string {
  return error instanceof Error && error.message ? error.message : "未知连接错误";
}

export function connectionLabel(connection: RepositoryConnection): string {
  if (connection.status === "mock") return "演示数据";
  if (connection.status === "loading") return connection.mode === "real" ? "正在连接 AI 服务" : "正在加载";
  if (connection.status === "online") return "AI 服务在线";
  return connection.mode === "real" ? "AI 服务离线" : "演示数据加载失败";
}

export function RuntimeProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<Mode>("mock");
  const [repo, setRepo] = useState<Repository>(() => createMockRepository());
  const [connection, setConnection] = useState<RepositoryConnection>({ mode: "mock", status: "loading" });
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<RepositoryHealth>({ status: "loading" });
  const [readiness, setReadiness] = useState<ReadinessContract | null>(null);
  const [detectors, setDetectors] = useState<DetectorProviderStatusContract[] | null>(null);
  const [events, setEvents] = useState<UnifiedEvent[]>([]);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [objects, setObjects] = useState<RegisteredObject[]>([]);
  const [persons, setPersons] = useState<RegisteredPerson[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<number | undefined>(undefined);

  const notify = useCallback((message: string | null) => {
    setToast(message);
    window.clearTimeout(toastTimer.current);
    if (message) toastTimer.current = window.setTimeout(() => setToast(null), 3800);
  }, []);

  useEffect(() => {
    const nextRepo = mode === "mock" ? createMockRepository() : createRealRepository(AI_API_URL);
    let active = true;
    setRepo(nextRepo);
    setLoading(true);
    setHealth({ status: "loading" });
    setConnection({ mode, status: "loading" });
    // Clear the previous source before any request starts; a late response from
    // the old source is ignored so Mock data cannot survive a failed Real load.
    setEvents([]); setPlugins([]); setObjects([]); setPersons([]);
    setReadiness(null); setDetectors(null);

    const runtimeAdapter = createRuntimeAdapter(mode, { repository: mode === "mock" ? nextRepo : undefined, baseUrl: AI_API_URL });
    Promise.all([nextRepo.health(), runtimeAdapter.getSnapshot()])
      .then(([nextHealth, snapshot]) => {
        if (!active) return;
        setHealth(nextHealth);
        setEvents(snapshot.events.map(toLegacyEvent));
        setPlugins(snapshot.plugins.map((plugin) => ({ ...plugin })));
        setObjects(snapshot.objects.map(toLegacyObject));
        setPersons(snapshot.persons.map(toLegacyPerson));
        setConnection({ mode, status: mode === "mock" ? "mock" : "online" });
      })
      .catch((error: unknown) => {
        if (!active) return;
        const reason = errorMessage(error);
        setEvents([]); setPlugins([]); setObjects([]); setPersons([]);
        setHealth({ status: "offline" });
        setConnection({ mode, status: "offline", reason });
        notify(`${mode === "real" ? "AI 服务" : "演示数据"}不可用：${reason}`);
      })
      .finally(() => { if (active) setLoading(false); });

    if (mode === "real") {
      // Readiness and provider rows are diagnostics; failures leave them null instead of blocking the page.
      const insights = createInsightsApi(AI_API_URL);
      insights.ready().then((value) => { if (active) setReadiness(value); }).catch(() => undefined);
      insights.detectors().then((value) => { if (active) setDetectors(value); }).catch(() => undefined);
    }
    return () => { active = false; };
  }, [mode, notify]);

  const canMutate = mode === "mock" || connection.status === "online";

  const guard = useCallback((action: string) => {
    if (canMutate) return true;
    notify(`${connectionLabel(connection)}，${action}未执行${connection.reason ? `：${connection.reason}` : ""}`);
    return false;
  }, [canMutate, connection, notify]);

  const review = useCallback(async (event: UnifiedEvent, status: ReviewStatus) => {
    if (!guard("事件复核")) return;
    try {
      const updated = await repo.reviewEvent(event.event_id, status);
      setEvents((current) => current.map((item) => (item.event_id === updated.event_id ? updated : item)));
      notify(status === "confirmed" ? "已确认，复核记录已写入" : "已驳回该事件");
    } catch (error) {
      notify(`事件复核失败：${errorMessage(error)}`);
    }
  }, [guard, notify, repo]);

  const togglePlugin = useCallback(async (plugin: Plugin) => {
    if (!guard("插件操作")) return;
    try {
      const updated = await repo.togglePlugin(plugin.plugin_id, !plugin.enabled);
      setPlugins((current) => current.map((item) => (item.plugin_id === updated.plugin_id ? updated : item)));
      notify(`${updated.name} 已${updated.enabled ? "启用" : "停用"}`);
    } catch (error) {
      notify(`插件操作失败：${errorMessage(error)}`);
    }
  }, [guard, notify, repo]);

  const runAnalysis = useCallback(async (source?: string) => {
    if (!guard("分析任务")) return null;
    setAnalyzing(true);
    try {
      const target = source ?? (mode === "mock" ? "mock://elderly-medication" : import.meta.env.VITE_AI_PREVIEW_SOURCE ?? "camera.mp4");
      const job = await repo.createAnalysis(target);
      let finalJob = job;
      if (mode === "real" && !["completed", "failed", "stopped"].includes(finalJob.status)) {
        for (let attempt = 0; attempt < 20; attempt += 1) {
          await new Promise((resolve) => setTimeout(resolve, 250));
          finalJob = await repo.getAnalysis(job.job_id);
          if (["completed", "failed", "stopped"].includes(finalJob.status)) break;
        }
      }
      const nextEvents = await repo.listEvents();
      setEvents(nextEvents);
      const created = nextEvents.find((event) => finalJob.event_ids.includes(event.event_id)) ?? null;
      notify(finalJob.status === "completed" ? `分析完成${finalJob.event_ids.length ? `，生成 ${finalJob.event_ids.length} 个事件` : ""}` : finalJob.status === "failed" ? "分析任务失败" : finalJob.status === "stopped" ? "分析任务已停止" : "分析任务已提交");
      return created;
    } catch (error) {
      notify(`分析任务失败：${errorMessage(error)}`);
      return null;
    } finally {
      setAnalyzing(false);
    }
  }, [guard, mode, notify, repo]);

  const createObject = useCallback(async (name: string, description: string, references: string[]) => {
    if (!guard("物品登记")) return false;
    try {
      await repo.createObject(name, description || "新登记物品", references);
      setObjects(await repo.listObjects());
      notify(`已记住「${name}」`);
      return true;
    } catch (error) {
      notify(`物品登记失败：${errorMessage(error)}`);
      return false;
    }
  }, [guard, notify, repo]);

  const createPerson = useCallback(async (name: string, role: string, references: string[]) => {
    if (!guard("人员登记")) return false;
    try {
      await repo.createPerson(name, role || "unknown", references);
      setPersons(await repo.listPersons());
      notify(`已登记人员「${name}」`);
      return true;
    } catch (error) {
      notify(`人员登记失败：${errorMessage(error)}`);
      return false;
    }
  }, [guard, notify, repo]);

  const value = useMemo<Runtime>(() => ({
    mode, setMode, repo, connection, loading, health, readiness, detectors, events, plugins, objects, persons, analyzing, canMutate,
    review, togglePlugin, runAnalysis, createObject, createPerson, toast, notify,
  }), [mode, repo, connection, loading, health, readiness, detectors, events, plugins, objects, persons, analyzing, canMutate, review, togglePlugin, runAnalysis, createObject, createPerson, toast, notify]);

  return <RuntimeContext.Provider value={value}>{children}</RuntimeContext.Provider>;
}

export function useRuntime(): Runtime {
  const runtime = useContext(RuntimeContext);
  if (!runtime) throw new Error("useRuntime must be used inside RuntimeProvider");
  return runtime;
}
