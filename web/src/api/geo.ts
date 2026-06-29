import { authFetch } from "./client";

export interface GeoMeResponse {
  ip: string;
  province?: string | null;
  city?: string | null;
  adcode?: string | null;
  weather?: string | null;
  temperature?: string | null;
}

export async function getGeoMe(): Promise<GeoMeResponse | null> {
  try {
    const response = await authFetch("/geo/me");
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as GeoMeResponse;
  } catch {
    return null;
  }
}
