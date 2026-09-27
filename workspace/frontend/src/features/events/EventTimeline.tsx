import { ArrowRight, CircleDot } from "lucide-react";
import type { PrimitiveFactContract } from "../../contracts";

const labels: Record<string, string> = {
  person_entered_zone: "人物进入监控区",
  object_detected: "检测到对象",
  object_picked: "拿起对象",
  pickup_candidate: "出现拿取候选",
  hand_to_face: "手靠近面部",
  hand_near_object: "手靠近对象",
  object_put_down: "放下对象",
  putdown_candidate: "出现放回候选",
  object_removed: "对象离开区域",
  object_returned: "对象回到区域",
  object_in_zone: "对象位于区域",
  entered_zone: "进入区域",
  left_zone: "离开区域",
  motion: "发生移动",
};

function factTitle(factType: string) {
  return labels[factType] ?? factType.replaceAll("_", " ");
}

export function EventTimeline({ facts }: { facts: PrimitiveFactContract[] }) {
  if (!facts.length) return <p className="event-contract-empty">没有附加推理事实</p>;
  return <div className="event-reasoning-timeline">
    {facts.map((fact, index) => (
      <div className="event-reasoning-step" key={`${fact.fact_type}-${index}`}>
        <div className="event-reasoning-marker"><CircleDot size={13} /></div>
        <div className="event-reasoning-copy"><strong>{index + 1}. {factTitle(fact.fact_type)}</strong><span>{fact.location ?? "来源帧事实"} · {Math.round(fact.confidence * 100)}% 置信度</span></div>
        {index < facts.length - 1 && <ArrowRight className="event-reasoning-arrow" size={14} />}
      </div>
    ))}
  </div>;
}
