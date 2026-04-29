// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface LoginResponse {
  first_name: string;
  last_name: string;
  email: string;
  access_token: string;
  refresh_token: string;
  access_token_life_time_in_seconds: number;
  refresh_token_life_time_in_seconds: number;
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

/** Status values as returned by the API */
export type ApiStatus = "pending" | "processing" | "completed" | "failed";

/** Display status: pending/processing → hold */
export type DisplayStatus = "hold" | "completed" | "failed";

export interface Transaction {
  amount_in_paise: number;
  status: ApiStatus;
  datetime: string;
}

export interface Payout {
  amount_in_paise: number;
  status: ApiStatus;
  created_at: string;
}

export interface Ledger {
  amount_in_paise: number;
  entry_type: string;
  created_at: string;
}

export interface DashboardResponse {
  available_balance: number;
  hold_balance: number;
  transactions: Transaction[];
  payout_list: Payout[];
  ledger_list: Ledger[];
}

// ─── Payout ───────────────────────────────────────────────────────────────────

export interface PayoutResponse {
  [key: string]: unknown;
}

// ─── API Error ────────────────────────────────────────────────────────────────

export interface ApiError {
  detail?: string;
  message?: string;
}
