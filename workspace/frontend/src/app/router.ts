import { useEffect, useState } from "react";

export type Page = "dashboard" | "monitor" | "events" | "medication" | "memory" | "plugins" | "demo" | "settings";
export const PAGES: Page[] = ["dashboard", "monitor", "events", "medication", "memory", "plugins", "demo", "settings"];

export interface Route { page: Page; param: string | null }

const LEGACY: Record<string, Page> = { registry: "memory" };

export function parseHash(hash: string): Route {
  const [head, ...rest] = hash.replace(/^#\/?/, "").split("/");
  const page = (LEGACY[head] ?? head) as Page;
  return { page: PAGES.includes(page) ? page : "dashboard", param: rest.length ? decodeURIComponent(rest.join("/")) : null };
}

export function href(page: Page, param?: string | null): string {
  return `#/${page}${param ? `/${encodeURIComponent(param)}` : ""}`;
}

export function navigate(page: Page, param?: string | null) {
  window.location.hash = href(page, param);
}

export function useRoute(): Route {
  const [route, setRoute] = useState(() => parseHash(window.location.hash));
  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
