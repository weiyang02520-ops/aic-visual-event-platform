import { useEffect, useState, type ReactNode } from "react";
import { Bell, Boxes, FileSearch, LayoutDashboard, Pill, Play, Puzzle, ScanEye, Settings } from "lucide-react";
import { Dot, Segmented } from "../design/ui";
import { connectionLabel, useRuntime } from "./runtime";
import { href, type Page } from "./router";
import { PAGE_TITLES } from "./pageTitles";
import { clockTime } from "../engine/labels";
import "./shell.css";

const NAV: Array<{ page: Page; label: string; icon: typeof LayoutDashboard }> = [
  { page: "dashboard", label: "总览", icon: LayoutDashboard },
  { page: "monitor", label: "隐私监护", icon: ScanEye },
  { page: "events", label: "事件分析", icon: FileSearch },
  { page: "medication", label: "用药计划", icon: Pill },
  { page: "memory", label: "记忆库", icon: Boxes },
  { page: "plugins", label: "插件", icon: Puzzle },
];

export function BrandMark({ size = 34 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <rect x="1" y="1" width="38" height="38" rx="12" fill="#3a73e8" />
      <path d="M9 20 Q20 10 31 20 Q20 30 9 20 Z" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinejoin="round" />
      <circle cx="20" cy="20" r="4.6" fill="#fff" />
      <circle cx="21.6" cy="18.4" r="1.4" fill="#3a73e8" />
    </svg>
  );
}

function useClock() {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => { const timer = window.setInterval(() => setNow(Date.now()), 1000); return () => window.clearInterval(timer); }, []);
  return now;
}

export function Shell({ page, children }: { page: Page; children: ReactNode }) {
  const { mode, setMode, connection, events } = useRuntime();
  const now = useClock();
  const pending = events.filter((event) => event.review_status === "pending").length;
  const tone = connection.status === "offline" ? "risk" : connection.status === "loading" ? "warn" : connection.status === "mock" ? "accent" : "ok";

  return (
    <div className="shell">
      <nav className="rail" aria-label="主导航">
        <a className="rail-brand" href={href("dashboard")} aria-label="Sentinel 首页"><BrandMark /></a>
        <div className="rail-items">
          {NAV.map(({ page: target, label, icon: Icon }) => (
            <a key={target} href={href(target)} className="rail-item" aria-current={page === target ? "page" : undefined}>
              <Icon size={22} strokeWidth={1.8} />
              <span>{label}</span>
              {target === "events" && pending > 0 && <em className="num">{pending}</em>}
            </a>
          ))}
        </div>
        <div className="rail-foot">
          <a href={href("demo")} className="rail-demo" aria-label="进入演示模式"><Play size={18} fill="currentColor" /><span>演示</span></a>
          <a href={href("settings")} className="rail-item" aria-current={page === "settings" ? "page" : undefined}><Settings size={22} strokeWidth={1.8} /><span>设置</span></a>
        </div>
      </nav>

      <div className="shell-main">
        <header className="topbar">
          <div className="topbar-left">
            <strong className="topbar-brand">Sentinel</strong>
            <span className="topbar-sep" />
            <span className="topbar-page">{PAGE_TITLES[page]}</span>
          </div>
          <div className="topbar-center" aria-live="polite">
            {events[0] && <a className="ticker" href={href("events", events[0].event_id)}><Bell size={15} /><span>{events[0].title}</span><b className="num">{Math.round(events[0].confidence * 100)}%</b></a>}
          </div>
          <div className="topbar-right">
            <span className={`conn conn-${tone}`}><Dot tone={tone} live={tone === "ok" || tone === "accent"} />{connectionLabel(connection)}</span>
            <Segmented label="数据源" value={mode} onChange={setMode} options={[{ value: "mock", label: "演示" }, { value: "real", label: "实时 API" }]} />
            <time className="topbar-clock num">{clockTime(now)}</time>
          </div>
        </header>
        <main className="shell-content">{children}</main>
      </div>
    </div>
  );
}
