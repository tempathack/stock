import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig } from "axios";
import type { MacroHistoryPoint, MacroLatest } from "./types";

const TRANSIENT_STATUS_CODES = new Set([502, 503, 504]);
const MAX_RETRIES = 3;
const RETRY_DELAYS_MS = [1000, 2000, 4000];

interface RetryConfig extends InternalAxiosRequestConfig {
  _retryCount?: number;
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig | undefined;
    const status = error.response?.status;

    const isTransient =
      !status || TRANSIENT_STATUS_CODES.has(status); // network error has no status

    if (!config || !isTransient) {
      if (import.meta.env.DEV) {
        console.error("[API]", status, error.message);
      }
      return Promise.reject(error);
    }

    config._retryCount = config._retryCount ?? 0;

    if (config._retryCount >= MAX_RETRIES) {
      if (import.meta.env.DEV) {
        console.error("[API] max retries reached", status, error.message);
      }
      return Promise.reject(error);
    }

    const delay = RETRY_DELAYS_MS[config._retryCount];
    config._retryCount += 1;

    if (import.meta.env.DEV) {
      console.debug(
        `[API] retry ${config._retryCount}/${MAX_RETRIES} after ${delay}ms — status=${status ?? "network error"}`,
      );
    }

    await new Promise((resolve) => setTimeout(resolve, delay));
    return apiClient(config);
  },
);

export async function fetchMacroLatest(): Promise<MacroLatest> {
  const res = await fetch(
    `${import.meta.env.VITE_API_URL || "/api"}/market/macro/latest`,
  );
  if (!res.ok) throw new Error("Failed to fetch macro data");
  return res.json() as Promise<MacroLatest>;
}

export async function fetchMacroHistory(days: number = 90): Promise<MacroHistoryPoint[]> {
  const base = import.meta.env.VITE_API_URL || "/api";
  const res = await fetch(`${base}/market/macro/history?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch macro history");
  return res.json() as Promise<MacroHistoryPoint[]>;
}

export default apiClient;
