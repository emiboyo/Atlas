export const API_VERSION = "v1" as const;
export const API_PREFIX = `/api/${API_VERSION}` as const;

export type ServiceStatus = "healthy" | "degraded" | "unhealthy";

export interface HealthResponse {
  status: ServiceStatus;
  service: string;
  version: string;
}
