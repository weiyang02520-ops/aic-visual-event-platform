import { useEffect, useId, type ReactNode } from "react";
import { X } from "lucide-react";

export type Tone = "ok" | "warn" | "risk" | "accent" | "neutral";

export function Dot({ tone = "neutral", live = false }: { tone?: Tone; live?: boolean }) {
  return <span className={`dot ${tone} ${live ? "live" : ""}`} aria-hidden="true" />;
}

export function Pill({ tone = "neutral", children, className = "" }: { tone?: Tone | "ghost"; children: ReactNode; className?: string }) {
  return <span className={`pill ${tone} ${className}`}>{children}</span>;
}

export function Panel({ title, icon, aside, children, className = "", pad = true }: { title?: ReactNode; icon?: ReactNode; aside?: ReactNode; children: ReactNode; className?: string; pad?: boolean }) {
  return (
    <section className={`panel ${pad ? "panel-pad" : ""} ${className}`}>
      {(title || aside) && (
        <header className="panel-head">
          <h2 className="panel-title">{icon}{title}</h2>
          {aside}
        </header>
      )}
      {children}
    </section>
  );
}

export function ConfidenceRing({ value, size = 88, stroke = 7, label = "置信度", tone = "accent" }: { value: number | null; size?: number; stroke?: number; label?: string; tone?: Tone }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const safe = typeof value === "number" && Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
  const color = tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : tone === "risk" ? "var(--risk)" : "var(--accent)";
  return (
    <div className="ring" style={{ width: size, height: size }} role="img" aria-label={`${label} ${value == null ? "未知" : `${Math.round(safe * 100)}%`}`}>
      <svg width={size} height={size}>
        <circle className="ring-track" cx={size / 2} cy={size / 2} r={radius} fill="none" strokeWidth={stroke} />
        <circle className="ring-value" cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth={stroke} strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={circumference * (1 - safe)} />
      </svg>
      <div className="ring-label">
        <strong className="num" style={{ fontSize: size < 70 ? 15 : undefined }}>{value == null ? "—" : Math.round(safe * 100)}<small style={{ fontSize: "0.5em", marginLeft: 1 }}>{value == null ? "" : "%"}</small></strong>
        {size >= 70 && <span>{label}</span>}
      </div>
    </div>
  );
}

export function Meter({ value, tone }: { value: number; tone?: Tone }) {
  const color = tone === "ok" ? "var(--ok)" : tone === "warn" ? "var(--warn)" : tone === "risk" ? "var(--risk)" : undefined;
  return <div className="meter"><i style={{ width: `${Math.round(Math.min(1, Math.max(0, value)) * 100)}%`, background: color }} /></div>;
}

export function Segmented<T extends string>({ value, options, onChange, label }: { value: T; options: Array<{ value: T; label: ReactNode }>; onChange: (value: T) => void; label: string }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map((option) => (
        <button key={option.value} type="button" aria-pressed={option.value === value} onClick={() => onChange(option.value)}>{option.label}</button>
      ))}
    </div>
  );
}

export function Switch({ checked, onChange, label, disabled }: { checked: boolean; onChange: () => void; label: string; disabled?: boolean }) {
  return <button type="button" role="switch" className="switch" aria-checked={checked} aria-label={label} onClick={onChange} disabled={disabled} />;
}

export function Empty({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return <div className="empty">{icon}<strong>{title}</strong>{children && <span>{children}</span>}</div>;
}

export function Modal({ title, subtitle, onClose, children }: { title: string; subtitle?: string; onClose: () => void; children: ReactNode }) {
  const id = useId();
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={id} onMouseDown={(event) => event.stopPropagation()}>
        <div className="modal-head">
          <div><h2 id={id}>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>
          <button className="icon-btn" onClick={onClose} aria-label="关闭"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function reviewTone(status: string): Tone {
  return status === "confirmed" ? "ok" : status === "rejected" ? "risk" : "warn";
}
