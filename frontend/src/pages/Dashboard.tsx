import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { api } from "../api";
import type { DashboardResponse, Payout, Ledger, ApiStatus, DisplayStatus } from "../types";

// ─── Helpers ──────────────────────────────────────────────────────────────────

const STATUS_MAP: Record<ApiStatus, DisplayStatus> = {
  pending: "hold",
  processing: "hold",
  completed: "completed",
  failed: "failed",
};

function mapStatus(raw: ApiStatus): DisplayStatus {
  return STATUS_MAP[raw] ?? "hold";
}

function formatDateTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

function formatPaise(paise: number): string {
  return new Intl.NumberFormat("en-IN").format(paise);
}

// ─── Status Badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: DisplayStatus }) {
  const styles: Record<DisplayStatus, string> = {
    completed: "bg-gray-100 text-gray-700 border-gray-200",
    failed: "bg-gray-100 text-gray-500 border-gray-200 line-through",
    hold: "bg-gray-100 text-gray-600 border-gray-200",
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono border ${styles[status]}`}>
      {status}
    </span>
  );
}

// ─── Table ────────────────────────────────────────────────────────────────────

function Table({
  label,
  count,
  headers,
  children,
  empty,
}: {
  label: string;
  count: number;
  headers: string[];
  children: React.ReactNode;
  empty: boolean;
}) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-mono text-gray-400 tracking-widest uppercase">{label}</p>
        <span className="text-xs font-mono text-gray-300">{count} record{count !== 1 ? "s" : ""}</span>
      </div>
      {empty ? (
        <div className="border border-gray-200 rounded-xl px-6 py-12 text-center">
          <p className="text-gray-400 text-sm">No records yet.</p>
        </div>
      ) : (
        <div className="border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  {headers.map((h) => (
                    <th key={h} className="text-left px-5 py-3 text-xs font-mono text-gray-400 tracking-widest uppercase whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>{children}</tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate();
  const { auth, logout } = useAuth();

  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboard = async () => {
      setLoading(true);
      setError("");
      const result = await api.dashboard(auth?.access_token ?? "");
      if (!result.ok) {
        setError(result.error);
      } else {
        setDashboard(result.data);
      }
      setLoading(false);
    };
    void fetchDashboard();
  }, [auth?.access_token]);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const initials = `${auth?.first_name?.[0] ?? ""}${auth?.last_name?.[0] ?? ""}`.toUpperCase();
  const payouts: Payout[] = dashboard?.payout_list ?? [];
  const ledgers: Ledger[] = dashboard?.ledger_list ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-black" />
            <span className="font-semibold text-gray-900">PayApp</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center">
              <span className="text-white text-xs font-mono">{initials}</span>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        {/* Greeting */}
        <div>
          <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-1">Dashboard</p>
          <h1 className="text-3xl font-bold text-gray-900">
            Good day, {auth?.first_name ?? "there"}
          </h1>
          <p className="text-gray-400 text-sm mt-0.5">{auth?.email}</p>
        </div>

        {/* Loading */}
        {loading && <p className="text-gray-400 text-sm py-8">Loading…</p>}

        {/* Error */}
        {!loading && error && (
          <p className="text-red-600 text-sm border border-red-200 bg-red-50 rounded-xl px-5 py-4">
            {error}
          </p>
        )}

        {/* Data */}
        {!loading && !error && dashboard && (
          <>
            {/* Balance cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-gray-900 rounded-xl p-6">
                <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-3">Available Balance</p>
                <p className="text-3xl font-bold text-white leading-none">{formatPaise(dashboard.available_balance)}</p>
                <p className="text-xs font-mono text-gray-500 mt-1 uppercase tracking-widest">paise</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl p-6">
                <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-3">Hold Balance</p>
                <p className="text-3xl font-bold text-gray-900 leading-none">{formatPaise(dashboard.hold_balance)}</p>
                <p className="text-xs font-mono text-gray-400 mt-1 uppercase tracking-widest">paise</p>
              </div>
            </div>

            {/* Payout history */}
            <Table
              label="Payout Request History"
              count={payouts.length}
              headers={["Amount (paise)", "Status", "Date & Time"]}
              empty={payouts.length === 0}
            >
              {payouts.map((p, i) => (
                <tr key={i} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-gray-900 font-medium">{formatPaise(p.amount_in_paise)}</td>
                  <td className="px-5 py-3.5"><StatusBadge status={mapStatus(p.status)} /></td>
                  <td className="px-5 py-3.5 text-gray-400 text-xs whitespace-nowrap">{formatDateTime(p.created_at)}</td>
                </tr>
              ))}
            </Table>

            {/* Ledger */}
            <Table
              label="Ledger"
              count={ledgers.length}
              headers={["Amount (paise)", "Entry Type", "Date & Time"]}
              empty={ledgers.length === 0}
            >
              {ledgers.map((l, i) => (
                <tr key={i} className="border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3.5 font-mono text-gray-900 font-medium">{formatPaise(l.amount_in_paise)}</td>
                  <td className="px-5 py-3.5 font-mono text-xs text-gray-500">{l.entry_type}</td>
                  <td className="px-5 py-3.5 text-gray-400 text-xs whitespace-nowrap">{formatDateTime(l.created_at)}</td>
                </tr>
              ))}
            </Table>
          </>
        )}

        {/* Payout CTA */}
        {!loading && (
          <div>
            <button
              onClick={() => navigate("/payout")}
              className="bg-gray-900 text-white text-sm font-medium px-6 py-3 rounded-lg hover:bg-black transition-colors"
            >
              Request Payout →
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
