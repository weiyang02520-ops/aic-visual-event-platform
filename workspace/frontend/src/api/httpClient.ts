import { ContractApiError } from "../contracts/common";
import type { ApiErrorPayload } from "../contracts/common";

export interface RequestJsonOptions extends RequestInit {
  timeoutMs?: number;
}

export async function requestJson<T>(baseUrl: string, path: string, options?: RequestJsonOptions): Promise<T> {
  const root = baseUrl.replace(/\/+$/, "");
  const { timeoutMs = 10000, signal: externalSignal, ...requestOptions } = options ?? {};
  const controller = new AbortController();
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const relayAbort = () => controller.abort();
  externalSignal?.addEventListener("abort", relayAbort, { once: true });
  let response: Response;
  try {
    response = await fetch(`${root}${path}`, {
      ...requestOptions,
      headers: { "Content-Type": "application/json", ...(requestOptions.headers ?? {}) },
      signal: controller.signal,
    });
  } catch (error) {
    if (timedOut) throw new ContractApiError(`请求超时（${timeoutMs}ms）`, 0);
    if (externalSignal?.aborted) throw new ContractApiError("请求已取消", 0);
    throw new ContractApiError(error instanceof Error && error.message ? error.message : "网络请求失败", 0);
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", relayAbort);
  }
  if (!response.ok) {
    let detail: string | undefined;
    try {
      const payload = (await response.json()) as ApiErrorPayload;
      const raw = payload.detail ?? payload.message ?? payload.error;
      detail = typeof raw === "string" ? raw : raw == null ? undefined : JSON.stringify(raw);
    } catch {
      // Keep the HTTP status when the backend does not return JSON.
    }
    const message = `${response.status} ${response.statusText}${detail ? `：${detail}` : ""}`.trim();
    throw new ContractApiError(message, response.status, detail);
  }
  return response.json() as Promise<T>;
}
