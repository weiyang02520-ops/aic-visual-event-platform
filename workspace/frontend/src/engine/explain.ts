import { factLabel } from "./labels.ts";

/** Minimal event shape so the engine stays independent from React and API modules. */
export interface ExplainableFact {
  fact_type: string;
  confidence: number;
  location?: string | null;
  timestamp?: string;
}

export interface ExplainableEvent {
  event_id: string;
  plugin_id: string;
  event_type: string;
  title: string;
  confidence: number;
  started_at: string;
  ended_at: string;
  location?: string | null;
  subject?: Record<string, unknown> | null;
  object?: Record<string, unknown> | null;
  facts: ExplainableFact[];
  metadata: Record<string, unknown>;
}

export type StageKey = "person" | "object" | "interaction" | "action" | "verdict";
export type StageStatus = "passed" | "missing";

export interface ReasoningStage {
  key: StageKey;
  title: string;
  status: StageStatus;
  confidence: number | null;
  facts: ExplainableFact[];
  reason: string;
}

export interface EventExplanation {
  isMedication: boolean;
  sequenceComplete: boolean;
  stages: ReasoningStage[];
  verdict: { headline: string; confidence: number; disclaimer: string };
}

const PERSON_FACTS = new Set(["person_entered_zone", "person_detected", "person_present", "entered_zone", "motion"]);
const OBJECT_FACTS = new Set(["object_detected", "object_in_zone"]);
const INTERACTION_FACTS = new Set(["hand_near_object", "pickup_candidate", "object_picked", "object_put_down", "putdown_candidate", "object_removed", "object_returned", "left_zone"]);
const ACTION_FACTS = new Set(["hand_to_face"]);

function stageFor(factType: string): Exclude<StageKey, "verdict"> {
  if (PERSON_FACTS.has(factType)) return "person";
  if (OBJECT_FACTS.has(factType)) return "object";
  if (INTERACTION_FACTS.has(factType)) return "interaction";
  if (ACTION_FACTS.has(factType)) return "action";
  return "action";
}

function isFact(value: unknown): value is ExplainableFact {
  return Boolean(value) && typeof value === "object" && typeof (value as ExplainableFact).fact_type === "string";
}

/** `metadata.reasoning_chain` is the plugin's own ordering; plain `facts` are the fallback. */
export function reasoningFacts(event: ExplainableEvent): ExplainableFact[] {
  const chain = event.metadata?.reasoning_chain;
  const source = Array.isArray(chain) && chain.some(isFact) ? chain.filter(isFact) : event.facts;
  return source.map((fact) => ({ ...fact, confidence: typeof fact.confidence === "number" ? fact.confidence : event.confidence }));
}

export function isMedicationEvent(event: Pick<ExplainableEvent, "plugin_id" | "event_type">): boolean {
  return event.plugin_id === "elderly_care" || /medication/.test(event.event_type);
}

function label(value: Record<string, unknown> | null | undefined, fallback: string): string {
  const text = value?.label ?? value?.name ?? value?.id;
  return typeof text === "string" && text ? text : fallback;
}

function maxConfidence(facts: ExplainableFact[]): number | null {
  return facts.length ? Math.max(...facts.map((fact) => fact.confidence)) : null;
}

export function explainEvent(event: ExplainableEvent): EventExplanation {
  const medication = isMedicationEvent(event);
  const facts = reasoningFacts(event);
  const grouped: Record<Exclude<StageKey, "verdict">, ExplainableFact[]> = { person: [], object: [], interaction: [], action: [] };
  facts.forEach((fact) => grouped[stageFor(fact.fact_type)].push(fact));

  const person = label(event.subject, "人物");
  const object = label(event.object, medication ? "药盒" : "物品");
  const where = (items: ExplainableFact[]) => items.find((fact) => fact.location)?.location ?? event.location ?? "监控区";

  const templates: Array<{ key: Exclude<StageKey, "verdict">; title: string; passed: (items: ExplainableFact[]) => string; missing: string }> = [
    { key: "person", title: "发现人物", passed: (items) => `在${where(items)}建立 ${person} 的连续骨骼轨迹`, missing: "没有稳定的人物轨迹" },
    { key: "object", title: medication ? "检测药盒" : "识别物品", passed: (items) => `在${where(items)}识别到${object}`, missing: `未识别到${object}` },
    { key: "interaction", title: medication ? "检测拿取" : "检测交互", passed: (items) => items.map((fact) => factLabel(fact.fact_type)).join(" → "), missing: medication ? "没有观察到手与药盒的接触或拿取" : "没有观察到人与物品的交互" },
    { key: "action", title: "检测动作", passed: (items) => items.map((fact) => factLabel(fact.fact_type)).join(" → "), missing: medication ? "缺少手部接近面部的后续动作" : "没有后续动作" },
  ];

  const stages: ReasoningStage[] = templates
    .filter((template) => medication || grouped[template.key].length > 0)
    .map((template) => {
      const items = grouped[template.key];
      return { key: template.key, title: template.title, status: items.length ? "passed" : "missing", confidence: maxConfidence(items), facts: items, reason: items.length ? template.passed(items) : template.missing };
    });

  const declared = event.metadata?.sequence_complete;
  const sequenceComplete = typeof declared === "boolean" ? declared : stages.every((stage) => stage.status === "passed");
  const disclaimer = typeof event.metadata?.interpretation === "string" ? event.metadata.interpretation : "辅助判断，不是医学诊断";
  const headline = medication ? (sequenceComplete ? "疑似完成服药 · 需人工复核" : "服药序列不完整 · 仅作复核线索") : event.title;

  stages.push({ key: "verdict", title: "生成判断", status: "passed", confidence: event.confidence, facts: [], reason: headline });
  return { isMedication: medication, sequenceComplete, stages, verdict: { headline, confidence: event.confidence, disclaimer } };
}
