import type {
  AnalysisJob,
  Plugin,
  RegisteredObject,
  RegisteredPerson,
  Repository,
  ReviewStatus,
  UnifiedEvent,
} from "./types";

const now = () => new Date().toISOString();

const mockPlugins: Plugin[] = [
  {
    plugin_id: "elderly_care",
    name: "智慧养老辅助判断",
    version: "0.1.0",
    description: "把药盒、人物和动作事实组合成可复核的疑似服药事件。",
    enabled: true,
    state: "enabled",
  },
  {
    plugin_id: "workshop",
    name: "工作室物品管理",
    version: "0.1.0",
    description: "追踪工具离开登记区域、归还和最后出现位置。",
    enabled: true,
    state: "enabled",
  },
];

const mockEvents: UnifiedEvent[] = [
  {
    event_id: "evt-demo-001",
    plugin_id: "elderly_care",
    plugin_version: "0.1.0",
    event_type: "suspected_medication",
    title: "疑似发生服药相关行为",
    description: "检测到药盒拿起与手部接近面部的连续事实，建议结合历史视频人工复核。",
    source_id: "living-room-cam-01",
    started_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
    ended_at: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
    confidence: 0.78,
    severity: "medium",
    review_status: "pending",
    subject: { id: "person_01", label: "爷爷" },
    object: { id: "medicine_box_01", label: "降压药盒" },
    location: "客厅桌面",
    evidence: [
      {
        source_id: "living-room-cam-01",
        started_at: new Date(Date.now() - 1000 * 60 * 8 - 3000).toISOString(),
        ended_at: new Date(Date.now() - 1000 * 60 * 7 + 3000).toISOString(),
        resolver: "hls-evidence-resolver",
        status: "designed",
      },
    ],
    facts: [
      { fact_type: "object_picked", confidence: 0.91, location: "药箱区域" },
      { fact_type: "hand_to_face", confidence: 0.74, location: "客厅桌面" },
    ],
    metadata: { interpretation: "辅助判断，不是医学诊断" },
  },
  {
    event_id: "evt-demo-002",
    plugin_id: "workshop",
    plugin_version: "0.1.0",
    event_type: "object_removed",
    title: "电钻离开工具架 A",
    description: "检测到关注物品离开登记区域，最后出现位置已记录。",
    source_id: "workbench-cam-02",
    started_at: new Date(Date.now() - 1000 * 60 * 34).toISOString(),
    ended_at: new Date(Date.now() - 1000 * 60 * 34).toISOString(),
    confidence: 0.88,
    severity: "low",
    review_status: "confirmed",
    subject: { id: "person_02", label: "工作人员" },
    object: { id: "drill_01", label: "电钻" },
    location: "工具架 A",
    evidence: [],
    facts: [{ fact_type: "object_removed", confidence: 0.88, location: "工具架 A" }],
    metadata: {},
  },
];

const wait = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));

export function createMockRepository(): Repository {
  let plugins = structuredClone(mockPlugins);
  let events = structuredClone(mockEvents);
  const jobs = new Map<string, AnalysisJob>();
  let objects: RegisteredObject[] = [
    { object_id: "obj-01", name: "降压药盒", description: "爷爷每日药盒", reference_uris: [], status: "active" },
    { object_id: "obj-02", name: "电钻", description: "工具架 A 关注物品", reference_uris: [], status: "active" },
  ];
  let persons: RegisteredPerson[] = [
    { person_id: "person-01", display_name: "爷爷", role: "resident", reference_uris: [], status: "active" },
    { person_id: "person-02", display_name: "工作人员", role: "staff", reference_uris: [], status: "active" },
  ];
  return {
    async listPlugins() {
      await wait();
      return structuredClone(plugins);
    },
    async togglePlugin(pluginId, enabled) {
      await wait();
      plugins = plugins.map((plugin) =>
        plugin.plugin_id === pluginId ? { ...plugin, enabled, state: enabled ? "enabled" : "disabled" } : plugin,
      );
      const result = plugins.find((plugin) => plugin.plugin_id === pluginId);
      if (!result) throw new Error("plugin not found");
      return structuredClone(result);
    },
    async listEvents() {
      await wait();
      return structuredClone(events);
    },
    async reviewEvent(eventId, status) {
      await wait();
      events = events.map((event) => (event.event_id === eventId ? { ...event, review_status: status } : event));
      const result = events.find((event) => event.event_id === eventId);
      if (!result) throw new Error("event not found");
      return structuredClone(result);
    },
    async createAnalysis(source) {
      await wait(320);
      const job: AnalysisJob = { job_id: `mock-job-${Date.now()}`, source, status: "completed", progress: 1, event_ids: [] };
      if (source.includes("elderly")) {
        const event = structuredClone(mockEvents[0]);
        event.event_id = `evt-${Date.now()}`;
        event.created_at = now();
        events = [event, ...events];
        job.event_ids = [event.event_id];
      }
      jobs.set(job.job_id, structuredClone(job));
      return job;
    },
    async getAnalysis(jobId) {
      await wait();
      const job = jobs.get(jobId);
      if (!job) throw new Error("job not found");
      return structuredClone(job);
    },
    async listObjects() {
      await wait();
      return structuredClone(objects);
    },
    async createObject(name) {
      await wait();
      const item: RegisteredObject = { object_id: `obj-${Date.now()}`, name, description: "新注册对象", reference_uris: [], status: "active" };
      objects = [item, ...objects];
      return structuredClone(item);
    },
    async listPersons() {
      await wait();
      return structuredClone(persons);
    },
    async createPerson(name, role) {
      await wait();
      const item: RegisteredPerson = { person_id: `person-${Date.now()}`, display_name: name, role, reference_uris: [], status: "active" };
      persons = [item, ...persons];
      return structuredClone(item);
    },
  };
}

export function createRealRepository(baseUrl: string): Repository {
  async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${baseUrl}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    return response.json() as Promise<T>;
  }
  return {
    listPlugins: () => request<Plugin[]>("/api/v1/plugins"),
    togglePlugin: (id, enabled) => request<Plugin>(`/api/v1/plugins/${id}/${enabled ? "enable" : "disable"}`, { method: "POST" }),
    listEvents: () => request<UnifiedEvent[]>("/api/v1/events"),
    reviewEvent: (id, status) => request<UnifiedEvent>(`/api/v1/events/${id}/review`, { method: "POST", body: JSON.stringify({ status }) }),
    createAnalysis: (source) => request<AnalysisJob>("/api/v1/analysis/jobs", { method: "POST", body: JSON.stringify({ source }) }),
    getAnalysis: (jobId) => request<AnalysisJob>(`/api/v1/analysis/jobs/${encodeURIComponent(jobId)}`),
    listObjects: () => request<RegisteredObject[]>("/api/v1/objects"),
    createObject: (name) => request<RegisteredObject>("/api/v1/objects", { method: "POST", body: JSON.stringify({ name }) }),
    listPersons: () => request<RegisteredPerson[]>("/api/v1/persons"),
    createPerson: (name, role) => request<RegisteredPerson>("/api/v1/persons", { method: "POST", body: JSON.stringify({ display_name: name, role }) }),
  };
}
