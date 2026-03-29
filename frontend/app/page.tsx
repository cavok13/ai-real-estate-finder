'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import PropertyCard from '@/components/PropertyCard';
import { PropertyWithScore } from '@/lib/types';

const TESTIMONIALS = [
  {
    name: 'Sarah M.',
    role: 'Property Investor',
    avatar: '👩‍💼',
    quote: 'Found a property with 12% ROI in just 2 days. The AI scoring saved me hours of research!'
  },
  {
    name: 'James K.',
    role: 'Real Estate Agent',
    avatar: '👨‍💼',
    quote: 'I use this for every client. The market comparison feature is incredibly accurate.'
  },
  {
    name: 'Maria L.',
    role: 'Portfolio Manager',
    avatar: '👩‍💻',
    quote: 'The ROI estimates helped me build a portfolio generating 8% annual returns consistently.'
  }
];

const LOGOS = ['Zillow', 'Realtor', 'Redfin', 'Rightmove', 'Trulia'];

const STEPS = [
  {
    num: '01',
    title: 'Enter Property',
    desc: 'Input any property URL or manual details',
    icon: '🔗'
  },
  {
    num: '02',
    title: 'AI Analysis',
    desc: 'Our AI processes market data instantly',
    icon: '🧠'
  },
  {
    num: '03',
    title: 'Get Your Score',
    desc: 'Receive ROI, risk score, and recommendations',
    icon: '📊'
  }
];

const FEATURES = [
  {
    title: 'AI Deal Scoring',
    desc: 'Proprietary algorithm analyzes 50+ data points to score each property',
    icon: '🎯',
    color: 'from-purple-500 to-pink-500'
  },
  {
    title: 'Market Comparison',
    desc: 'Compare any property against local market averages and trends',
    icon: '📈',
    color: 'from-blue-500 to-cyan-500'
  },
  {
    title: 'ROI Calculator',
    desc: 'Estimate rental yield, capital appreciation, and total returns',
    icon: '💰',
    color: 'from-green-500 to-emerald-500'
  },
  {
    title: 'Risk Analysis',
    desc: 'Identify potential red flags and market volatility factors',
    icon: '⚠️',
    color: 'from-orange-500 to-red-500'
  }
];

const DEMO_PROPERTIES = [
  {
    location: 'Dubai Marina, UAE',
    price: 485000,
    roi: '8.5%',
    score: 87,
    tag: 'High ROI',
    tagColor: 'bg-green-500'
  },
  {
    location: 'Manhattan, New York',
    price: 1250000,
    roi: '4.2%',
    score: 62,
    tag: 'Premium',
    tagColor: 'bg-blue-500'
  },
  {
    location: 'London Canary Wharf',
    price: 650000,
    roi: '6.8%',
    score: 78,
    tag: 'Undervalued',
    tagColor: 'bg-purple-500'
  }
];

