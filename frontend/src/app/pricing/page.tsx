"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { createCheckoutSession } from "@/lib/api";

const plans = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    period: "forever",
    desc: "Try the engine on your first deals.",
    features: [
      "3 AI-powered analyses",
      "Full investor summary per deal",
      "BUY / REVIEW / AVOID verdict",
      "Email verification required",
    ],
    cta: "Get started free",
    highlight: false,
  },
  {
    id: "starter",
    name: "Starter",
    price: "€19",
    period: "per month",
    desc: "For active investors running regular deal checks.",
    features: [
      "100 AI analyses / month",
      "All Free features",
      "Saved analysis history",
      "Global deal search",
      "Priority support",
    ],
    cta: "Upgrade to Starter",
    highlight: true,
    badge: "Most popular",
  },
  {
    id: "pro",
    name: "Pro",
    price: "€49",
    period: "per month",
    desc: "For power users and small investment teams.",
    features: [
      "500 AI analyses / month",
      "All Starter features",
      "Priority AI processing",
      "Advanced reporting (soon)",
      "API access (soon)",
    ],
    cta: "Upgrade to Pro",
    highlight: false,
  },
];

export default function PricingPage() {
  const router = useRouter();
  const { user, token } = useAuthStore();

  const handleUpgrade = async (planId: "starter" | "pro") => {
    if (!token) { router.push("/login"); return; }
    try {
      const { checkout_url } = await createCheckoutSession(token, planId);
      window.location.href = checkout_url;
    } catch (err: unknown) {
      alert((err as Error).message || "Unable to start checkout");
    }
  };

  const handleCta = (planId: string) => {
    if (planId === "free") {
      router.push(user ? "/dashboard" : "/register");
    } else {
      handleUpgrade(planId as "starter" | "pro");
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-14">
      <div className="text-center mb-12">
        <h1 className="text-3xl font-bold mb-3">Simple, transparent pricing</h1>
        <p className="text-slate-400 text-base">
          Start free, upgrade when you&apos;re ready to scale your deal flow.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={
              "relative rounded-2xl p-6 flex flex-col border " +
              (plan.highlight
                ? "border-emerald-500 bg-emerald-500/5"
                : "border-slate-800 bg-slate-900/30")
            }
          >
            {plan.badge && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold bg-emerald-500 text-slate-900 px-3 py-0.5 rounded-full">
                {plan.badge}
              </span>
            )}

            <div className="mb-5">
              <h2 className="font-bold text-lg mb-1">{plan.name}</h2>
              <p className="text-slate-400 text-sm">{plan.desc}</p>
            </div>

            <div className="mb-5">
              <span className="text-4xl font-bold">{plan.price}</span>
              <span className="text-slate-400 text-sm ml-2">{plan.period}</span>
            </div>

            <ul className="space-y-2 mb-8 flex-1">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                  <span className="text-emerald-400 mt-0.5 shrink-0">✓</span>
                  {f}
                </li>
              ))}
            </ul>

            <button
              onClick={() => handleCta(plan.id)}
              className={
                "w-full py-2.5 rounded font-semibold " +
                (plan.highlight
                  ? "bg-emerald-500 hover:bg-emerald-400 text-slate-900"
                  : "border border-slate-700 hover:border-slate-500 text-slate-100")
              }
            >
              {plan.cta}
            </button>
          </div>
        ))}
      </div>

      <p className="text-center text-xs text-slate-500 mt-10">
        All paid plans auto-renew monthly. Cancel anytime. Credits reset each billing cycle.
      </p>
    </div>
  );
}
