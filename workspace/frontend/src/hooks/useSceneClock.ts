import { useCallback, useEffect, useRef, useState } from "react";

export interface SceneClock {
  t: number;
  playing: boolean;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (t: number) => void;
  restart: () => void;
}

/** requestAnimationFrame clock for scripted or replayed scenes. */
export function useSceneClock(duration: number, { loop = true, autoplay = true, start = 0, onEnd }: { loop?: boolean; autoplay?: boolean; start?: number; onEnd?: () => void } = {}): SceneClock {
  const [t, setT] = useState(start);
  const [playing, setPlaying] = useState(autoplay);
  const tRef = useRef(start);
  const endRef = useRef(onEnd);
  endRef.current = onEnd;

  useEffect(() => {
    if (!playing || duration <= 0) return;
    let frame = 0;
    let last = performance.now();
    const tick = (now: number) => {
      // rAF timestamps can precede the performance.now() captured at start; never step backwards.
      const delta = Math.min(0.1, Math.max(0, (now - last) / 1000));
      last = now;
      let next = tRef.current + delta;
      if (next >= duration) {
        if (loop) next %= duration;
        else {
          next = duration;
          tRef.current = next;
          setT(next);
          setPlaying(false);
          endRef.current?.();
          return;
        }
      }
      tRef.current = next;
      setT(next);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, duration, loop]);

  const seek = useCallback((value: number) => {
    const next = Math.min(duration, Math.max(0, value));
    tRef.current = next;
    setT(next);
  }, [duration]);

  return {
    t,
    playing,
    play: useCallback(() => { if (tRef.current >= duration) seek(0); setPlaying(true); }, [duration, seek]),
    pause: useCallback(() => setPlaying(false), []),
    toggle: useCallback(() => setPlaying((value) => { if (!value && tRef.current >= duration) { tRef.current = 0; setT(0); } return !value; }), [duration]),
    seek,
    restart: useCallback(() => { seek(0); setPlaying(true); }, [seek]),
  };
}
