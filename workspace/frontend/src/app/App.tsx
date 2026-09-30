import { useEffect } from "react";
import { Info, X } from "lucide-react";
import { RuntimeProvider, useRuntime } from "./runtime";
import { useRoute } from "./router";
import { PAGE_TITLES } from "./pageTitles";
import { Shell } from "./Shell";
import { DashboardPage } from "../pages/dashboard/DashboardPage";
import { MonitorPage } from "../pages/monitor/MonitorPage";
import { EventsPage } from "../pages/events/EventsPage";
import { MemoryPage } from "../pages/memory/MemoryPage";
import { MedicationPlanPage } from "../pages/medication/MedicationPlanPage";
import { PluginsPage } from "../pages/plugins/PluginsPage";
import { DemoPage } from "../pages/demo/DemoPage";
import { SettingsPage } from "../pages/settings/SettingsPage";

function Toast() {
  const { toast, notify } = useRuntime();
  if (!toast) return null;
  return <div className="toast" role="status"><Info size={18} /><span>{toast}</span><button className="icon-btn" style={{ width: 28, height: 28 }} onClick={() => notify(null)} aria-label="关闭提示"><X size={14} /></button></div>;
}

function Routes() {
  const { page, param } = useRoute();
  useEffect(() => { document.title = `${PAGE_TITLES[page]} · Sentinel AI 视觉监护`; }, [page]);
  if (page === "demo") return <><DemoPage key={param ?? "start"} startAt={param} /><Toast /></>;
  return (
    <Shell page={page}>
      {page === "dashboard" && <DashboardPage />}
      {page === "monitor" && <MonitorPage />}
      {page === "events" && <EventsPage selectedId={param} />}
      {page === "memory" && <MemoryPage selectedId={param} />}
      {page === "medication" && <MedicationPlanPage />}
      {page === "plugins" && <PluginsPage />}
      {page === "settings" && <SettingsPage />}
      <Toast />
    </Shell>
  );
}

export default function App() {
  return <RuntimeProvider><Routes /></RuntimeProvider>;
}
