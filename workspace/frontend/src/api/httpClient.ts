import { ContractApiError } from "../contracts/common";
import type { ApiErrorPayload } from "../contracts/common";

export async function requestJson<T>(baseUrl: string, path: string, options?: RequestInit): Promise<T> {
  const root = baseUrl.replace(/\/+$/, "");
  let response: Response;
  try {
    response = await fetch(`${root}${path}`, {
      headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
      ...options,
    });
  } catch (error) {
    throw new ContractApiError(error instanceof Error && error.message ? error.message : "网络请求失败", 0);
  }
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      const raw = payload.detail ?? payload.message ?? payload.error;
      detail = typeof raw === "string" ? raw : undefined;
    } catch {
      // Keep the HTTP status when the backend does not return JSON.
    }
    const message = `${response.status} ${response.statusText}${detail ? `：${detail}` : ""}`.trim();
    throw new ContractApiError(message, response.status, detail);
  }
  return response.json() as Promise<T>;
}