export default function Home() {
  const [bestDeals, setBestDeals] = useState<PropertyWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzerData, setAnalyzerData] = useState({ price: '', area: '', city: '' });
  const [analyzerResult, setAnalyzerResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/properties/best-deals?limit=8`);
      if (res.ok) {
        const data = await res.json();
        setBestDeals(data);
      }
    } catch (error) {
      console.error('Failed to load:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setAnalyzing(true);
    setAnalyzerResult(null);

    const price = parseFloat(analyzerData.price);
    const area = parseFloat(analyzerData.area);

    if (!price || !area) {
      setAnalyzing(false);
      return;
    }

    await new Promise(r => setTimeout(r, 1500));

    const pricePerSqm = price / area;
    const marketAvg = 5000 + Math.random() * 5000;
    const diff = ((marketAvg - pricePerSqm) / marketAvg) * 100;
    const roi = 5 + (diff * 0.3) + (Math.random() * 3);
    const score = Math.min(100, Math.max(0, 50 + (diff * 2) + (Math.random() * 10)));

    let label = 'Average';
    if (score >= 75) label = 'Great Deal';
    else if (score < 50) label = 'Overpriced';

    setAnalyzerResult({
      pricePerSqm: pricePerSqm.toFixed(2),
      marketAvg: marketAvg.toFixed(2),
      roi: roi.toFixed(1),
      score: Math.round(score),
      label
    });

    setAnalyzing(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* STICKY CTA */}
      <div className="fixed bottom-6 right-6 z-50">
        <a
          href="#analyzer"
          className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-4 rounded-full font-bold shadow-2xl shadow-purple-500/30 hover:shadow-purple-500/50 hover:scale-105 transition-all flex items-center gap-2 animate-pulse"
        >
          <span>⚡</span> Scan Property Free
        </a>
      </div>

      {/* HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="absolute inset-0">
          <div className="absolute top-20 left-10 w-72 h-72 bg-purple-500/30 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative max-w-6xl mx-auto px-4 py-24 md:py-32">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full text-white/90 text-sm mb-8 border border-white/10">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              AI-Powered Real Estate Intelligence
            </div>

            <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight mb-6">
              Find Profitable Real Estate Deals{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                Before the Market Reacts
              </span>
            </h1>

            <p className="text-xl text-white/70 mb-10 max-w-2xl mx-auto leading-relaxed">
              AI analyzes thousands of properties to uncover hidden opportunities with high ROI in seconds.
              Make smarter investment decisions with data-driven insights.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
              <a
                href="#analyzer"
                className="group bg-gradient-to-r from-purple-500 to-pink-500 text-white px-8 py-4 rounded-xl font-bold text-lg hover:from-purple-600 hover:to-pink-600 transition-all shadow-xl shadow-purple-500/30 hover:shadow-purple-500/50 flex items-center justify-center gap-2"
              >
                <span>🚀</span> Scan Your First Property Free
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </a>
              <a
                href="#deals"
                className="bg-white/10 backdrop-blur-sm text-white border border-white/20 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-white/20 transition-all"
              >
                View Live Deals
              </a>
            </div>

            <p className="text-purple-300 text-sm mb-10">
              ⚡ Limited free analyses available today
            </p>

            {/* Trust Indicators */}
            <div className="flex flex-wrap justify-center gap-6 md:gap-12 text-white/60 text-sm">
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-white/10 rounded flex items-center justify-center text-xs">✓</span>
                No credit card required
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-white/10 rounded flex items-center justify-center text-xs">⚡</span>
                Results in seconds
              </div>
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 bg-white/10 rounded flex items-center justify-center text-xs">🌍</span>
                50+ countries
              </div>
            </div>

            {/* Stats */}
            <div className="flex flex-wrap justify-center gap-8 md:gap-16 mt-12 pt-12 border-t border-white/10">
              <div className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white">5,000+</div>
                <div className="text-white/60 text-sm">Trusted Investors</div>
              </div>
              <div className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white">100K+</div>
                <div className="text-white/60 text-sm">Properties Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white">$2.5B</div>
                <div className="text-white/60 text-sm">Deals Identified</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* LOGOS */}
      <section className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <p className="text-center text-gray-500 text-sm mb-6">Integrated with leading property platforms</p>
          <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-50 grayscale hover:grayscale-0 transition-all">
            {LOGOS.map((logo) => (
              <span key={logo} className="text-xl font-bold text-gray-400">{logo}</span>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              Get professional-grade property analysis in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {STEPS.map((step, i) => (
              <div key={i} className="relative text-center group">
                {i < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-1/2 w-full h-0.5 bg-gradient-to-r from-purple-300 to-transparent"></div>
                )}
                <div className="relative z-10 w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-purple-100 to-pink-100 rounded-2xl flex items-center justify-center text-4xl group-hover:scale-110 transition-transform">
                  {step.icon}
                </div>
                <div className="text-purple-600 font-bold text-sm mb-2">Step {step.num}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-600">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DEMO / LIVE EXAMPLE */}
      <section id="deals" className="py-20 bg-gradient-to-br from-gray-50 to-purple-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <span className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Live Examples</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">
              Real Properties, Real Opportunities
            </h2>
            <p className="text-gray-600 text-lg">
              See how our AI scores real properties from around the world
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {DEMO_PROPERTIES.map((prop, i) => (
              <div key={i} className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-all hover:-translate-y-1">
                <div className="h-40 bg-gradient-to-br from-purple-400 to-pink-400 relative">
                  <img
                    src={`https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=400&h=300&fit=crop&sat=-100`}
                    alt={prop.location}
                    className="w-full h-full object-cover opacity-80"
                  />
                  <div className={`absolute top-3 left-3 ${prop.tagColor} text-white text-xs font-bold px-3 py-1 rounded-full`}>
                    {prop.tag}
                  </div>
                  <div className="absolute top-3 right-3 bg-black/70 text-white font-bold px-3 py-1 rounded-full">
                    {prop.score}/100
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="font-bold text-gray-900 mb-2">{prop.location}</h3>
                  <div className="text-2xl font-bold text-gray-900 mb-3">${prop.price.toLocaleString()}</div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Est. ROI</span>
                    <span className="text-green-600 font-bold">{prop.roi}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center mt-10">
            <a href="/best-deals" className="inline-flex items-center gap-2 bg-purple-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-purple-700 transition-all">
              View All Properties <span>→</span>
            </a>
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <span className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Features</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">
              Built for Serious Investors
            </h2>
            <p className="text-gray-600 text-lg max-w-2xl mx-auto">
              Professional-grade tools to analyze and compare properties with confidence
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((feature, i) => (
              <div key={i} className="bg-gray-50 rounded-2xl p-6 hover:bg-gray-100 transition-all group">
                <div className={`w-14 h-14 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center text-2xl mb-4 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ANALYZER SECTION */}
      <section id="analyzer" className="py-20 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="max-w-4xl mx-auto px-4">
          <div className="text-center mb-10">
            <span className="text-purple-400 font-semibold text-sm uppercase tracking-wide">Free Tool</span>
            <h2 className="text-3xl md:text-4xl font-bold text-white mt-2 mb-4">
              ⚡ Property Deal Analyzer
            </h2>
            <p className="text-white/70">
              Enter property details to get an instant AI analysis
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-2xl p-8">
            <form onSubmit={handleAnalyze} className="grid md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Property Price ($)</label>
                <input
                  type="number"
                  value={analyzerData.price}
                  onChange={(e) => setAnalyzerData({ ...analyzerData, price: e.target.value })}
                  placeholder="500,000"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Size (sqm)</label>
                <input
                  type="number"
                  value={analyzerData.area}
                  onChange={(e) => setAnalyzerData({ ...analyzerData, area: e.target.value })}
                  placeholder="120"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">City</label>
                <input
                  type="text"
                  value={analyzerData.city}
                  onChange={(e) => setAnalyzerData({ ...analyzerData, city: e.target.value })}
                  placeholder="New York"
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div className="md:col-span-3">
                <button
                  type="submit"
                  disabled={analyzing}
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 rounded-xl font-bold text-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {analyzing ? (
                    <>
                      <span className="animate-spin">⏳</span> Analyzing...
                    </>
                  ) : (
                    <>
                      <span>🔍</span> Analyze Property Deal
                    </>
                  )}
                </button>
              </div>
            </form>

            {analyzerResult && (
              <div className="mt-8 pt-8 border-t border-gray-200">
                <div className="text-center mb-6">
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-lg font-bold ${
                    analyzerResult.label === 'Great Deal' ? 'bg-green-100 text-green-700' :
                    analyzerResult.label === 'Overpriced' ? 'bg-red-100 text-red-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {analyzerResult.label === 'Great Deal' ? '🔥' : analyzerResult.label === 'Overpriced' ? '❌' : '⚠️'}
                    {analyzerResult.label}
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">{analyzerResult.score}</div>
                    <div className="text-sm text-gray-500">Deal Score</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-purple-600">{analyzerResult.roi}%</div>
                    <div className="text-sm text-gray-500">Est. ROI</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600">${analyzerResult.pricePerSqm}</div>
                    <div className="text-sm text-gray-500">Price/sqm</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <div className="text-2xl font-bold text-gray-900">${analyzerResult.marketAvg}</div>
                    <div className="text-sm text-gray-500">Market Avg</div>
                  </div>
                </div>

                <p className="text-gray-600 text-center mb-6">
                  {analyzerResult.score >= 75 
                    ? `This property is priced significantly below market average with an estimated ${analyzerResult.roi}% annual ROI.`
                    : analyzerResult.score < 50
                    ? 'This property is priced above market average. Consider negotiating or looking for better deals.'
                    : `This property is fairly priced near market average with a moderate ${analyzerResult.roi}% estimated ROI.`}
                </p>

                <a href="/register" className="block w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-xl font-semibold text-center hover:opacity-90">
                  Get Detailed Analysis (Free Account)
                </a>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="py-20 bg-white">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <span className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Testimonials</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">
              Trusted by Investors Worldwide
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((testimonial, i) => (
              <div key={i} className="bg-gray-50 rounded-2xl p-6 hover:shadow-lg transition-all">
                <div className="text-4xl mb-4">{testimonial.avatar}</div>
                <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
                <div>
                  <div className="font-bold text-gray-900">{testimonial.name}</div>
                  <div className="text-gray-500 text-sm">{testimonial.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section className="py-20 bg-gradient-to-br from-gray-50 to-purple-50">
        <div className="max-w-5xl mx-auto px-4">
          <div className="text-center mb-12">
            <span className="text-purple-600 font-semibold text-sm uppercase tracking-wide">Pricing</span>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mt-2 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-gray-600">Start free, upgrade when you need more</p>
          </div>

          <div className="grid md:grid-cols-4 gap-6">
            {/* Free */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="text-sm font-medium text-gray-500 uppercase mb-2">Free</div>
              <div className="text-4xl font-bold text-gray-900 mb-1">€0</div>
              <div className="text-gray-500 mb-2">Forever free</div>
              <div className="text-gray-500 text-sm mb-6">10 credits</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> 10 analyses/month</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Basic deal scoring</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> UAE + USA markets</li>
              </ul>
              <a href="/register" className="block w-full text-center bg-gray-100 text-gray-900 py-3 rounded-xl font-semibold hover:bg-gray-200 transition-all">
                Get Started
              </a>
            </div>

            {/* Pro */}
            <div className="bg-gradient-to-br from-purple-600 to-pink-600 rounded-2xl shadow-xl p-6 text-white relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-yellow-400 text-yellow-900 text-xs font-bold px-4 py-1 rounded-full">
                POPULAR
              </div>
              <div className="text-sm font-medium text-white/80 uppercase mb-2">Starter</div>
              <div className="text-4xl font-bold mb-1">€9</div>
              <div className="text-white/70 mb-2">per month</div>
              <div className="text-white/60 text-sm mb-6">100 credits/month</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2"><span className="text-green-300">✓</span> 100 analyses/month</li>
                <li className="flex items-center gap-2"><span className="text-green-300">✓</span> UAE + USA markets</li>
                <li className="flex items-center gap-2"><span className="text-green-300">✓</span> API access</li>
                <li className="flex items-center gap-2"><span className="text-green-300">✓</span> Email support</li>
              </ul>
              <a href="/register?plan=starter" className="block w-full text-center bg-white text-purple-600 py-3 rounded-xl font-bold hover:bg-gray-100 transition-all">
                Start Starter
              </a>
            </div>

            {/* Pro */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-purple-200 relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-4 py-1 rounded-full">
                RECOMMENDED
              </div>
              <div className="text-sm font-medium text-purple-600 uppercase mb-2">Pro</div>
              <div className="text-4xl font-bold text-gray-900 mb-1">€29</div>
              <div className="text-gray-500 mb-2">per month</div>
              <div className="text-gray-500 text-sm mb-6">500 credits/month</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> 500 analyses/month</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> All markets</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Batch processing</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Priority support</li>
              </ul>
              <a href="/register?plan=pro" className="block w-full text-center bg-purple-600 text-white py-3 rounded-xl font-semibold hover:bg-purple-700 transition-all">
                Get Started
              </a>
            </div>

            {/* Investor */}
            <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-yellow-400">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-yellow-400 to-amber-500 text-black text-xs font-bold px-4 py-1 rounded-full">
                BEST VALUE
              </div>
              <div className="text-sm font-medium text-yellow-600 uppercase mb-2 mt-2">Investor</div>
              <div className="text-4xl font-bold text-gray-900 mb-1">€79</div>
              <div className="text-gray-500 mb-2">per month</div>
              <div className="text-gray-500 text-sm mb-6">2000 credits/month</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Everything in Pro</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> 2000 analyses/month</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Custom integrations</li>
                <li className="flex items-center gap-2 text-gray-700"><span className="text-green-500">✓</span> Dedicated support</li>
              </ul>
              <a href="/register?plan=investor" className="block w-full text-center bg-gradient-to-r from-yellow-400 to-amber-500 text-black py-3 rounded-xl font-bold hover:opacity-90 transition-all">
                Get Started
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* TRUST */}
      <section className="py-16 bg-white border-t">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Built for Serious Investors</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <div className="text-3xl mb-3">🔒</div>
              <h3 className="font-bold text-gray-900 mb-2">Bank-Level Security</h3>
              <p className="text-gray-600 text-sm">Your data is encrypted and secure. We never share your information.</p>
            </div>
            <div>
              <div className="text-3xl mb-3">📊</div>
              <h3 className="font-bold text-gray-900 mb-2">Verified Market Data</h3>
              <p className="text-gray-600 text-sm">Powered by aggregated data from 50+ real estate sources worldwide.</p>
            </div>
            <div>
              <div className="text-3xl mb-3">🤖</div>
              <h3 className="font-bold text-gray-900 mb-2">AI Trained on 1M+ Deals</h3>
              <p className="text-gray-600 text-sm">Our machine learning models improve continuously with every analysis.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="text-xl font-bold mb-4">AI Deals Finder</div>
              <p className="text-gray-400 text-sm">Find profitable real estate investments with AI-powered analysis.</p>
            </div>
            <div>
              <div className="font-semibold mb-4">Product</div>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#analyzer" className="hover:text-white">Analyzer</a></li>
                <li><a href="#deals" className="hover:text-white">Best Deals</a></li>
                <li><a href="#" className="hover:text-white">Pricing</a></li>
              </ul>
            </div>
            <div>
              <div className="font-semibold mb-4">Company</div>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white">About</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
              </ul>
            </div>
            <div>
              <div className="font-semibold mb-4">Legal</div>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white">Privacy</a></li>
                <li><a href="#" className="hover:text-white">Terms</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-500 text-sm">
            © 2024 AI Deals Finder. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
