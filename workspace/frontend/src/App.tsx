import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bell,
  Box,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Eye,
  Gauge,
  LayoutDashboard,
  Network,
  Pause,
  Play,
  Plus,
  Radio,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Users,
  Video,
  X,
} from "lucide-react";
import { createMockRepository, createRealRepository } from "./repository";
import { choosePlayback, classifyPlaybackUrl, createMakerverseLiveAdapter } from "./media";
import type { LiveSession, Mode, Plugin, RegisteredObject, RegisteredPerson, Repository, RepositoryConnection, RepositoryConnectionStatus, ReviewStatus, Scenario, UnifiedEvent, View } from "./types";

const navItems: { id: View; label: string; icon: typeof LayoutDashboard }[] = [
  { id: "dashboard", label: "总览", icon: LayoutDashboard },
  { id: "monitor", label: "实时监控", icon: Video },
  { id: "events", label: "事件中心", icon: Activity },
  { id: "plugins", label: "插件能力", icon: Network },
  { id: "registry", label: "对象与人员", icon: Users },
  { id: "settings", label: "系统设置", icon: Settings },
];

const scenarioCopy: Record<Scenario, { label: string; subtitle: string }> = {
  elderly: { label: "智慧养老", subtitle: "连续视觉事件辅助与人工复核" },
  workshop: { label: "工作室管理", subtitle: "关注物品位置变化与视频证据" },
  robot: { label: "机器人辅助", subtitle: "感知事件与执行端接口预留" },
  universal: { label: "通用视觉", subtitle: "基础事实与可插拔场景" },
};

