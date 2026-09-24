import type { LiveSession, PlaybackState } from "./types";

type JsonObject = Record<string, unknown>;

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function readString(object: JsonObject, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = stringValue(object[key]);
    if (value) return value;
  }
  return null;
}

/**
 * Convert Makerverse's DTO casing and nested endpoint response into the
 * frontend's stable, lower-camel-case boundary. The source snapshot returns
 * `LivestreamEndpointDto { IngestUrl, PlaybackEndpoints { RtmpUrl,
 * HttpFlvUrl } }`, while a gateway may already flatten those fields.
 */
export function normalizeLiveSession(raw: unknown, fallbackId?: string): LiveSession {
  const value = (raw && typeof raw === "object" ? raw : {}) as JsonObject;
  const playback = (value.playbackEndpoints ?? value.PlaybackEndpoints ?? {}) as JsonObject;
  const id = readString(value, "id", "Id", "liveId", "LiveId") ?? fallbackId ?? "unknown";
  return {
    id,
    title: readString(value, "title", "Title") ?? id,
    status: readString(value, "status", "Status") ?? "unknown",
    ingestUrl: readString(value, "ingestUrl", "IngestUrl") ?? readString(playback, "ingestUrl", "IngestUrl"),
    rtmpUrl: readString(value, "rtmpUrl", "RtmpUrl") ?? readString(playback, "rtmpUrl", "RtmpUrl"),
    httpFlvUrl: readString(value, "httpFlvUrl", "HttpFlvUrl") ?? readString(playback, "httpFlvUrl", "HttpFlvUrl"),
    hlsUrl: readString(value, "hlsUrl", "HlsUrl") ?? readString(playback, "hlsUrl", "HlsUrl"),
  };
}

export function classifyPlaybackUrl(url: string | null | undefined): PlaybackState {
  if (!url) return { kind: "unknown", url: null, browserPlayable: false, label: "未配置", reason: "没有可用播放地址" };
  if (url.startsWith("mock://")) return { kind: "mock", url, browserPlayable: false, label: "Mock 画面", reason: "离线演示画面，不是真实媒体流" };
  const normalized = url.toLowerCase();
  if (normalized.startsWith("rtmp://")) return { kind: "rtmp", url, browserPlayable: false, label: "RTMP ingest", reason: "浏览器原生 video 不支持 RTMP，需要转 HLS/HTTP-FLV" };
  if (normalized.startsWith("rtsp://")) return { kind: "rtsp", url, browserPlayable: false, label: "RTSP source", reason: "浏览器不能直接播放 RTSP，需要媒体网关" };
  if (normalized.includes(".m3u8") || normalized.includes("/hls/")) return { kind: "hls", url, browserPlayable: true, label: "HLS 播放", reason: "需要原生 HLS 或 HLS.js 播放器" };
  if (normalized.includes(".flv") || normalized.includes("/flv/")) return { kind: "http-flv", url, browserPlayable: true, label: "HTTP-FLV 播放", reason: "需要 flv.js 或兼容播放器" };
  return { kind: "unknown", url, browserPlayable: false, label: "未知媒体", reason: "尚未识别该播放地址格式" };
}

export function choosePlayback(session: LiveSession): PlaybackState {
  return classifyPlaybackUrl(session.hlsUrl ?? session.httpFlvUrl ?? session.rtmpUrl ?? session.ingestUrl);
}

export interface MakerverseLiveAdapter {
  listOnline(): Promise<LiveSession[]>;
  getEndpoint(liveId: string): Promise<LiveSession>;
}

export function createMakerverseLiveAdapter(baseUrl: string, token?: string): MakerverseLiveAdapter {
  const root = baseUrl.replace(/\/+$/, "");
  async function request(path: string): Promise<unknown> {
    const response = await fetch(`${root}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) throw new Error(`Makerverse ${response.status} ${response.statusText}`);
    return response.json() as Promise<unknown>;
  }
  return {
    listOnline: async () => {
      const raw = await request("/lives/online");
      return Array.isArray(raw) ? raw.map((item) => normalizeLiveSession(item)) : [];
    },
    getEndpoint: async (liveId) => normalizeLiveSession(
      await request(`/lives/${encodeURIComponent(liveId)}/endpoint`),
      liveId,
    ),
  };
}
