import { useMemo } from "react";
import { Box } from "lucide-react";
import { Empty } from "../../design/ui";
import { relativeTime } from "../../engine/labels";
import { buildMemory } from "../../engine/memory";
import { ObjectGlyph } from "../../render/ObjectGlyph";
import { definePlugin, type PluginContext } from "../sdk";

function ObjectCarePanel({ objects, events }: PluginContext) {
  const items = useMemo(() => buildMemory(objects, events).filter((item) => item.appearances.length).slice(0, 3), [objects, events]);
  if (!items.length) return <Empty title="暂无物品位置记录" />;
  return (
    <ul className="mon-objects">
      {items.map((item) => (
        <li key={item.object.object_id}>
          <span className="glyph-tile"><ObjectGlyph kind={item.glyph} size={28} /></span>
          <div><strong>{item.object.name}</strong><span>最近在 {item.lastLocation ?? "—"} · {relativeTime(item.lastSeen)}</span></div>
        </li>
      ))}
    </ul>
  );
}

export default definePlugin({
  id: "workshop",
  label: "物品看护",
  scene: "物品管理",
  icon: Box,
  description: "记住常用物品和工具放在哪里，物品被拿走或放回时留下记录，找东西时能查到最后出现的位置。",
  inputs: ["object_in_zone", "hand_near_object", "left_zone", "entered_zone"],
  outputs: ["物品离开区域", "物品回到区域", "最近已知位置"],
  watches: ["tool", "daily"],
  Panel: ObjectCarePanel,
  summarize: ({ events }) => {
    const latest = events[0];
    if (!latest) return { headline: "还没有物品变动", detail: "物品被拿走或放回时会记录", tone: "neutral" };
    return { headline: latest.title, detail: `${latest.location ?? "—"} · ${relativeTime(latest.started_at)}`, tone: "accent" };
  },
});
