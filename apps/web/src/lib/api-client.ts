"use client";

export class AtlasApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "AtlasApiError";
  }
}

type ErrorEnvelope = {
  error?: { code?: string; message?: string; request_id?: string };
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function atlasApi<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
      Authorization: `Bearer ${token}`,
    },
  });
  const requestId = response.headers.get("x-request-id") ?? undefined;
  if (!response.ok) {
    let envelope: ErrorEnvelope = {};
    try {
      envelope = (await response.json()) as ErrorEnvelope;
    } catch {
      // The stable fallback intentionally exposes no response body.
    }
    throw new AtlasApiError(
      envelope.error?.message ?? "The request could not be completed.",
      response.status,
      envelope.error?.code ?? "request_failed",
      envelope.error?.request_id ?? requestId,
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
