import { Calendar, Clock, Edit, Pill as PillIcon, Plus } from "lucide-react";
import { useRuntime } from "../../app/runtime";
import { Empty, Panel, Pill } from "../../design/ui";
import { clockTime } from "../../engine/labels";
import "./medication.css";

/**
 * Medication plan management (F5). The backend contract is frozen at storing
 * plans and matching them to detected events. This page is a placeholder
 * showing that structure, but it doesn't implement the five cue types
 * (on-time, early, late, wrong-item, insufficient-evidence) or configuration
 * UI yet, since those need backend API design.
 */
export function MedicationPlanPage() {
  const { mode, connection } = useRuntime();

  return (
    <div className="page medication-page">
      <header className="page-head">
        <div>
          <h1>用药计划</h1>
          <p>配置预期的用药时间和药物，系统会在检测到相关行为时与计划比对，生成五种提示：按时、提前、延迟、错误药物、证据不足。</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-primary"><Plus size={16} />新增计划</button>
        </div>
      </header>

      <Panel title="计划列表" icon={<Calendar size={18} />}>
        <Empty icon={<PillIcon size={24} />} title="用药计划功能待完善">
          <p>后端已支持存储计划和匹配逻辑（冻结契约），前端这个页面是占位符。完整实现需要：</p>
          <ul className="med-list">
            <li><strong>五种提示分类</strong>：按时匹配、提前候选、延迟候选、错误药物、证据不足。</li>
            <li><strong>计划配置界面</strong>：时间窗口、药物名称、剂量、时区。</li>
            <li><strong>后端 API</strong>：GET /api/v1/medication/plans（列出）、POST（新增）、PATCH（修改）。</li>
          </ul>
          {connection.status === "offline" && <p className="faint">{connection.reason}</p>}
          {mode === "mock" && <p className="faint">演示模式不展示计划匹配，只展示检测到的用药行为事件。</p>}
        </Empty>
      </Panel>

      <section className="med-sample">
        <h2 className="eyebrow">示例计划（仅供参考，不是真实数据）</h2>
        <div className="med-card panel">
          <div className="med-card-head">
            <span className="med-icon"><PillIcon size={20} /></span>
            <div><strong>早晨降压药</strong><Pill tone="ok">启用</Pill></div>
            <button className="icon-btn" aria-label="编辑"><Edit size={16} /></button>
          </div>
          <dl className="kv">
            <div><dt><Clock size={13} /> 预期时间</dt><dd>08:00 ± 30 分钟</dd></div>
            <div><dt><PillIcon size={13} /> 药物</dt><dd>降压药 · 1 片</dd></div>
            <div><dt>时区</dt><dd>Asia/Shanghai</dd></div>
          </dl>
          <p className="faint">系统会在 07:30–08:30 检测到用药行为时生成"按时匹配"提示，在此之前或之后则生成"提前/延迟候选"。</p>
        </div>
      </section>
    </div>
  );
}
