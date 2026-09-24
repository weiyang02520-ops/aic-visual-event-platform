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
import type { LiveSession, Mode, Plugin, RegisteredObject, RegisteredPerson, Repository, ReviewStatus, Scenario, UnifiedEvent, View } from "./types";

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
  const [toast, setToast] = useState<string | null>(null);

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
    setRepo(nextRepo);
    setLoading(true);
    Promise.all([nextRepo.listEvents(), nextRepo.listPlugins(), nextRepo.listObjects(), nextRepo.listPersons()])
      .then(([nextEvents, nextPlugins, nextObjects, nextPersons]) => {
        setEvents(nextEvents);
        setPlugins(nextPlugins);
        setObjects(nextObjects);
        setPersons(nextPersons);
      })
      .catch((error: Error) => setToast(`数据源连接失败：${error.message}`))
      .finally(() => setLoading(false));
  }, [mode]);

  const pendingCount = events.filter((event) => event.review_status === "pending").length;
  const enabledCount = plugins.filter((plugin) => plugin.enabled).length;
  const evidenceCount = events.filter((event) => event.evidence.length > 0).length;

  async function review(event: UnifiedEvent, status: ReviewStatus) {
    const updated = await repo.reviewEvent(event.event_id, status);
    setEvents((current) => current.map((item) => (item.event_id === updated.event_id ? updated : item)));
    setToast(status === "confirmed" ? "事件已确认，已写入复核记录" : "事件已驳回");
  }

  async function toggle(plugin: Plugin) {
    const updated = await repo.togglePlugin(plugin.plugin_id, !plugin.enabled);
    setPlugins((current) => current.map((item) => (item.plugin_id === updated.plugin_id ? updated : item)));
    setToast(`${updated.name} 已${updated.enabled ? "启用" : "停用"}`);
  }

  async function runDemo() {
    const job = await repo.createAnalysis(scenario === "workshop" ? "mock://workshop-tool" : "mock://elderly-medication");
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
  }

  const currentScenario = scenarioCopy[scenario];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Sparkles size={18} /></div><div><strong>sentinel</strong><span>VISION OPERATIONS</span></div></div>
        <div className="workspace-switch"><span className="status-dot" /> 演示工作区 <ChevronDown size={14} /></div>
        <nav className="main-nav">
          <span className="nav-caption">工作台</span>
          {navItems.map((item) => {
            const Icon = item.icon;
            return <button key={item.id} className={`nav-item ${view === item.id ? "active" : ""}`} onClick={() => setView(item.id)}><Icon size={17} /><span>{item.label}</span>{item.id === "events" && pendingCount > 0 && <em>{pendingCount}</em>}</button>;
          })}
        </nav>
        <div className="sidebar-bottom"><div className="health-card"><div className="health-heading"><span className="status-dot green" /> 系统状态 <span>正常</span></div><div className="health-line"><span>AI Engine</span><b>在线</b></div><div className="health-line"><span>媒体流</span><b className="muted">Mock</b></div><div className="health-line"><span>机器人适配</span><b className="muted">预留</b></div></div><div className="user-chip"><div className="avatar">未</div><div><strong>未央</strong><span>项目成员</span></div><CircleHelp size={16} /></div></div>
      </aside>

      <main className="main-content">
        <header className="topbar"><div className="breadcrumbs"><span>控制台</span><span>/</span><strong>{currentScenario.label}</strong></div><div className="top-actions"><div className="mode-toggle"><button className={mode === "mock" ? "selected" : ""} onClick={() => setMode("mock")}>Mock</button><button className={mode === "real" ? "selected" : ""} onClick={() => setMode("real")}>Real API</button></div><button className="icon-button"><Bell size={18} /><i /></button><div className="top-avatar">未</div></div></header>
        <div className="content-wrap">
          <section className="page-intro"><div><div className="eyebrow"><span className="live-pulse" /> LIVE OPERATIONS / 01</div><h1>{currentScenario.label} <span>控制台</span></h1><p>{currentScenario.subtitle} · {mode === "mock" ? "离线演示数据" : "AI REST 数据源"}</p></div><div className="intro-actions"><label className="select-wrap"><SlidersHorizontal size={15} /><select value={scenario} onChange={(event) => setScenario(event.target.value as Scenario)}>{Object.entries(scenarioCopy).map(([key, item]) => <option key={key} value={key}>{item.label}</option>)}</select></label><button className="primary-button" onClick={runDemo}><Play size={15} fill="currentColor" /> 开始一次分析</button></div></section>

          {view === "dashboard" && <Dashboard events={events} plugins={plugins} pendingCount={pendingCount} enabledCount={enabledCount} evidenceCount={evidenceCount} loading={loading} onNavigate={setView} onReview={review} />}
          {view === "monitor" && <MonitorLive scenario={scenario} mode={mode} onRun={runDemo} />}
          {view === "events" && <EventsViewInteractive events={events} onReview={review} />}
          {view === "plugins" && <PluginsView plugins={plugins} onToggle={toggle} />}
          {view === "registry" && <RegistryView repo={repo} objects={objects} persons={persons} onObjects={setObjects} onPersons={setPersons} onToast={setToast} />}
          {view === "settings" && <SettingsView mode={mode} scenario={scenario} />}
        </div>
      </main>
      {toast && <div className="toast"><Check size={16} /> {toast}<button onClick={() => setToast(null)}><X size={14} /></button></div>}
    </div>
  );
}

