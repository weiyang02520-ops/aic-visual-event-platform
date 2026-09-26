export interface BackendWebSocketPreparation {
  url: string;
  protocols?: string | string[];
}

/**
 * WebSocket preparation only. The integration layer exposes connection
 * metadata for a future stream adapter; it intentionally does not open a
 * socket or implement realtime event handling in this task.
 */
export function prepareBackendWebSocket(baseUrl: string, path = "/api/v1/events/stream", protocols?: string | string[]): BackendWebSocketPreparation {
  const normalized = baseUrl.replace(/^http/, "ws").replace(/\/+$/, "");
  return { url: `${normalized}${path.startsWith("/") ? path : `/${path}`}`, protocols };
}
