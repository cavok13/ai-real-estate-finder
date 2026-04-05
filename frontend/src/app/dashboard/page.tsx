"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { analyzeProperty, AnalysisResponse } from "@/lib/api";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const { user, token } = useAuthStore();

  const [url, setUrl] = useState("");
  const [price, setPrice] = useState("");
  const [rent, setRent] = useState("");
  const [roi, setRoi] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [propType, setPropType] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user || !token) {
    router.push("/login");
    return null;
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await analyzeProperty(token, {
        property_url: url,
        price: price ? Number(price) : null,
        rent_estimate: rent ? Number(rent) : null,
        roi: roi ? Number(roi) : null,
        city: city || null,
        country: country || null,
        property_type: propType || null,
        notes: notes || null,
        extra_data: { source: "frontend_dashboard" },
      });
      setResult(data);
    } catch (err: unknown) {
      setError((err as Error).message || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const decisionColor =
    result?.analysis.decision === "BUY"
      ? "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
      : result?.analysis.decision === "AVOID"
      ? "text-red-400 bg-red-400/10 border-red-400/30"
      : "text-amber-300 bg-amber-300/10 border-amber-300/30";

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold">Property Analysis</h1>
          <p className="text-slate-400 text-sm mt-1">
            Paste a listing URL and let AI evaluate the deal for you.
          </p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="border border-slate-800 rounded-lg px-4 py-2 bg-slate-900/50 text-center">
            <p className="text-xs text-slate-500 mb-0.5">Credits</p>
            <p className="text-emerald-400 font-bold text-lg leading-none">
              {user.total_credits}
            </p>
          </div>
          <div className="border border-slate-800 rounded-lg px-4 py-2 bg-slate-900/50 text-center">
            <p className="text-xs text-slate-500 mb-0.5">Plan</p>
            <p className="text-slate-200 font-semibold capitalize leading-none">
              {user.plan}
            </p>
          </div>
          {user.total_credits < 3 && (
            <Link
              href="/pricing"
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 font-semibold px-3 py-2 rounded text-xs"
            >
              Buy credits
            </Link>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-[1.6fr,2fr] gap-8">
        {/* Form */}
        <form onSubmit={onSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium mb-1.5">
              Property URL <span className="text-red-400">*</span>
            </label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.bayut.com/property/details-..."
              className="w-full"
            />
            <p className="text-xs text-slate-500 mt-1">
              Any listing URL — Bayut, Rightmove, Zillow, Immobilier, etc.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">Price</label>
              <input
                type="number"
                min={0}
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="250000"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Annual rent</label>
              <input
                type="number"
                min={0}
                value={rent}
                onChange={(e) => setRent(e.target.value)}
                placeholder="18000"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">ROI %</label>
              <input
                type="number"
                step="0.1"
                value={roi}
                onChange={(e) => setRoi(e.target.value)}
                placeholder="7.2"
                className="w-full"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium mb-1">City</label>
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Dubai"
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Country</label>
              <input
                type="text"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="UAE"
                className="w-full"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">Property type</label>
            <select
              value={propType}
              onChange={(e) => setPropType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm"
            >
              <option value="">— Select —</option>
              <option value="apartment">Apartment</option>
              <option value="villa">Villa / House</option>
              <option value="studio">Studio</option>
              <option value="townhouse">Townhouse</option>
              <option value="commercial">Commercial</option>
              <option value="land">Land / Plot</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">
              Notes for AI (optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Needs renovation, off-plan, near metro..."
              className="w-full resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !url}
            className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:opacity-60 text-slate-900 font-semibold py-2.5 rounded"
          >
            {loading ? "Analyzing deal..." : "Analyze this deal →"}
          </button>

          {error && (
            <p className="text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded px-3 py-2">
              {error}
            </p>
          )}

          <p className="text-xs text-slate-500">
            1 credit per analysis. Repeated analyses of the same URL are cached and free.
          </p>
        </form>

        {/* Results */}
        <div className="border border-slate-800 rounded-2xl bg-slate-900/30 p-5 min-h-[300px]">
          {!result && !loading && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 space-y-3">
              <span className="text-4xl">🏠</span>
              <p className="text-slate-400 text-sm max-w-xs">
                Fill in the form and click "Analyze this deal" to see the AI
                investor analysis here.
              </p>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12 space-y-3">
              <span className="text-4xl animate-spin">⚙️</span>
              <p className="text-slate-400 text-sm animate-pulse">
                AI is analyzing the deal...
              </p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-slate-50">
                    {result.analysis.headline}
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {result.cached ? "Cached result" : "New analysis"} · {result.provider} /{" "}
                    {result.model}
                  </p>
                </div>
                <span
                  className={
                    "px-3 py-1 rounded-full text-xs font-bold border " + decisionColor
                  }
                >
                  {result.analysis.decision}
                </span>
              </div>

              <p className="text-slate-300 text-sm leading-relaxed">
                {result.analysis.summary}
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div className="border border-emerald-500/20 bg-emerald-500/5 rounded-xl p-3">
                  <h3 className="text-xs font-semibold text-emerald-400 mb-2 uppercase tracking-wide">
                    Strengths
                  </h3>
                  <ul className="space-y-1.5">
                    {result.analysis.strengths?.map((s, i) => (
                      <li key={i} className="text-xs text-slate-300 flex gap-1.5">
                        <span className="text-emerald-400 mt-0.5">✓</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="border border-red-500/20 bg-red-500/5 rounded-xl p-3">
                  <h3 className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wide">
                    Risks
                  </h3>
                  <ul className="space-y-1.5">
                    {result.analysis.risks?.map((r, i) => (
                      <li key={i} className="text-xs text-slate-300 flex gap-1.5">
                        <span className="text-red-400 mt-0.5">⚠</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="border border-slate-800 rounded-xl p-4 space-y-2 text-xs text-slate-300">
                <div>
                  <span className="font-semibold text-slate-100">Score explanation: </span>
                  {result.analysis.score_explanation}
                </div>
                <div>
                  <span className="font-semibold text-slate-100">Next step: </span>
                  {result.analysis.next_step}
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                <span>
                  Credits remaining:{" "}
                  <span className="text-emerald-400 font-semibold">
                    {result.remaining_credits}
                  </span>
                </span>
                {result.credit_source && (
                  <span>Source: {result.credit_source}</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
