import { useState, type FormEvent, type ChangeEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { api } from "../api";
import type { PayoutResponse } from "../types";

function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export default function Payout() {
  const navigate = useNavigate();
  const { auth } = useAuth();

  const [amountInRupees, setAmountInRupees] = useState("");
  const [bankAccountId, setBankAccountId] = useState("");
  const [idempotencyKey] = useState(generateIdempotencyKey);
  const [status, setStatus] = useState<"success" | "error" | null>(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [responseData, setResponseData] = useState<PayoutResponse | null>(null);

  const amountInPaise = amountInRupees ? Math.round(parseFloat(amountInRupees) * 100) : 0;

  const handleChange =
    (setter: (v: string) => void) => (e: ChangeEvent<HTMLInputElement>) => {
      setter(e.target.value);
      setStatus(null);
    };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!amountInPaise || amountInPaise <= 0) return;

    setLoading(true);
    setStatus(null);
    setMessage("");
    setResponseData(null);

    const result = await api.payout(
      auth?.access_token ?? "",
      amountInPaise,
      bankAccountId,
      idempotencyKey,
    );

    if (!result.ok) {
      setStatus("error");
      setMessage(result.error);
    } else {
      setStatus("success");
      setMessage("Payout request submitted successfully.");
      setResponseData(result.data);
    }

    setLoading(false);
  };

  const displayAmount = amountInRupees
    ? parseFloat(amountInRupees).toLocaleString("en-IN", { minimumFractionDigits: 2 })
    : "0.00";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Nav */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate("/dashboard")}
            className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            ← Dashboard
          </button>
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-black" />
            <span className="font-semibold text-gray-900">PayApp</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <div className="grid lg:grid-cols-2 gap-12 items-start">

          {/* Form */}
          <div>
            <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-1">Payout</p>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Request funds</h1>
            <p className="text-gray-400 text-sm mb-8">Enter the amount you'd like to withdraw.</p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Amount */}
              <div>
                <label className="block text-xs font-mono text-gray-500 mb-1.5 tracking-widest uppercase">
                  Amount (₹)
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 text-sm">₹</span>
                  <input
                    type="number"
                    min="1"
                    step="0.01"
                    value={amountInRupees}
                    onChange={handleChange(setAmountInRupees)}
                    required
                    placeholder="0.00"
                    className="w-full bg-white border border-gray-200 rounded-lg pl-8 pr-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 transition-all"
                  />
                </div>
                {amountInPaise > 0 && (
                  <p className="text-xs font-mono text-gray-400 mt-1">
                    = {amountInPaise.toLocaleString("en-IN")} paise
                  </p>
                )}
              </div>

              {/* Bank Account ID */}
              <div>
                <label className="block text-xs font-mono text-gray-500 mb-1.5 tracking-widest uppercase">
                  Bank Account ID
                </label>
                <input
                  type="text"
                  value={bankAccountId}
                  onChange={handleChange(setBankAccountId)}
                  required
                  placeholder="ACC123456"
                  className="w-full bg-white border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:border-gray-900 focus:ring-1 focus:ring-gray-900 transition-all"
                />
              </div>

              {status === "error" && (
                <p className="text-red-600 text-sm border border-red-200 bg-red-50 rounded-lg px-4 py-3">
                  {message}
                </p>
              )}

              <button
                type="submit"
                disabled={loading || !amountInRupees || amountInPaise <= 0 || !bankAccountId}
                className="w-full bg-gray-900 text-white text-sm font-medium py-3 rounded-lg hover:bg-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {loading ? "Processing…" : `Request ₹${displayAmount}`}
              </button>
            </form>
          </div>

          {/* Preview / Response panel */}
          {status === "success" ? (
            <div className="bg-gray-900 rounded-xl p-8">
              <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-2">Status</p>
              <p className="text-2xl font-bold text-white mb-1">Request submitted</p>
              <p className="text-gray-400 text-sm mb-6">{message}</p>

              {responseData && (
                <div className="border-t border-gray-700 pt-6 mb-6">
                  <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-3">Response</p>
                  <pre className="text-xs font-mono text-gray-500 whitespace-pre-wrap break-all leading-relaxed">
                    {JSON.stringify(responseData, null, 2)}
                  </pre>
                </div>
              )}

              <button
                onClick={() => navigate("/dashboard")}
                className="text-sm text-gray-400 hover:text-white transition-colors"
              >
                ← Back to dashboard
              </button>
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl p-8">
              <p className="text-xs font-mono text-gray-400 tracking-widest uppercase mb-6">Preview</p>
              <div className="space-y-3">
                <div className="flex justify-between items-center pb-4 border-b border-gray-100">
                  <span className="text-sm text-gray-500">Amount</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {amountInRupees ? `₹${displayAmount}` : "₹—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-gray-500">In paise</span>
                  <span className="font-mono text-sm text-gray-900">
                    {amountInPaise > 0 ? amountInPaise.toLocaleString("en-IN") : "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-gray-500">Bank Account</span>
                  <span className="font-mono text-xs text-gray-900 truncate max-w-[160px]">
                    {bankAccountId || "—"}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2">
                  <span className="text-sm text-gray-500">Account</span>
                  <span className="font-mono text-xs text-gray-900 truncate max-w-[160px]">
                    {auth?.email ?? "—"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}