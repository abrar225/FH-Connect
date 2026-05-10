import { supabase } from "@/lib/supabase";
import { getApiUrl, getWsUrl } from "@/app/lib/env";

const SESSION_TIMEOUT_MS = 5000;
const FETCH_TIMEOUT_MS = 15000;

function timeout<T>(promise: PromiseLike<T>, timeoutMs: number, label: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error(`${label} timed out`)), timeoutMs);
    Promise.resolve(promise)
      .then(resolve)
      .catch(reject)
      .finally(() => window.clearTimeout(timer));
  });
}

export async function getAccessToken() {
  try {
    const { data } = await timeout(supabase.auth.getSession(), SESSION_TIMEOUT_MS, "Auth session");
    return data.session?.access_token ?? null;
  } catch {
    return null;
  }
}

export async function authFetch(input: string, init: RequestInit = {}) {
  const token = await getAccessToken();
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    return await fetch(input.startsWith("http") ? input : getApiUrl(input), {
      ...init,
      headers,
      signal: init.signal || controller.signal,
    });
  } catch {
    return new Response(JSON.stringify({ detail: "Backend unavailable" }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export async function authWsUrl(endpoint: string) {
  const token = await getAccessToken();
  const separator = endpoint.includes("?") ? "&" : "?";
  return getWsUrl(`${endpoint}${separator}token=${encodeURIComponent(token ?? "")}`);
}
