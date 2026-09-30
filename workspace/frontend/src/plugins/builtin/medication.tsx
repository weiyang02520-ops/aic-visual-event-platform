import { Bell, Check, ClipboardCheck } from "lucide-react";
import { href } from "../../app/router";
import { Empty } from "../../design/ui";
import { explainEvent } from "../../engine/explain";
import { percent, planCueLabel, relativeTime, reviewLabel } from "../../engine/labels";
import { definePlugin, type PluginContext } from "../sdk";

function MedicationPanel({ frame, events }: PluginContext) {
  const latest = events[0];
  // The live scene drives the checklist; without one, fall back to the latest event's reasoning.
  const steps = frame?.steps.length
    ? frame.steps
    : latest ? explainEvent(latest).stages.map((stage) => ({ key: stage.key, label: stage.title, done: stage.status === "passed", confidence: stage.confidence })) : [];
  const cue = planCueLabel(latest?.metadata.plan_cue);
  const showResult = frame?.steps.length ? frame.eventReady : Boolean(latest);
  return (
    <>
      {steps.length ? (
        <ol className="med-steps">
          {steps.map((step) => (
            <li key={step.key} className={step.done ? "done" : ""}>
              <span className="med-check">{step.done ? <Check size={13} strokeWidth={3} /> : null}</span>
              <span>{step.label}</span>
              <b className="num">{step.done ? percent(step.confidence) : "—"}</b>
            </li>
          ))}
        </ol>
      ) : <Empty title="等待用药相关动作" />}
      {showResult && (
        <a className="med-result" href={latest ? href("events", latest.event_id) : href("events")}>
          <Bell size={16} />
          <span><strong>{frame?.steps.length ? "疑似完成服药 · 需复核" : explainEvent(latest!).verdict.headline}</strong><small>{cue ?? "辅助判断，不是医学诊断"}</small></span>
        </a>
      )}
    </>
  );
}

export default definePlugin({
  id: "elderly_care",
  label: "用药辅助",
  scene: "智慧养老",
  icon: ClipboardCheck,
  description: "把人物、药盒和手部动作串起来，判断老人是否疑似完成服药，并对照用药计划给出复核提示。",
  inputs: ["person_entered_zone", "object_detected", "hand_near_object", "object_picked", "hand_to_face"],
  outputs: ["疑似服药", "服药序列不完整", "用药计划提示"],
  watches: ["medicine"],
  Panel: MedicationPanel,
  summarize: ({ events }) => {
    const latest = events[0];
    if (!latest) return { headline: "今天还没有用药记录", detail: "等待老人拿取药盒", tone: "neutral" };
    const explanation = explainEvent(latest);
    return { headline: explanation.verdict.headline, detail: `${relativeTime(latest.started_at)} · ${reviewLabel(latest.review_status)}`, tone: latest.review_status === "pending" ? "warn" : "ok" };
  },
});
