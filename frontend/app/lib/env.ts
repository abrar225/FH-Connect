export const API_VERSION = "v1";
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const getApiUrl = (endpoint: string) => `${API_BASE}/${API_VERSION}${endpoint}`;

export const getWsUrl = (endpoint: string) => {
  const wsBase = API_BASE.replace("http://", "ws://").replace("https://", "wss://");
  return `${wsBase}${endpoint}`;
};
