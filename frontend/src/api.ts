import type { LoginResponse, DashboardResponse, PayoutResponse, ApiError } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api/v1";

type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResult<T>> {
  const { headers: extraHeaders, ...rest } = options;
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      credentials: "omit",
      headers: { "Content-Type": "application/json", ...extraHeaders },
      ...rest,
    });
    const json = (await res.json()) as T | ApiError;
    if (!res.ok) {
      const err = json as ApiError;
      return { ok: false, error: err.detail ?? err.message ?? "Something went wrong." };
    }
    return { ok: true, data: json as T };
  } catch {
    return { ok: false, error: "Unable to reach server. Check your connection." };
  }
}

export const api = {
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  dashboard: (token: string) =>
    request<DashboardResponse>("/dashboard/", {
      headers: { Authorization: `Bearer ${token}` },
    }),

  payout: (token: string, amountInPaise: number, bankAccountId: string, idempotencyKey: string) =>
    request<PayoutResponse>("/payout/request/", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({ amount_in_paise: amountInPaise, bank_account_id: bankAccountId }),
    }),
};