function viewFromHash(hash: string): View {
  const candidate = hash.replace(/^#/, "") as View;
  return navItems.some((item) => item.id === candidate) ? candidate : "dashboard";
}

function errorMessage(error: unknown): string {
  return error instanceof Error && error.message ? error.message : "未知连接错误";
}

function connectionLabel(connection: RepositoryConnection): string {
  if (connection.status === "mock") return "Mock 演示数据";
  if (connection.status === "loading") return connection.mode === "real" ? "正在连接 Real API" : "正在加载 Mock";
  if (connection.status === "online") return "Real API 在线";
  return connection.mode === "real" ? "Real API 离线" : "Mock 加载失败";
}

function connectionDotClass(status: RepositoryConnectionStatus): string {
  if (status === "online" || status === "mock") return "green";
  if (status === "offline") return "red";
  return "";
}

function App() {
  const [mode, setMode] = useState<Mode>("mock");
  const [scenario, setScenario] = useState<Scenario>("elderly");
  const [view, setView] = useState<View>(() => viewFromHash(typeof window === "undefined" ? "" : window.location.hash));
  const [repo, setRepo] = useState<Repository>(() => createMockRepository());
  const [events, setEvents] = useState<UnifiedEvent[]>([]);
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [objects, setObjects] = useState<RegisteredObject[]>([]);
  const [persons, setPersons] = useState<RegisteredPerson[]>([]);
  const [loading, setLoading] = useState(true);
  const [connection, setConnection] = useState<RepositoryConnection>({ mode: "mock", status: "loading" });
  const [toast, setToast] = useState<string | null>(null);
  const [pluginsOpen, setPluginsOpen] = useState(false);

  useEffect(() => {
    function onHashChange() {
      setView(viewFromHash(window.location.hash));
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    const nextHash = `#${view}`;
    if (window.location.hash !== nextHash) window.history.replaceState(null, "", nextHash);
  }, [view]);

  useEffect(() => {
    const nextRepo = mode === "mock" ? createMockRepository() : createRealRepository(import.meta.env.VITE_AI_API_URL ?? "http://127.0.0.1:8010");
    let active = true;
    setRepo(nextRepo);
    setLoading(true);
    setConnection({ mode, status: "loading" });
    // Clear the previous source before any request starts. A late response from
    // the old source is ignored so Mock data cannot survive a failed Real load.
    setEvents([]);
    setPlugins([]);
    setObjects([]);
    setPersons([]);
    Promise.all([nextRepo.health(), nextRepo.listEvents(), nextRepo.listPlugins(), nextRepo.listObjects(), nextRepo.listPersons()])
      .then(([, nextEvents, nextPlugins, nextObjects, nextPersons]) => {
        if (!active) return;
        setEvents(nextEvents);
        setPlugins(nextPlugins);
        setObjects(nextObjects);
        setPersons(nextPersons);
        setConnection({ mode, status: mode === "mock" ? "mock" : "online" });
      })
      .catch((error: unknown) => {
        if (!active) return;
        const reason = errorMessage(error);
        setEvents([]);
        setPlugins([]);
        setObjects([]);
        setPersons([]);
        setConnection({ mode, status: "offline", reason });
        setToast(`${mode === "real" ? "Real API" : "Mock"} 数据源不可用：${reason}`);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [mode]);

  const pendingCount = events.filter((event) => event.review_status === "pending").length;
  const enabledCount = plugins.filter((plugin) => plugin.enabled).length;
  const evidenceCount = events.filter((event) => event.evidence.length > 0).length;

  function ensureActionAvailable(action: string): boolean {
    if (mode === "mock" || connection.status === "online") return true;
    setToast(`${connectionLabel(connection)}，${action}未执行${connection.reason ? `：${connection.reason}` : ""}`);
    return false;
  }

  async function review(event: UnifiedEvent, status: ReviewStatus) {
    if (!ensureActionAvailable("事件复核")) return;
    try {
      const updated = await repo.reviewEvent(event.event_id, status);
      setEvents((current) => current.map((item) => (item.event_id === updated.event_id ? updated : item)));
      setToast(status === "confirmed" ? "事件已确认，已写入复核记录" : "事件已驳回");
    } catch (error) {
      setToast(`事件复核失败：${errorMessage(error)}`);
    }
  }

  async function toggle(plugin: Plugin) {
    if (!ensureActionAvailable("插件操作")) return;
    try {
      const updated = await repo.togglePlugin(plugin.plugin_id, !plugin.enabled);
      setPlugins((current) => current.map((item) => (item.plugin_id === updated.plugin_id ? updated : item)));
      setToast(`${updated.name} 已${updated.enabled ? "启用" : "停用"}`);
    } catch (error) {
      setToast(`插件操作失败：${errorMessage(error)}`);
    }
  }

  async function runDemo() {
    if (!ensureActionAvailable("分析任务")) return;
    try {
      const source = mode === "mock" ? (scenario === "workshop" ? "mock://workshop-tool" : "mock://elderly-medication") : "camera.mp4";
      const job = await repo.createAnalysis(source);
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
      setToast(`分析任务 ${finalJob.status === "completed" ? "已完成" : finalJob.status === "failed" ? "失败" : finalJob.status === "stopped" ? "已停止" : "已提交"}`);
    } catch (error) {
      setToast(`分析任务失败：${errorMessage(error)}`);
    }
  }

  const currentScenario = scenarioCopy[scenario];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <nav className="main-nav primary-nav">
          {navItems.filter((item) => ["dashboard", "monitor", "events"].includes(item.id)).map((item) => {
            const Icon = item.icon;
            const label = item.id === "dashboard" ? "首页" : item.id === "monitor" ? "隐私监护" : "事件中心";
            return <button key={item.id} className={`nav-item ${view === item.id ? "active" : ""}`} onClick={() => setView(item.id)}><Icon size={20} /><span>{label}</span>{item.id === "events" && pendingCount > 0 && <em>{pendingCount}</em>}</button>;
          })}
        </nav>

        <section className={`sidebar-plugin-section ${pluginsOpen ? "open" : ""}`}>
          <button className="sidebar-plugin-toggle" onClick={() => setPluginsOpen((open) => !open)} aria-expanded={pluginsOpen}>
            <Network size={19} />
            <span>插件功能</span>
            <ChevronDown size={16} className="sidebar-plugin-chevron" />
          </button>
          {pluginsOpen && <div className="sidebar-plugin-list">
            {plugins.length === 0 ? <div className="sidebar-plugin-empty">暂无可用插件</div> : plugins.map((plugin) => {
              const displayName = plugin.plugin_id === "elderly_care" ? "用药辅助" : plugin.plugin_id === "workshop" ? "物品看护" : plugin.name;
              return <div className={`sidebar-plugin-row ${plugin.enabled ? "enabled" : ""}`} key={plugin.plugin_id}>
                <div className="sidebar-plugin-icon">{plugin.plugin_id === "workshop" ? <Box size={18} /> : <ClipboardCheck size={18} />}</div>
                <div className="sidebar-plugin-copy"><strong>{displayName}</strong><span><i className={`mini-status ${plugin.enabled ? "on" : ""}`} />{plugin.enabled ? "已启用" : "未启用"}</span></div>
                <button className={`sidebar-mini-switch ${plugin.enabled ? "on" : ""}`} onClick={() => toggle(plugin)} aria-label={`${plugin.enabled ? "停用" : "启用"}${displayName}`}><i /></button>
              </div>;
            })}
            <button className="sidebar-plugin-manage" onClick={() => setView("plugins")}>管理全部插件 <ArrowUpRight size={14} /></button>
          </div>}
        </section>

        <div className="sidebar-admin">
          <button onClick={() => setView("registry")} className={view === "registry" ? "active" : ""}><Users size={18} /><span>对象与人员</span></button>
          <button onClick={() => setView("settings")} className={view === "settings" ? "active" : ""}><Settings size={18} /><span>系统设置</span></button>
        </div>
      </aside>

      <main className="main-content">
        {view !== "monitor" && <header className="topbar"><div className="breadcrumbs"><span>控制台</span><span>/</span><strong>{currentScenario.label}</strong></div><div className="top-actions"><div className="mode-toggle"><button className={mode === "mock" ? "selected" : ""} onClick={() => setMode("mock")}>Mock</button><button className={mode === "real" ? "selected" : ""} onClick={() => setMode("real")}>Real API</button></div><button className="icon-button"><Bell size={18} /><i /></button><div className="top-avatar">未</div></div></header>}
        <div className={`content-wrap ${view === "monitor" ? "monitor-content-wrap" : ""}`}>
          {view !== "monitor" && <section className="page-intro"><div><div className="eyebrow"><span className="live-pulse" /> LIVE OPERATIONS / 01</div><h1>{currentScenario.label} <span>控制台</span></h1><p>{currentScenario.subtitle} · {mode === "mock" ? "离线演示数据" : "AI REST 数据源"}</p></div><div className="intro-actions"><div className={`connection-state ${connection.status}`}><span className={`status-dot ${connectionDotClass(connection.status)}`} /><strong>{connectionLabel(connection)}</strong>{connection.reason && <small title={connection.reason}>{connection.reason}</small>}</div><label className="select-wrap"><SlidersHorizontal size={15} /><select value={scenario} onChange={(event) => setScenario(event.target.value as Scenario)}>{Object.entries(scenarioCopy).map(([key, item]) => <option key={key} value={key}>{item.label}</option>)}</select></label><button className="primary-button" onClick={runDemo}><Play size={15} fill="currentColor" /> 开始一次分析</button></div></section>}

          {view === "dashboard" && <Dashboard events={events} plugins={plugins} pendingCount={pendingCount} enabledCount={enabledCount} evidenceCount={evidenceCount} loading={loading} mode={mode} connection={connection} onNavigate={setView} onReview={review} />}
          {view === "monitor" && <MonitorLive scenario={scenario} mode={mode} connection={connection} plugins={plugins} events={events} objects={objects} onToggle={toggle} onRun={runDemo} onModeChange={setMode} />}
          {view === "events" && <EventsViewInteractive events={events} onReview={review} />}
          {view === "plugins" && <PluginsView plugins={plugins} connection={connection} onToggle={toggle} />}
          {view === "registry" && <RegistryView repo={repo} mode={mode} connection={connection} objects={objects} persons={persons} onObjects={setObjects} onPersons={setPersons} onToast={setToast} />}
          {view === "settings" && <SettingsView mode={mode} scenario={scenario} connection={connection} />}
        </div>
      </main>
      {toast && <div className="toast"><Check size={16} /> {toast}<button onClick={() => setToast(null)}><X size={14} /></button></div>}
    </div>
  );
}

function Dashboard({ events, plugins, pendingCount, enabledCount, evidenceCount, loading, mode, connection, onNavigate, onReview }: { events: UnifiedEvent[]; plugins: Plugin[]; pendingCount: number; enabledCount: number; evidenceCount: number; loading: boolean; mode: Mode; connection: RepositoryConnection; onNavigate: (view: View) => void; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  const recent = events.slice(0, 3);
  return <>
    <section className="metric-grid"><Metric icon={Activity} label="今日事件" value={loading ? "—" : String(events.length).padStart(2, "0")} trend="实时" tone="cyan" /><Metric icon={ClipboardCheck} label="待人工复核" value={String(pendingCount).padStart(2, "0")} trend={pendingCount ? "需要关注" : "已清空"} tone="amber" /><Metric icon={Network} label="运行中插件" value={`${enabledCount}/${plugins.length}`} trend="全局状态" tone="violet" /><Metric icon={ShieldCheck} label="证据时间窗" value={`${evidenceCount}/${events.length || 0}`} trend="可定位" tone="green" /></section>
    <section className="dashboard-grid"><div className="panel monitor-panel"><div className="panel-heading"><div><span className="panel-kicker">PRIMARY SOURCE / 01</span><h2>客厅摄像头 <span className="live-tag">{mode === "mock" ? "MOCK" : "未接入"}</span></h2></div><button className="ghost-button" onClick={() => onNavigate("monitor")}>展开监控 <ArrowUpRight size={15} /></button></div><div className="video-preview"><div className="video-grid" /><div className="camera-label"><span className="status-dot red" /> living-room-cam-01 <span>00:08:42</span></div><div className="video-center"><div className="play-ring"><Play size={22} fill="currentColor" /></div><p>{mode === "mock" ? "Mock 视频源 · 等待真实流接入" : connection.status === "offline" ? `Real API 离线：${connection.reason ?? "未连接"}` : "Real API 已连接 · 媒体流未接入"}</p></div><div className="video-scan" /></div><div className="stream-footer"><span><Gauge size={14} /> 事件管线 <b>{connection.status === "online" ? "已连接" : connection.status === "mock" ? "Mock" : "未就绪"}</b></span><span><Radio size={14} /> 延迟 <b>—</b></span><span><Eye size={14} /> 证据 <b>{mode === "mock" ? "演示" : "待接入"}</b></span></div></div><div className="panel scene-panel"><div className="panel-heading"><div><span className="panel-kicker">SCENARIO PROFILE</span><h2>场景能力</h2></div><button className="more-button" onClick={() => onNavigate("plugins")}>管理</button></div><div className="scene-orbit"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="orbit-core"><Sparkles size={22} /><span>VISUAL<br />FACTS</span></div><div className="orbit-label label-a"><b>人</b><span>轨迹</span></div><div className="orbit-label label-b"><b>物</b><span>关系</span></div><div className="orbit-label label-c"><b>时</b><span>证据</span></div></div><div className="scene-note"><span className={`status-dot ${connectionDotClass(connection.status)}`} /><span>{connection.status === "offline" ? "等待数据源恢复" : connection.status === "loading" ? "正在连接数据源" : "通用视觉底座运行中"}</span><b>{enabledCount} 个插件已启用</b></div></div></section>
    <section className="lower-grid"><div className="panel events-panel"><div className="panel-heading"><div><span className="panel-kicker">REVIEW QUEUE / {String(events.length).padStart(2, "0")}</span><h2>最近事件</h2></div><button className="more-button" onClick={() => onNavigate("events")}>查看全部 <ArrowUpRight size={14} /></button></div>{recent.length ? recent.map((event) => <EventRow key={event.event_id} event={event} onReview={onReview} />) : <EmptyState text="还没有事件" />}</div><div className="panel readiness-panel"><div className="panel-heading"><div><span className="panel-kicker">DELIVERY READINESS</span><h2>交付进度</h2></div><span className="readiness-score">{Math.min(99, 42 + enabledCount * 10)}%</span></div><Progress label="AI 核心闭环" value={78} /><Progress label="前端演示" value={62} /><Progress label="真实流适配" value={18} muted /><Progress label="机器人融合" value={8} muted /><div className="readiness-foot"><span>当前为原型阶段</span><span>Mock 可演示</span></div></div></section>
  </>;
}

function Metric({ icon: Icon, label, value, trend, tone }: { icon: typeof Activity; label: string; value: string; trend: string; tone: string }) { return <div className={`metric-card ${tone}`}><div className="metric-top"><div className="metric-icon"><Icon size={17} /></div><span>{trend}</span></div><strong>{value}</strong><label>{label}</label><div className="metric-line" /></div>; }
function Progress({ label, value, muted }: { label: string; value: number; muted?: boolean }) { return <div className={`progress-row ${muted ? "muted" : ""}`}><div><span>{label}</span><b>{value}%</b></div><div className="progress-track"><i style={{ width: `${value}%` }} /></div></div>; }
function EventRow({ event, onReview }: { event: UnifiedEvent; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) { return <div className="event-row"><div className={`event-type ${event.severity}`}><Activity size={16} /></div><div className="event-main"><div><strong>{event.title}</strong><span className={`review-badge ${event.review_status}`}>{event.review_status === "pending" ? "待复核" : event.review_status === "confirmed" ? "已确认" : "已驳回"}</span></div><p>{event.location ?? "未标注位置"} · {Math.round(event.confidence * 100)}% 置信度</p></div><div className="event-time">{relativeTime(event.started_at)}</div>{event.review_status === "pending" && <div className="row-actions"><button title="确认" onClick={() => onReview(event, "confirmed")}><Check size={15} /></button><button title="驳回" onClick={() => onReview(event, "rejected")}><X size={15} /></button></div>}</div>; }
function EmptyState({ text }: { text: string }) { return <div className="empty-state"><Sparkles size={18} /><span>{text}</span></div>; }

function Signal({ label, value, color }: { label: string; value: string; color: string }) { return <div className="signal"><span className={`signal-dot ${color}`} /><span>{label}</span><b>{value}</b></div>; }

function EventsView({ events, onReview }: { events: UnifiedEvent[]; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReviewStatus | "all">("all");
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = events.filter((event) => {
    if (status !== "all" && event.review_status !== status) return false;
    if (!normalizedQuery) return true;
    const haystack = [
      event.title,
      event.description,
      event.plugin_id,
      event.source_id,
      event.location ?? "",
      String(event.object?.label ?? ""),
      String(event.subject?.label ?? ""),
    ].join(" ").toLowerCase();
    return haystack.includes(normalizedQuery);
  });
  return <section className="panel full-panel"><div className="panel-heading"><div><span className="panel-kicker">EVENT CENTER / HISTORY</span><h2>事件中心</h2></div><div className="filter-row"><label className="search-box"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索事件、位置或对象" /></label><label className="filter-select"><SlidersHorizontal size={15} /><select value={status} onChange={(event) => setStatus(event.target.value as ReviewStatus | "all")}><option value="all">全部状态</option><option value="pending">待复核</option><option value="confirmed">已确认</option><option value="rejected">已驳回</option></select></label></div></div><div className="event-table"><div className="event-table-head"><span>事件</span><span>来源</span><span>置信度</span><span>状态</span><span>时间</span><span /></div>{filtered.length === 0 ? <EmptyState text="没有匹配事件" /> : filtered.map((event) => { const evidenceStatus = event.evidence[0]?.status ?? "unavailable"; const evidenceText = evidenceStatus === "fixture" ? "测试 fixture" : evidenceStatus === "provided_unverified" ? "已提供·未验证" : evidenceStatus === "available" ? "可回放" : "待解析"; return <div className="event-table-row" key={event.event_id}><div className="table-event"><div className={`event-type ${event.severity}`}><Activity size={15} /></div><div><strong>{event.title}</strong><small>{event.plugin_id} · {event.object?.label as string ?? "基础事实"}</small></div></div><span className="source-cell"><strong>{event.source_id}</strong><small className="evidence-inline">证据：{evidenceText}</small></span><span className="confidence"><i style={{ width: `${event.confidence * 100}%` }} />{Math.round(event.confidence * 100)}%</span><span className={`review-badge ${event.review_status}`}>{event.review_status === "pending" ? "待复核" : event.review_status === "confirmed" ? "已确认" : "已驳回"}</span><span className="table-time">{relativeTime(event.started_at)}</span><button className="table-open"><ArrowUpRight size={15} /></button>{event.review_status === "pending" && <div className="table-row-actions"><button onClick={() => onReview(event, "confirmed")}><Check size={14} /></button><button onClick={() => onReview(event, "rejected")}><X size={14} /></button></div>}</div>; })}</div></section>;
}

function PluginsView({ plugins, connection, onToggle }: { plugins: Plugin[]; connection: RepositoryConnection; onToggle: (plugin: Plugin) => Promise<void> }) { return <section className="plugin-layout"><div className="panel plugin-main"><div className="panel-heading"><div><span className="panel-kicker">EXTENSION RUNTIME</span><h2>插件能力</h2></div><span className="status-summary"><span className={`status-dot ${connectionDotClass(connection.status)}`} /> {connection.status === "offline" ? "数据源离线" : `${plugins.filter((item) => item.enabled).length} 个运行中`}</span></div><p className="panel-lead">插件在启动时从 <code>plugins/</code> 自动发现。场景模式只改变界面重点，不会替你关闭其他插件。</p>{plugins.map((plugin) => <div className="plugin-row" key={plugin.plugin_id}><div className={`plugin-symbol ${plugin.enabled ? "on" : "off"}`}><Sparkles size={18} /></div><div className="plugin-copy"><div><strong>{plugin.name}</strong><span className="version">v{plugin.version}</span></div><p>{plugin.description}</p><small>{plugin.plugin_id} · {plugin.state}</small></div><button className={`switch ${plugin.enabled ? "on" : ""}`} onClick={() => onToggle(plugin)} aria-label={`切换${plugin.name}`}><i /></button></div>)}</div><div className="panel plugin-note"><span className="panel-kicker">PLUGIN CONTRACT</span><h2>统一事件出口</h2><p>前端只消费统一事件，不直接理解插件内部算法。插件异常会进入 degraded/error 状态，主服务和其他插件继续运行。</p><div className="contract-list"><span><Check size={14} /> 自动发现</span><span><Check size={14} /> 全局启停</span><span><Check size={14} /> 并行运行</span><span><Check size={14} /> 独立测试</span></div></div></section>; }

function RegistryView({ repo, mode, connection, objects, persons, onObjects, onPersons, onToast }: { repo: Repository; mode: Mode; connection: RepositoryConnection; objects: RegisteredObject[]; persons: RegisteredPerson[]; onObjects: (items: RegisteredObject[]) => void; onPersons: (items: RegisteredPerson[]) => void; onToast: (message: string) => void }) {
  const [objectName, setObjectName] = useState("");
  const [personName, setPersonName] = useState("");
  const canMutate = mode === "mock" || connection.status === "online";
  const blockedMessage = () => onToast(`${connectionLabel(connection)}，登记操作未执行${connection.reason ? `：${connection.reason}` : ""}`);

  async function addObject() {
    if (!objectName.trim()) return;
    if (!canMutate) return blockedMessage();
    try {
      await repo.createObject(objectName.trim());
      onObjects(await repo.listObjects());
      setObjectName("");
      onToast("关注对象已登记");
    } catch (error) {
      onToast(`对象登记失败：${errorMessage(error)}`);
    }
  }

  async function addPerson() {
    if (!personName.trim()) return;
    if (!canMutate) return blockedMessage();
    try {
      await repo.createPerson(personName.trim(), "unknown");
      onPersons(await repo.listPersons());
      setPersonName("");
      onToast("人员已登记");
    } catch (error) {
      onToast(`人员登记失败：${errorMessage(error)}`);
    }
  }

  return <section className="registry-grid"><div className="panel registry-panel"><div className="panel-heading"><div><span className="panel-kicker">REGISTERED OBJECTS</span><h2>关注对象</h2></div><span className="count-pill">{objects.length}</span></div><p className="panel-lead">上传少量参考图即可注册长尾物品；当前演示先保存名称与引用位。</p><div className="inline-form"><input value={objectName} onChange={(event) => setObjectName(event.target.value)} placeholder="例如：这个药盒 / 这把电钻" /><button onClick={addObject}><Plus size={15} /> 登记</button></div>{objects.map((item) => <div className="registry-row" key={item.object_id}><div className="registry-icon"><Box size={16} /></div><div><strong>{item.name}</strong><span>{item.description}</span></div><span className="active-label">{item.status}</span></div>)}</div><div className="panel registry-panel"><div className="panel-heading"><div><span className="panel-kicker">REGISTERED PEOPLE</span><h2>人员身份</h2></div><span className="count-pill">{persons.length}</span></div><p className="panel-lead">支持注册式人员区分；识别不确定时保留 unknown/ambiguous 状态。</p><div className="inline-form"><input value={personName} onChange={(event) => setPersonName(event.target.value)} placeholder="例如：爷爷 / 家属 / 工作人员" /><button onClick={addPerson}><Plus size={15} /> 登记</button></div>{persons.map((item) => <div className="registry-row" key={item.person_id}><div className="registry-icon person"><Users size={16} /></div><div><strong>{item.display_name}</strong><span>{item.role}</span></div><span className="active-label">{item.status}</span></div>)}</div></section>;
}
function SettingsView({ mode, scenario, connection }: { mode: Mode; scenario: Scenario; connection: RepositoryConnection }) { return <section className="settings-grid"><div className="panel settings-main"><span className="panel-kicker">WORKSPACE SETTINGS</span><h2>系统设置</h2><div className="setting-item"><div><strong>数据源模式</strong><span>当前前端数据 provider</span></div><b className="setting-value">{mode === "mock" ? "Mock 演示" : connection.status === "online" ? "Real AI API 在线" : connection.status === "loading" ? "Real API 连接中" : "Real API 离线"}</b></div><div className="setting-item"><div><strong>当前场景</strong><span>只改变界面重点，不改变插件状态</span></div><b className="setting-value">{scenarioCopy[scenario].label}</b></div><div className="setting-item"><div><strong>API 地址</strong><span>Real 模式下的 AI 服务地址</span></div><code>{import.meta.env.VITE_AI_API_URL ?? "http://127.0.0.1:8010"}</code></div><div className="setting-item"><div><strong>隐私模式</strong><span>事件保存，不重复保存视频</span></div><span className="switch on"><i /></span></div></div><div className="panel settings-note"><ShieldCheck size={22} /><h3>证据边界</h3><p>事件用于辅助判断和人工复核。没有可用录像解析器时，界面会保留时间窗并标注“待解析”，不会伪造播放证据。</p><div className="note-tag"><Check size={13} /> 文档与实现保持同步</div></div></section>; }

function relativeTime(value: string) { const diff = Math.max(0, Date.now() - new Date(value).getTime()); const minutes = Math.round(diff / 60000); return minutes < 1 ? "刚刚" : minutes < 60 ? `${minutes} 分钟前` : `${Math.round(minutes / 60)} 小时前`; }

type PrivacyMode = "cartoon" | "skeleton";

type TimelineEntry = {
  id: string;
  time: string;
  title: string;
  detail: string;
  kind: "person" | "medicine" | "object" | "status";
};

function factLabel(factType: string): string {
  const labels: Record<string, string> = {
    hand_near_object: "手靠近物品",
    hand_to_face: "手靠近面部",
    pickup_candidate: "拿起物品",
    putdown_candidate: "放回物品",
    entered_zone: "进入区域",
    left_zone: "离开区域",
    motion: "发生移动",
    object_in_zone: "物品位于区域",
    object_detected: "检测到物品",
  };
  return labels[factType] ?? factType.replaceAll("_", " ");
}

function buildMonitorTimeline(mode: Mode, events: UnifiedEvent[], plugins: Plugin[]): TimelineEntry[] {
  if (mode === "mock") {
    const enabled = new Set(plugins.filter((plugin) => plugin.enabled).map((plugin) => plugin.plugin_id));
    const entries: TimelineEntry[] = [
      { id: "enter", time: "07:42", title: "进入客厅", detail: "连续轨迹建立", kind: "person" },
      { id: "settle", time: "08:12", title: "在沙发就座", detail: "持续静止", kind: "status" },
    ];
    if (enabled.has("elderly_care")) {
      entries.splice(1, 0,
        { id: "medicine-pick", time: "07:58", title: "拿起药盒", detail: "手接触药盒", kind: "medicine" },
        { id: "face", time: "08:01", title: "手靠近面部", detail: "疑似服药行为", kind: "medicine" },
        { id: "medicine-return", time: "08:05", title: "放回药盒", detail: "回到桌面区域", kind: "medicine" },
      );
    }
    if (enabled.has("workshop")) {
      entries.splice(Math.min(entries.length - 1, 3), 0, { id: "water", time: "08:04", title: "拿起水杯", detail: "物品位置变化", kind: "object" });
    }
    return entries;
  }

  const flattened = events.flatMap((event) =>
    event.facts.map((fact, index) => ({
      id: `${event.event_id}-${index}`,
      time: new Date(event.started_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }),
      title: factLabel(fact.fact_type),
      detail: event.location ?? event.title,
      kind: event.plugin_id === "elderly_care" ? "medicine" as const : event.object ? "object" as const : "status" as const,
    })),
  );
  return flattened.slice(0, 8);
}

function MonitorLive({ scenario, mode, connection, plugins, events, objects, onToggle, onRun, onModeChange }: {
  scenario: Scenario;
  mode: Mode;
  connection: RepositoryConnection;
  plugins: Plugin[];
  events: UnifiedEvent[];
  objects: RegisteredObject[];
  onToggle: (plugin: Plugin) => Promise<void>;
  onRun: () => Promise<void>;
  onModeChange: (mode: Mode) => void;
}) {
  const [session, setSession] = useState<LiveSession | null>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [privacyMode, setPrivacyMode] = useState<PrivacyMode>("cartoon");

  useEffect(() => {
    if (mode === "mock") {
      setSession(null);
      setMediaError(null);
      return;
    }
    const baseUrl = import.meta.env.VITE_MAKERVERSE_API_URL as string | undefined;
    if (!baseUrl) {
      setSession(null);
      setMediaError("未配置 VITE_MAKERVERSE_API_URL");
      return;
    }
    const adapter = createMakerverseLiveAdapter(
      baseUrl,
      import.meta.env.VITE_MAKERVERSE_TOKEN as string | undefined,
    );
    let cancelled = false;
    setMediaError(null);
    adapter.listOnline()
      .then(async (online) => {
        if (!online[0]) return null;
        const endpoint = await adapter.getEndpoint(online[0].id);
        return { ...online[0], ...endpoint };
      })
      .then((next) => {
        if (!cancelled) setSession(next);
      })
      .catch((error: Error) => {
        if (!cancelled) {
          setSession(null);
          setMediaError(error.message);
        }
      });
    return () => { cancelled = true; };
  }, [mode]);

  const playback = mode === "mock"
    ? classifyPlaybackUrl("mock://living-room-cam-01")
    : session ? choosePlayback(session) : classifyPlaybackUrl(null);
  const realReason = connection.status === "offline"
    ? `Real API 离线：${connection.reason ?? "未连接"}`
    : mediaError ?? playback.reason;
  const enabledPlugins = plugins.filter((plugin) => plugin.enabled);
  const timeline = useMemo(() => buildMonitorTimeline(mode, events, plugins), [mode, events, plugins]);
  const medicationEvents = events.filter((event) => event.plugin_id === "elderly_care").slice(0, 2);
  const displayObjects = mode === "mock" && scenario === "elderly"
    ? [
        objects.find((item) => item.name.includes("药")) ?? { object_id: "mock-med", name: "降压药盒", description: "Mock 演示对象", reference_uris: [], status: "active" },
        { object_id: "mock-water", name: "水杯", description: "Mock 演示对象", reference_uris: [], status: "active" },
      ]
    : objects.slice(0, 2);

  return <section className="privacy-monitor-page">
    <header className="privacy-page-header">
      <div className="privacy-title-block">
        <h1>隐私监护</h1>
        <p>在保护隐私的前提下查看关键行为与物品状态</p>
      </div>
      <div className="privacy-header-tools">
        <div className="privacy-policy-note"><ShieldCheck size={18} /><span>界面不提供原始画面入口，仅展示骨骼/卡漫结果</span></div>
        <div className="privacy-mode-switch" role="group" aria-label="隐私显示模式">
          <button className={privacyMode === "cartoon" ? "active" : ""} onClick={() => setPrivacyMode("cartoon")}><Eye size={17} /> 卡漫模式</button>
          <button className={privacyMode === "skeleton" ? "active" : ""} onClick={() => setPrivacyMode("skeleton")}><Users size={17} /> 骨骼模式</button>
        </div>
        <div className="monitor-source-toggle" title="切换前端数据源">
          <button className={mode === "mock" ? "active" : ""} onClick={() => onModeChange("mock")}>Mock</button>
          <button className={mode === "real" ? "active" : ""} onClick={() => onModeChange("real")}>Real</button>
        </div>
      </div>
    </header>

    <div className="privacy-monitor-grid">
      <article className="privacy-video-card">
        <div className="privacy-stage">
          {mode === "mock" ? <PrivacyMockScene privacyMode={privacyMode} medicationEnabled={enabledPlugins.some((plugin) => plugin.plugin_id === "elderly_care")} objectEnabled={enabledPlugins.some((plugin) => plugin.plugin_id === "workshop")} /> :
            <div className="privacy-stream-placeholder"><ShieldCheck size={30} /><strong>隐私渲染流未接入</strong><span>隐私监护页不会直接回退到原始视频。{session ? `已发现媒体会话，等待骨骼/卡漫输出接口。` : realReason}</span></div>}
          <div className="camera-chip"><span className="camera-online-dot" /> 客厅 · Camera 01 <i /> {mode === "mock" ? "08:01:23" : session ? "LIVE" : "NO STREAM"}</div>
          <div className="privacy-player-controls"><button aria-label="暂停"><Pause size={19} fill="currentColor" /></button><span>08:01 / 10:00</span><div className="privacy-progress"><i /></div><button aria-label="运行分析" onClick={onRun}><Sparkles size={18} /></button></div>
        </div>
      </article>

      <aside className="privacy-side-column">
        <section className="privacy-info-card privacy-status-card">
          <div className="privacy-card-heading"><div><Activity size={20} /><strong>当前状态</strong></div><span className="healthy-pill"><i />正常</span></div>
          <div className="privacy-status-row"><Users size={17} /><span>人物</span><strong>{mode === "mock" ? "Person 01" : session ? "已发现" : "待接入"}</strong></div>
          <div className="privacy-status-row"><Sparkles size={17} /><span>当前动作</span><strong>{enabledPlugins.some((plugin) => plugin.plugin_id === "elderly_care") ? "手靠近药盒" : "基础轨迹"}</strong></div>
          <div className="privacy-status-row"><ShieldCheck size={17} /><span>停留区域</span><strong>客厅 · 茶几</strong></div>
          <div className="privacy-status-row"><ShieldCheck size={17} /><span>状态</span><strong className="status-ok">{connection.status === "offline" ? "数据源离线" : "正常"}</strong></div>
        </section>

        {enabledPlugins.map((plugin, index) => <PluginMonitorCard key={plugin.plugin_id} plugin={plugin} events={plugin.plugin_id === "elderly_care" ? medicationEvents : events.filter((event) => event.plugin_id === plugin.plugin_id).slice(0, 2)} objects={displayObjects} mode={mode} onToggle={onToggle} stretch={index === enabledPlugins.length - 1} />)}
        {enabledPlugins.length === 0 && <section className="privacy-info-card plugin-live-card plugin-live-empty"><Network size={24} /><strong>未启用场景插件</strong><span>展开左侧“插件功能”后启用需要的监护能力。</span></section>}
      </aside>
    </div>

    <ActionTimeline entries={timeline} />
  </section>;
}

function PrivacyMockScene({ privacyMode, medicationEnabled, objectEnabled }: { privacyMode: PrivacyMode; medicationEnabled: boolean; objectEnabled: boolean }) {
  return <div className={`privacy-mock-scene ${privacyMode}`}>
    <svg className="room-scene-svg" viewBox="0 0 1000 620" preserveAspectRatio="xMidYMid slice" aria-label="Mock 客厅隐私监护画面">
      <defs>
        <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f5eee4" /><stop offset="1" stopColor="#dfd2c0" /></linearGradient>
        <linearGradient id="floor" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#b98f6a" /><stop offset="1" stopColor="#765440" /></linearGradient>
        <linearGradient id="windowLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#dff3ff" /><stop offset="1" stopColor="#fbffff" /></linearGradient>
      </defs>
      <rect width="1000" height="410" fill="url(#wall)" />
      <polygon points="0,390 1000,360 1000,620 0,620" fill="url(#floor)" />
      <rect x="700" y="70" width="220" height="245" rx="4" fill="#9d775e" opacity=".55" />
      <rect x="714" y="82" width="92" height="220" fill="url(#windowLight)" />
      <rect x="814" y="82" width="92" height="220" fill="url(#windowLight)" />
      <rect x="80" y="300" width="420" height="145" rx="34" fill="#d6c6b7" />
      <rect x="105" y="270" width="175" height="65" rx="22" fill="#ece5dc" />
      <rect x="295" y="270" width="170" height="65" rx="22" fill="#b7b2a9" />
      <rect x="90" y="430" width="480" height="26" rx="8" fill="#8b684d" />
      <rect x="150" y="455" width="26" height="100" fill="#72533f" />
      <rect x="500" y="455" width="26" height="100" fill="#72533f" />
      <rect x="585" y="470" width="290" height="95" rx="48" fill="#eee6dc" opacity=".9" />
      <circle cx="130" cy="230" r="28" fill="#66845e" opacity=".85" />
      <circle cx="160" cy="210" r="34" fill="#7b9a6d" opacity=".85" />
      <rect x="135" y="235" width="28" height="75" rx="8" fill="#a77852" />

      <g className="cartoon-body">
        <circle cx="590" cy="205" r="54" fill="#f0c9ab" stroke="#69575a" strokeWidth="4" />
        <path d="M541 198c5-50 87-76 106-10-24-20-65-26-106 10Z" fill="#b8ada8" />
        <path d="M550 254 Q590 235 626 260 L655 390 Q610 418 554 389 Z" fill="#8b79a7" stroke="#564a63" strokeWidth="4" />
        <path d="M565 278 L510 365" stroke="#8b79a7" strokeWidth="30" strokeLinecap="round" />
        <path d="M620 280 L654 365" stroke="#8b79a7" strokeWidth="30" strokeLinecap="round" />
        <path d="M575 390 L570 535" stroke="#3f4651" strokeWidth="34" strokeLinecap="round" />
        <path d="M625 390 L640 535" stroke="#3f4651" strokeWidth="34" strokeLinecap="round" />
        <circle cx="572" cy="205" r="4" fill="#5d4f4d" /><circle cx="607" cy="205" r="4" fill="#5d4f4d" />
        <path d="M582 224 Q592 232 603 223" fill="none" stroke="#9b6a63" strokeWidth="3" strokeLinecap="round" />
      </g>

      <g className="skeleton-overlay">
        <g stroke="#5fa7ff" strokeWidth="5" strokeLinecap="round" fill="none">
          <path d="M590 250 L590 300 L563 345 L536 388" />
          <path d="M590 300 L621 344 L647 386" />
          <path d="M590 300 L579 400 L573 500" />
          <path d="M590 300 L621 401 L638 500" />
        </g>
        {[["590","250"],["590","300"],["563","345"],["536","388"],["621","344"],["647","386"],["579","400"],["573","500"],["621","401"],["638","500"]].map(([cx, cy]) => <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="8" fill="#ffffff" stroke="#5fa7ff" strokeWidth="4" />)}
      </g>
    </svg>
    <div className="person-label">Person 01</div>
    {medicationEnabled && <div className="object-detection medicine-box"><b>降压药盒</b><span /></div>}
    {objectEnabled && <div className="object-detection water-box"><b>水杯</b><span /></div>}
  </div>;
}

function PluginMonitorCard({ plugin, events, objects, mode, onToggle, stretch }: {
  plugin: Plugin;
  events: UnifiedEvent[];
  objects: RegisteredObject[];
  mode: Mode;
  onToggle: (plugin: Plugin) => Promise<void>;
  stretch: boolean;
}) {
  const isMedication = plugin.plugin_id === "elderly_care";
  const isObjectWatch = plugin.plugin_id === "workshop";
  const title = isMedication ? "用药辅助" : isObjectWatch ? "物品看护" : plugin.name;
  return <section className={`privacy-info-card plugin-live-card ${stretch ? "stretch" : ""}`}>
    <div className="privacy-card-heading">
      <div>{isObjectWatch ? <Box size={20} /> : <ClipboardCheck size={20} />}<strong>{title}</strong><span className="enabled-pill"><i />已启用</span></div>
      <button className="plugin-inline-toggle" onClick={() => onToggle(plugin)}>停用</button>
    </div>
    {isMedication ? <div className="plugin-live-list">
      {(events.length ? events : mode === "mock" ? [
        { event_id: "mock-med-1", title: "疑似服药行为", started_at: new Date(), review_status: "pending" },
        { event_id: "mock-med-2", title: "时间与计划匹配", started_at: new Date(), review_status: "pending" },
      ] : []).slice(0, 2).map((event: any, index: number) => <div className="plugin-live-row" key={event.event_id ?? index}><div className="plugin-live-thumb medicine-thumb" /><div><span>{index === 0 ? "07:58" : "08:05"}</span><strong>{event.title}</strong></div><em>{event.review_status === "pending" ? "待确认" : "已记录"}</em></div>)}
      {!events.length && mode !== "mock" && <div className="plugin-card-empty">等待用药相关事件</div>}
    </div> : isObjectWatch ? <div className="plugin-live-list">
      {(objects.length ? objects : mode === "mock" ? [{ object_id: "med", name: "降压药盒" }, { object_id: "water", name: "水杯" }] : []).slice(0, 2).map((item: any, index: number) => <div className="plugin-live-row object-row" key={item.object_id ?? index}><div className={`plugin-live-thumb ${index === 0 ? "medicine-thumb" : "water-thumb"}`} /><div><strong>{item.name}</strong><span>{mode === "mock" ? (index === 0 ? "最后位置：客厅 · 茶几" : "当前位置：茶几") : "等待位置事实"}</span></div><ArrowUpRight size={15} /></div>)}
    </div> : <div className="plugin-generic-state"><Sparkles size={18} /><span>{plugin.description}</span></div>}
  </section>;
}

function ActionTimeline({ entries }: { entries: TimelineEntry[] }) {
  if (!entries.length) return <section className="action-timeline-card"><div className="action-timeline-heading"><div><Activity size={20} /><strong>最近动作</strong></div></div><div className="timeline-empty">暂无最近动作</div></section>;
  const offsets = [2, -7, 4, -5, 5, -2, 7, -4];
  return <section className="action-timeline-card">
    <div className="action-timeline-heading"><div><Activity size={20} /><strong>最近动作</strong></div><span>根据当前启用插件动态更新</span></div>
    <div className="action-timeline-track">
      <svg viewBox="0 0 1000 70" preserveAspectRatio="none" aria-hidden="true"><path d="M0 36 C90 58 145 2 245 28 S400 56 505 25 S660 4 760 32 S900 5 1000 28" /></svg>
      <div className="action-timeline-items" style={{ gridTemplateColumns: `repeat(${entries.length}, minmax(120px, 1fr))` }}>
        {entries.map((entry, index) => <div className={`action-timeline-item ${entry.kind}`} key={entry.id} style={{ transform: `translateY(${offsets[index % offsets.length]}px)` }}>
          <i className="action-node" />
          <span className="action-time">{entry.time}</span>
          <strong>{entry.title}</strong>
          <small>{entry.detail}</small>
        </div>)}
      </div>
    </div>
  </section>;
}

function EventsViewInteractive({ events, onReview }: { events: UnifiedEvent[]; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ReviewStatus | "all">("all");
  const [selected, setSelected] = useState<UnifiedEvent | null>(null);
  const normalizedQuery = query.trim().toLowerCase();
  const filtered = events.filter((event) => {
    if (status !== "all" && event.review_status !== status) return false;
    if (!normalizedQuery) return true;
    return [event.title, event.description, event.plugin_id, event.source_id, event.location ?? "", String(event.object?.label ?? ""), String(event.subject?.label ?? "")]
      .join(" ").toLowerCase().includes(normalizedQuery);
  });
  return <section className="panel full-panel"><div className="panel-heading"><div><span className="panel-kicker">EVENT CENTER / HISTORY</span><h2>事件中心</h2></div><div className="filter-row"><label className="search-box"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索事件、位置或对象" /></label><label className="filter-select"><SlidersHorizontal size={15} /><select value={status} onChange={(event) => setStatus(event.target.value as ReviewStatus | "all")}><option value="all">全部状态</option><option value="pending">待复核</option><option value="confirmed">已确认</option><option value="rejected">已驳回</option></select></label></div></div><div className="event-table"><div className="event-table-head"><span>事件</span><span>来源</span><span>置信度</span><span>状态</span><span>时间</span><span /></div>{filtered.length === 0 ? <EmptyState text="没有匹配事件" /> : filtered.map((event) => { const evidenceStatus = event.evidence[0]?.status ?? "unavailable"; const evidenceText = evidenceStatus === "fixture" ? "测试 fixture" : evidenceStatus === "provided_unverified" ? "已提供·未验证" : evidenceStatus === "available" ? "可回放" : "待解析"; return <div className="event-table-row" key={event.event_id}><div className="table-event"><div className={`event-type ${event.severity}`}><Activity size={15} /></div><div><strong>{event.title}</strong><small>{event.plugin_id} · {event.object?.label as string ?? "基础事实"}</small></div></div><span className="source-cell"><strong>{event.source_id}</strong><small className="evidence-inline">证据：{evidenceText}</small></span><span className="confidence"><i style={{ width: `${event.confidence * 100}%` }} />{Math.round(event.confidence * 100)}%</span><span className={`review-badge ${event.review_status}`}>{event.review_status === "pending" ? "待复核" : event.review_status === "confirmed" ? "已确认" : "已驳回"}</span><span className="table-time">{relativeTime(event.started_at)}</span><button className="table-open" onClick={() => setSelected(event)} title="查看事件详情"><ArrowUpRight size={15} /></button>{event.review_status === "pending" && <div className="table-row-actions"><button onClick={() => onReview(event, "confirmed")}><Check size={14} /></button><button onClick={() => onReview(event, "rejected")}><X size={14} /></button></div>}</div>; })}</div>{selected && <EventDetail event={selected} onClose={() => setSelected(null)} onReview={onReview} />}</section>;
}

function EventDetail({ event, onClose, onReview }: { event: UnifiedEvent; onClose: () => void; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  async function review(status: ReviewStatus) {
    await onReview(event, status);
    onClose();
  }
  return <div className="event-drawer-backdrop" onClick={onClose}><aside className="event-drawer" onClick={(click) => click.stopPropagation()}><div className="drawer-heading"><div><span className="panel-kicker">EVENT DETAIL / {event.plugin_id}</span><h2>{event.title}</h2></div><button className="icon-button" onClick={onClose}><X size={16} /></button></div><p className="drawer-description">{event.description}</p><div className="drawer-facts"><div><span>来源</span><strong>{event.source_id}</strong></div><div><span>置信度</span><strong>{Math.round(event.confidence * 100)}%</strong></div><div><span>时间窗</span><strong>{event.started_at} → {event.ended_at}</strong></div><div><span>位置</span><strong>{event.location ?? "未标注"}</strong></div></div><h3>基础事实</h3><div className="fact-list">{event.facts.length ? event.facts.map((fact, index) => <div key={`${fact.fact_type}-${index}`}><b>{fact.fact_type}</b><span>{Math.round(fact.confidence * 100)}% · {fact.location ?? "未标注位置"}</span></div>) : <span className="drawer-muted">没有附加事实</span>}</div><h3>证据时间窗</h3><div className="evidence-list">{event.evidence.length ? event.evidence.map((evidence, index) => <div key={`${evidence.source_id}-${index}`}><b>{evidence.status}</b><span>{evidence.source_id}</span><small>{evidence.started_at} → {evidence.ended_at}</small>{evidence.uri && evidence.status === "available" ? <a className="evidence-open" href={evidence.uri} target="_blank" rel="noreferrer">打开证据回放</a> : <small className="evidence-unavailable">回放地址未验证</small>}</div>) : <span className="drawer-muted">没有可解析证据；不能伪造回放地址</span>}</div>{event.review_status === "pending" && <div className="drawer-actions"><button className="primary-button" onClick={() => review("confirmed")}><Check size={15} /> 确认事件</button><button className="ghost-button drawer-reject" onClick={() => review("rejected")}><X size={15} /> 驳回</button></div>}</aside></div>;
}

export default App;
