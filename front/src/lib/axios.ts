import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";
import { useUserStore } from "@/store/useUserStore";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface RefreshResponse {
  access_token: string;
  refresh_token?: string;
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(refreshToken: string): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<RefreshResponse>(`${API_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      })
      .then((res) => res.data.access_token)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const { accessToken } = useUserStore.getState();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!original || original._retry || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (
      original.url?.includes("/auth/login") ||
      original.url?.includes("/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    const { refreshToken } = useUserStore.getState();

    if (!refreshToken) {
      useUserStore.getState().clearSession();
      return Promise.reject(error);
    }

    original._retry = true;

    try {
      const newAccessToken = await refreshAccessToken(refreshToken);
      useUserStore.getState().setTokens(newAccessToken, refreshToken);
      original.headers.Authorization = `Bearer ${newAccessToken}`;
      return api(original);
    } catch (refreshError) {
      useUserStore.getState().clearSession();
      return Promise.reject(refreshError);
    }
  },
);

export default api;
