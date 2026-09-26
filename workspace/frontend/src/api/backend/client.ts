import { requestJson, type RequestJsonOptions } from "../httpClient";

export interface BackendClientOptions {
  baseUrl: string;
  timeoutMs?: number;
}

/** Small REST client shared by the endpoint modules. It owns URL and timeout policy. */
export class BackendApiClient {
  readonly baseUrl: string;
  readonly timeoutMs: number;

  constructor(options: BackendClientOptions) {
    this.baseUrl = options.baseUrl;
    this.timeoutMs = options.timeoutMs ?? 10000;
  }

  request<T>(path: string, options?: RequestJsonOptions): Promise<T> {
    return requestJson<T>(this.baseUrl, path, { timeoutMs: this.timeoutMs, ...options });
  }

  get<T>(path: string, options?: Omit<RequestJsonOptions, "method" | "body">): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  post<T>(path: string, body?: unknown, options?: Omit<RequestJsonOptions, "method" | "body">): Promise<T> {
    return this.request<T>(path, { ...options, method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
  }
}
