"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { searchDeals, SearchDealsResponse } from "@/lib/api";
import Link from "next/link";

type Strategy = "rental_yield" | "capital_growth" | "balanced";

const REGIONS = [
  { code: "USA", label: "🇺🇸 USA" },
  { code: "UAE", label: "🇦🇪 UAE" },
  { code: "UK", label: "🇬🇧 UK" },
  { code: "France", label: "🇫🇷 France" },
  { code: "Germany", label: "🇩🇪 Germany" },
  { code: "Spain", label: "🇪🇸 Spain" },
  { code: "Portugal", label: "🇵🇹 Portugal" },
  { code: "Turkey", label: "🇹🇷 Turkey" },
  { code: "Thailand", label: "🇹🇭 Thailand" },
  { code: "Morocco", label: "🇲🇦 Morocco" },
];

export default function GlobalDealsPage() {
  const router = useRouter();
  const { user, token } = useAuthStore();

  const [budgetMin, setBudgetMin] = useState("");
  const [budgetMax, setBudgetMax] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [regions, setRegions] = useState<string[]>(["UAE", "USA"]);
  const [city, setCity] = useState("");
  const [strategy, setStrategy] = useState<Strategy>("balanced");
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState<SearchDealsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user || !token) {
    router.push("/login");
    return null;
  }

  const toggleRegion = (code: string) =>
    setRegions((prev) =>
      prev.includes(code) ? prev.filter((r) => r !== code) : [...prev, code]
    );

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setError(null);
    setRes(null);
    setLoading(true);
    try {
      const data = await searchDeals(token, {
        budget_min: Number(budgetMin),
        budget_max: Number(budgetMax),
        currency,
        countries: regions,
        cities: city ? [city] : [],
        strategy,
        limit: 12,
      });
      setRes(data);
    } catch (err: unknown) {
      setError((err as Error).message || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-10">
      <div className="pb-4 border-b border-slate-800">
        <h1 className="text-2xl font-bold mb-1">Global Deal Search</h1>
        <p className="text-slate-400 text-sm">
          Set your budget and strategy — AI surfaces the strongest property
          deals worldwide and explains each one.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="grid md:grid-cols-[1.2fr,1fr] gap-8 items-start"
      >
        <div className="space-y-6">
          {/* Budget */}
          <div>
            <label className="block text-sm font-medium mb-2">Budget range</label>
            <div className="flex gap-2">
              <input
                type="number"
                min={0}
                required
                value={budgetMin}
                onChange={(e) => setBudgetMin(e.target.value)}
                placeholder="Min: 200,000"
                className="flex-1"
              />
              <input
                type="number"
                min={0}
                required
                value={budgetMax}
                onChange={(e) => setBudgetMax(e.target.value)}
                placeholder="Max: 500,000"
                className="flex-1"
              />
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-20 bg-slate-900 border border-slate-700 rounded px-2 py-2 text-sm"
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="AED">AED</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
          </div>

          {/* Regions */}
          <div>
            <label className="block text-sm font-medium mb-2">Target regions</label>
            <div className="flex flex-wrap gap-2">
              {REGIONS.map(({ code, label }) => {
                const active = regions.includes(code);
                return (
                  <button
                    key={code}
                    type="button"
                    onClick={() => toggleRegion(code)}
                    className={
                      "text-xs px-3 py-1.5 rounded-full border transition-colors " +
                      (active
                        ? "bg-emerald-500 text-slate-900 border-emerald-400 font-semibold"
                        : "border-slate-700 text-slate-300 hover:border-slate-500")
                    }
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* City */}
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Preferred city{" "}
              <span className="text-slate-500 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Dubai, London, Miami, Lisbon..."
              className="w-full"
            />
          </div>

          {/* Strategy */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Investment strategy
            </label>
            <div className="flex flex-wrap gap-2 text-xs">
              {(
                [
                  { value: "rental_yield", label: "📈 High rental yield" },
                  { value: "capital_growth", label: "🚀 Capital growth" },
                  { value: "balanced", label: "⚖️ Balanced" },
                ] as { value: Strategy; label: string }[]
              ).map(({ value, label }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setStrategy(value)}
                  className={
                    "px-3 py-1.5 rounded-full border transition-colors " +
                    (strategy === value
                      ? "bg-emerald-500 text-slate-900 border-emerald-400 font-semibold"
                      : "border-slate-700 text-slate-300 hover:border-slate-500")
                  }
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading || regions.length === 0}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-60 text-slate-900 font-semibold py-2.5 rounded"
            >
              {loading ? "Searching worldwide..." : "Find best deals →"}
            </button>
            <p className="text-xs text-slate-500 mt-2">
              Uses 1 credit. AI ranks and explains every opportunity found.
            </p>
            {error && (
              <p className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded px-3 py-2 mt-2">
                {error}
              </p>
            )}
          </div>
        </div>

        {/* AI Summary panel */}
        <div className="border border-slate-800 rounded-2xl bg-slate-900/30 p-5 min-h-[220px]">
          {!res && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center py-8 space-y-2">
              <span className="text-4xl">🌍</span>
              <p className="text-slate-400 text-sm">
                AI strategy summary and diversified plan will appear here after
                your search.
              </p>
            </div>
          )}
          {loading && (
            <div className="flex flex-col items-center justify-center h-full text-center py-8 space-y-2">
              <span className="text-4xl animate-spin">🌐</span>
              <p className="text-slate-400 text-sm animate-pulse">
                Scanning global markets...
              </p>
            </div>
          )}
          {res && !loading && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-sm font-bold text-slate-100">
                  AI Strategy Summary
                </h2>
                <span className="text-[10px] text-slate-500">
                  {res.provider} · {res.remaining_credits} credits left
                </span>
              </div>
              <p className="text-sm text-slate-300 leading-relaxed">
                {res.ai_summary?.strategy_summary}
              </p>
              <div className="border border-slate-800 rounded-xl p-3">
                <p className="text-xs font-semibold text-slate-100 mb-2">
                  Diversified plan
                </p>
                <pre className="text-[11px] text-slate-400 whitespace-pre-wrap overflow-auto max-h-40">
                  {JSON.stringify(res.ai_summary?.diversified_plan, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </form>

      {/* Deals grid */}
      {res && res.deals.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">
            Top {res.deals.length} matching deals
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {res.deals.map((deal) => {
              const aiDeal = res.ai_summary?.best_deals?.find(
                (d) => d.id === deal.id
              );
              const decision = aiDeal?.decision || "REVIEW";
              const decisionStyle =
                decision === "BUY"
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                  : decision === "AVOID"
                  ? "bg-red-500/20 text-red-300 border-red-500/40"
                  : "bg-amber-500/10 text-amber-200 border-amber-500/30";

              return (
                <article
                  key={deal.id}
                  className="border border-slate-800 rounded-xl bg-slate-900/40 p-4 flex flex-col gap-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-slate-50 text-sm leading-snug">
                      {aiDeal?.headline ||
                        `${deal.city || "Unknown"}, ${deal.country || ""}`}
                    </h3>
                    <span
                      className={
                        "shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold border " +
                        decisionStyle
                      }
                    >
                      {decision}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400 space-y-0.5">
                    <p>
                      💰{" "}
                      {deal.price
                        ? deal.price.toLocaleString() +
                          " " +
                          (deal.currency || currency)
                        : "Price N/A"}
                    </p>
                    <p>
                      📍 {deal.city || "—"}, {deal.country || "—"}
                    </p>
                    {deal.score != null && (
                      <p>🎯 Score: {deal.score.toFixed(1)}</p>
                    )}
                  </div>

                  {aiDeal && (
                    <div className="text-[11px] text-slate-300 space-y-1.5 border-t border-slate-800 pt-2">
                      <p>
                        <span className="font-semibold text-emerald-400">
                          Why good:{" "}
                        </span>
                        {aiDeal.why_good}
                      </p>
                      <p>
                        <span className="font-semibold text-red-400">
                          Risk:{" "}
                        </span>
                        {aiDeal.risks}
                      </p>
                      {aiDeal.suggested_strategy && (
                        <p className="text-slate-400">
                          Strategy: {aiDeal.suggested_strategy}
                        </p>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between mt-auto pt-1">
                    <a
                      href={deal.url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-emerald-400 hover:text-emerald-300 underline"
                    >
                      View listing →
                    </a>
                    <span className="text-[10px] text-slate-600">
                      {deal.source}
                    </span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      {res && res.deals.length === 0 && (
        <div className="border border-slate-800 rounded-xl bg-slate-900/30 p-8 text-center">
          <p className="text-slate-400 text-sm mb-3">
            No deals found matching your filters. Try widening your budget or
            adding more regions.
          </p>
          <button
            onClick={() => { setRes(null); setBudgetMin(""); setBudgetMax(""); }}
            className="text-emerald-400 text-sm underline"
          >
            Reset and try again
          </button>
        </div>
      )}
    </div>
  );
}
