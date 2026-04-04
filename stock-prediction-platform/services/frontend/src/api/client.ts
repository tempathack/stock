import axios from "axios";
import type { MacroHistoryPoint, MacroLatest } from "./types";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[API]", error.response?.status, error.message);
    return Promise.reject(error);
  },
);

export async function fetchMacroLatest(): Promise<MacroLatest> {
  const res = await fetch(
    `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/market/macro/latest`,
  );
  if (!res.ok) throw new Error("Failed to fetch macro data");
  return res.json() as Promise<MacroLatest>;
}

export async function fetchMacroHistory(days: number = 90): Promise<MacroHistoryPoint[]> {
  const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const res = await fetch(`${base}/market/macro/history?days=${days}`);
  if (!res.ok) throw new Error("Failed to fetch macro history");
  return res.json() as Promise<MacroHistoryPoint[]>;
}

export default apiClient;