function Dashboard({ events, plugins, pendingCount, enabledCount, evidenceCount, loading, onNavigate, onReview }: { events: UnifiedEvent[]; plugins: Plugin[]; pendingCount: number; enabledCount: number; evidenceCount: number; loading: boolean; onNavigate: (view: View) => void; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) {
  const recent = events.slice(0, 3);
  return <>
    <section className="metric-grid"><Metric icon={Activity} label="今日事件" value={loading ? "—" : String(events.length).padStart(2, "0")} trend="实时" tone="cyan" /><Metric icon={ClipboardCheck} label="待人工复核" value={String(pendingCount).padStart(2, "0")} trend={pendingCount ? "需要关注" : "已清空"} tone="amber" /><Metric icon={Network} label="运行中插件" value={`${enabledCount}/${plugins.length}`} trend="全局状态" tone="violet" /><Metric icon={ShieldCheck} label="证据时间窗" value={`${evidenceCount}/${events.length || 0}`} trend="可定位" tone="green" /></section>
    <section className="dashboard-grid"><div className="panel monitor-panel"><div className="panel-heading"><div><span className="panel-kicker">PRIMARY SOURCE / 01</span><h2>客厅摄像头 <span className="live-tag">LIVE</span></h2></div><button className="ghost-button" onClick={() => onNavigate("monitor")}>展开监控 <ArrowUpRight size={15} /></button></div><div className="video-preview"><div className="video-grid" /><div className="camera-label"><span className="status-dot red" /> living-room-cam-01 <span>00:08:42</span></div><div className="video-center"><div className="play-ring"><Play size={22} fill="currentColor" /></div><p>Mock 视频源 · 等待真实流接入</p></div><div className="video-scan" /></div><div className="stream-footer"><span><Gauge size={14} /> 事件管线 <b>稳定</b></span><span><Radio size={14} /> 延迟 <b>—</b></span><span><Eye size={14} /> 证据 <b>已挂接</b></span></div></div><div className="panel scene-panel"><div className="panel-heading"><div><span className="panel-kicker">SCENARIO PROFILE</span><h2>场景能力</h2></div><button className="more-button" onClick={() => onNavigate("plugins")}>管理</button></div><div className="scene-orbit"><div className="orbit-ring ring-one" /><div className="orbit-ring ring-two" /><div className="orbit-core"><Sparkles size={22} /><span>VISUAL<br />FACTS</span></div><div className="orbit-label label-a"><b>人</b><span>轨迹</span></div><div className="orbit-label label-b"><b>物</b><span>关系</span></div><div className="orbit-label label-c"><b>时</b><span>证据</span></div></div><div className="scene-note"><span className="status-dot green" /><span>通用视觉底座运行中</span><b>{enabledCount} 个插件已启用</b></div></div></section>
    <section className="lower-grid"><div className="panel events-panel"><div className="panel-heading"><div><span className="panel-kicker">REVIEW QUEUE / {String(events.length).padStart(2, "0")}</span><h2>最近事件</h2></div><button className="more-button" onClick={() => onNavigate("events")}>查看全部 <ArrowUpRight size={14} /></button></div>{recent.length ? recent.map((event) => <EventRow key={event.event_id} event={event} onReview={onReview} />) : <EmptyState text="还没有事件" />}</div><div className="panel readiness-panel"><div className="panel-heading"><div><span className="panel-kicker">DELIVERY READINESS</span><h2>交付进度</h2></div><span className="readiness-score">{Math.min(99, 42 + enabledCount * 10)}%</span></div><Progress label="AI 核心闭环" value={78} /><Progress label="前端演示" value={62} /><Progress label="真实流适配" value={18} muted /><Progress label="机器人融合" value={8} muted /><div className="readiness-foot"><span>当前为原型阶段</span><span>Mock 可演示</span></div></div></section>
  </>;
}

function Metric({ icon: Icon, label, value, trend, tone }: { icon: typeof Activity; label: string; value: string; trend: string; tone: string }) { return <div className={`metric-card ${tone}`}><div className="metric-top"><div className="metric-icon"><Icon size={17} /></div><span>{trend}</span></div><strong>{value}</strong><label>{label}</label><div className="metric-line" /></div>; }
function Progress({ label, value, muted }: { label: string; value: number; muted?: boolean }) { return <div className={`progress-row ${muted ? "muted" : ""}`}><div><span>{label}</span><b>{value}%</b></div><div className="progress-track"><i style={{ width: `${value}%` }} /></div></div>; }
function EventRow({ event, onReview }: { event: UnifiedEvent; onReview: (event: UnifiedEvent, status: ReviewStatus) => Promise<void> }) { return <div className="event-row"><div className={`event-type ${event.severity}`}><Activity size={16} /></div><div className="event-main"><div><strong>{event.title}</strong><span className={`review-badge ${event.review_status}`}>{event.review_status === "pending" ? "待复核" : event.review_status === "confirmed" ? "已确认" : "已驳回"}</span></div><p>{event.location ?? "未标注位置"} · {Math.round(event.confidence * 100)}% 置信度</p></div><div className="event-time">{relativeTime(event.started_at)}</div>{event.review_status === "pending" && <div className="row-actions"><button title="确认" onClick={() => onReview(event, "confirmed")}><Check size={15} /></button><button title="驳回" onClick={() => onReview(event, "rejected")}><X size={15} /></button></div>}</div>; }
function EmptyState({ text }: { text: string }) { return <div className="empty-state"><Sparkles size={18} /><span>{text}</span></div>; }

function Monitor({ scenario, mode, onRun }: { scenario: Scenario; mode: Mode; onRun: () => Promise<void> }) { const playback = classifyPlaybackUrl(mode === "mock" ? "mock://living-room-cam-01" : null); return <section className="monitor-layout"><div className="panel large-video"><div className="panel-heading"><div><span className="panel-kicker">LIVE MONITOR / CAMERA 01</span><h2>客厅摄像头 <span className="live-tag">LIVE</span></h2></div><div className="monitor-actions"><span className="quality-pill">1080P · {mode === "mock" ? "MOCK" : "REAL"}</span><button className="icon-button"><Pause size={16} /></button></div></div><div className="video-preview expanded"><div className="video-grid" /><div className="video-center"><div className="play-ring"><Play size={24} fill="currentColor" /></div><p>{mode === "mock" ? scenarioCopy[scenario].subtitle : playback.reason}</p><small className="media-status">{playback.label}</small></div><div className="video-scan" /><div className="overlay-box box-one"><span>PERSON 01</span><b>{mode === "mock" ? "0.94" : "—"}</b></div><div className="overlay-box box-two"><span>MEDICINE BOX</span><b>{mode === "mock" ? "0.87" : "—"}</b></div></div><div className="timeline"><span>00:00</span><div><i /><b /><b /><b /></div><span>LIVE</span></div><button className="primary-button monitor-run" onClick={onRun}><Sparkles size={15} /> 运行一次事件分析</button></div><div className="monitor-side"><div className="panel"><div className="panel-heading"><div><span className="panel-kicker">SIGNALS</span><h2>实时信号</h2></div></div><Signal label="人物轨迹" value={mode === "mock" ? "稳定" : "待接入"} color="green" /><Signal label="关注对象" value={mode === "mock" ? "2 个" : "—"} color="cyan" /><Signal label="事件管线" value="监听中" color="violet" /><Signal label="视频证据" value={playback.label} color="amber" /></div><div className="panel robot-card"><span className="panel-kicker">ROBOT ADAPTER</span><h2>机器人执行端</h2><p>等待老师提供机器人型号与通信文档后接入。</p><div className="robot-placeholder"><Box size={20} /><span>ADAPTER RESERVED</span></div></div></div></section>; }
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

function PluginsView({ plugins, onToggle }: { plugins: Plugin[]; onToggle: (plugin: Plugin) => Promise<void> }) { return <section className="plugin-layout"><div className="panel plugin-main"><div className="panel-heading"><div><span className="panel-kicker">EXTENSION RUNTIME</span><h2>插件能力</h2></div><span className="status-summary"><span className="status-dot green" /> {plugins.filter((item) => item.enabled).length} 个运行中</span></div><p className="panel-lead">插件在启动时从 <code>plugins/</code> 自动发现。场景模式只改变界面重点，不会替你关闭其他插件。</p>{plugins.map((plugin) => <div className="plugin-row" key={plugin.plugin_id}><div className={`plugin-symbol ${plugin.enabled ? "on" : "off"}`}><Sparkles size={18} /></div><div className="plugin-copy"><div><strong>{plugin.name}</strong><span className="version">v{plugin.version}</span></div><p>{plugin.description}</p><small>{plugin.plugin_id} · {plugin.state}</small></div><button className={`switch ${plugin.enabled ? "on" : ""}`} onClick={() => onToggle(plugin)} aria-label={`切换${plugin.name}`}><i /></button></div>)}</div><div className="panel plugin-note"><span className="panel-kicker">PLUGIN CONTRACT</span><h2>统一事件出口</h2><p>前端只消费统一事件，不直接理解插件内部算法。插件异常会进入 degraded/error 状态，主服务和其他插件继续运行。</p><div className="contract-list"><span><Check size={14} /> 自动发现</span><span><Check size={14} /> 全局启停</span><span><Check size={14} /> 并行运行</span><span><Check size={14} /> 独立测试</span></div></div></section>; }

function RegistryView({ repo, objects, persons, onObjects, onPersons, onToast }: { repo: Repository; objects: RegisteredObject[]; persons: RegisteredPerson[]; onObjects: (items: RegisteredObject[]) => void; onPersons: (items: RegisteredPerson[]) => void; onToast: (message: string) => void }) { const [objectName, setObjectName] = useState(""); const [personName, setPersonName] = useState(""); async function addObject() { if (!objectName.trim()) return; await repo.createObject(objectName.trim()); onObjects(await repo.listObjects()); setObjectName(""); onToast("关注对象已登记"); } async function addPerson() { if (!personName.trim()) return; await repo.createPerson(personName.trim(), "unknown"); onPersons(await repo.listPersons()); setPersonName(""); onToast("人员已登记"); } return <section className="registry-grid"><div className="panel registry-panel"><div className="panel-heading"><div><span className="panel-kicker">REGISTERED OBJECTS</span><h2>关注对象</h2></div><span className="count-pill">{objects.length}</span></div><p className="panel-lead">上传少量参考图即可注册长尾物品；当前演示先保存名称与引用位。</p><div className="inline-form"><input value={objectName} onChange={(event) => setObjectName(event.target.value)} placeholder="例如：这个药盒 / 这把电钻" /><button onClick={addObject}><Plus size={15} /> 登记</button></div>{objects.map((item) => <div className="registry-row" key={item.object_id}><div className="registry-icon"><Box size={16} /></div><div><strong>{item.name}</strong><span>{item.description}</span></div><span className="active-label">{item.status}</span></div>)}</div><div className="panel registry-panel"><div className="panel-heading"><div><span className="panel-kicker">REGISTERED PEOPLE</span><h2>人员身份</h2></div><span className="count-pill">{persons.length}</span></div><p className="panel-lead">支持注册式人员区分；识别不确定时保留 unknown/ambiguous 状态。</p><div className="inline-form"><input value={personName} onChange={(event) => setPersonName(event.target.value)} placeholder="例如：爷爷 / 家属 / 工作人员" /><button onClick={addPerson}><Plus size={15} /> 登记</button></div>{persons.map((item) => <div className="registry-row" key={item.person_id}><div className="registry-icon person"><Users size={16} /></div><div><strong>{item.display_name}</strong><span>{item.role}</span></div><span className="active-label">{item.status}</span></div>)}</div></section>; }

function SettingsView({ mode, scenario }: { mode: Mode; scenario: Scenario }) { return <section className="settings-grid"><div className="panel settings-main"><span className="panel-kicker">WORKSPACE SETTINGS</span><h2>系统设置</h2><div className="setting-item"><div><strong>数据源模式</strong><span>当前前端数据 provider</span></div><b className="setting-value">{mode === "mock" ? "Mock 演示" : "Real AI API"}</b></div><div className="setting-item"><div><strong>当前场景</strong><span>只改变界面重点，不改变插件状态</span></div><b className="setting-value">{scenarioCopy[scenario].label}</b></div><div className="setting-item"><div><strong>API 地址</strong><span>Real 模式下的 AI 服务地址</span></div><code>http://127.0.0.1:8010</code></div><div className="setting-item"><div><strong>隐私模式</strong><span>事件保存，不重复保存视频</span></div><span className="switch on"><i /></span></div></div><div className="panel settings-note"><ShieldCheck size={22} /><h3>证据边界</h3><p>事件用于辅助判断和人工复核。没有可用录像解析器时，界面会保留时间窗并标注“待解析”，不会伪造播放证据。</p><div className="note-tag"><Check size={13} /> 文档与实现保持同步</div></div></section>; }

function relativeTime(value: string) { const diff = Math.max(0, Date.now() - new Date(value).getTime()); const minutes = Math.round(diff / 60000); return minutes < 1 ? "刚刚" : minutes < 60 ? `${minutes} 分钟前` : `${Math.round(minutes / 60)} 小时前`; }

function MonitorLive({ scenario, mode, onRun }: { scenario: Scenario; mode: Mode; onRun: () => Promise<void> }) {
  const [session, setSession] = useState<LiveSession | null>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);

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
  const realReason = mediaError ?? playback.reason;
  return <section className="monitor-layout"><div className="panel large-video"><div className="panel-heading"><div><span className="panel-kicker">LIVE MONITOR / CAMERA 01</span><h2>客厅摄像头 <span className="live-tag">LIVE</span></h2></div><div className="monitor-actions"><span className="quality-pill">1080P · {mode === "mock" ? "MOCK" : "REAL"}</span><button className="icon-button"><Pause size={16} /></button></div></div><div className="video-preview expanded"><div className="video-grid" /><div className="video-center"><div className="play-ring"><Play size={24} fill="currentColor" /></div><p>{mode === "mock" ? scenarioCopy[scenario].subtitle : realReason}</p><small className="media-status">{playback.label}</small></div><div className="video-scan" /><div className="overlay-box box-one"><span>PERSON 01</span><b>{mode === "mock" ? "0.94" : "—"}</b></div><div className="overlay-box box-two"><span>MEDICINE BOX</span><b>{mode === "mock" ? "0.87" : "—"}</b></div></div><div className="timeline"><span>00:00</span><div><i /><b /><b /><b /></div><span>LIVE</span></div><button className="primary-button monitor-run" onClick={onRun}><Sparkles size={15} /> 运行一次事件分析</button></div><div className="monitor-side"><div className="panel"><div className="panel-heading"><div><span className="panel-kicker">SIGNALS</span><h2>实时信号</h2></div></div><Signal label="人物轨迹" value={mode === "mock" ? "稳定" : session ? "已发现" : "待接入"} color="green" /><Signal label="关注对象" value={mode === "mock" ? "2 个" : "—"} color="cyan" /><Signal label="事件管线" value="监听中" color="violet" /><Signal label="视频证据" value={playback.label} color="amber" /></div><div className="panel robot-card"><span className="panel-kicker">ROBOT ADAPTER</span><h2>机器人执行端</h2><p>等待老师提供机器人型号与通信文档后接入。</p><div className="robot-placeholder"><Box size={20} /><span>ADAPTER RESERVED</span></div></div></div></section>;
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
