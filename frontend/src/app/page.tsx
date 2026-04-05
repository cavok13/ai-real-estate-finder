import Link from "next/link";

export default function HomePage() {
  const features = [
    {
      icon: "🔍",
      title: "Paste any property URL",
      desc: "Bayut, Rightmove, Zillow, Immobilier — any listing link works.",
    },
    {
      icon: "🤖",
      title: "AI-powered analysis",
      desc: "Get ROI, deal score, strengths, risks, and a BUY / REVIEW / AVOID verdict.",
    },
    {
      icon: "🌍",
      title: "Global deal search",
      desc: "Search the world for the best property deals matching your budget and strategy.",
    },
    {
      icon: "⚡",
      title: "Instant results",
      desc: "Analysis in seconds. Cached results never cost extra credits.",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4">
      {/* Hero */}
      <section className="py-16 md:py-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-3 block">
            AI Real Estate Intelligence
          </span>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-5">
            Find and analyze property deals with{" "}
            <span className="text-emerald-400">AI</span>.
          </h1>
          <p className="text-slate-300 text-lg mb-8 leading-relaxed">
            Paste a property link or enter deal numbers. Get instant investor-grade ROI
            analysis, risk flags, and a clear decision — all powered by AI.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link
              href="/register"
              className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-6 py-3 rounded font-semibold text-base"
            >
              Start free — 3 analyses
            </Link>
            <Link
              href="/pricing"
              className="border border-slate-700 hover:border-slate-500 text-slate-200 px-6 py-3 rounded text-base"
            >
              View pricing
            </Link>
          </div>
          <p className="text-xs text-slate-500 mt-4">
            No credit card required. Free plan includes 3 full analyses.
          </p>
        </div>

        {/* Example card */}
        <div className="border border-slate-800 bg-slate-900/50 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-emerald-400">Live example</span>
            <span className="text-xs text-slate-500 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full text-emerald-300">
              BUY
            </span>
          </div>
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3 text-sm">
            <p className="font-semibold text-slate-50 text-base">
              Dubai Marina · 1BR Apartment
            </p>
            <div className="flex gap-4 text-slate-400 text-xs">
              <span>💰 AED 920,000</span>
              <span>📈 ROI: 7.2%</span>
              <span>⚠️ Risk: Medium</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              This unit is slightly under market value for similar 1BRs in Dubai Marina and
              offers a healthy rental yield driven by high occupancy and strong tenant demand.
              Recommend proceeding to due diligence.
            </p>
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <p className="text-emerald-400 text-xs font-semibold mb-1">Strengths</p>
                <ul className="text-xs text-slate-300 space-y-0.5">
                  <li>• Under market value</li>
                  <li>• High rental demand</li>
                  <li>• Strong yield</li>
                </ul>
              </div>
              <div>
                <p className="text-red-400 text-xs font-semibold mb-1">Risks</p>
                <ul className="text-xs text-slate-300 space-y-0.5">
                  <li>• Market sensitivity</li>
                  <li>• Currency exposure</li>
                  <li>• Vacancy possible</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-12 border-t border-slate-900">
        <h2 className="text-2xl font-semibold text-center mb-10">
          Everything you need to evaluate a deal
        </h2>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
          {features.map((f) => (
            <div
              key={f.title}
              className="border border-slate-800 rounded-xl p-5 bg-slate-900/30 space-y-2"
            >
              <span className="text-2xl">{f.icon}</span>
              <h3 className="font-semibold text-slate-100">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 text-center border-t border-slate-900">
        <h2 className="text-2xl font-semibold mb-3">
          Ready to stop guessing on deals?
        </h2>
        <p className="text-slate-400 mb-6 text-sm">
          Join investors using AI to make faster, smarter property decisions.
        </p>
        <Link
          href="/register"
          className="bg-emerald-500 hover:bg-emerald-400 text-slate-900 px-8 py-3 rounded font-semibold"
        >
          Get started free
        </Link>
      </section>
    </div>
  );
}
