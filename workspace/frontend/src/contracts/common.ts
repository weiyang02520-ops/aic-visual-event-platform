export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };
export type IsoTimestamp = string;

export interface ApiErrorPayload {
  detail?: string | JsonValue;
  error?: string;
  message?: string;
}

export class ContractApiError extends Error {
  readonly status: number;
  readonly detail?: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ContractApiError";
    this.status = status;
    this.detail = detail;
  }
}
