import axios from "axios";
import type { MacroLatest } from "./types";

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
    `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/macro/latest`,
  );
  if (!res.ok) throw new Error("Failed to fetch macro data");
  return res.json() as Promise<MacroLatest>;
}

export default apiClient;
