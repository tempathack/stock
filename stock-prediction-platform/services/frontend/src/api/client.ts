import axios from "axios";

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

export default apiClient;
