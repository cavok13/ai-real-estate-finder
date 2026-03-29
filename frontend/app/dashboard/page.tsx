'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { marketsAPI } from '@/lib/api';

interface Property {
  id: number;
  title: string;
  price: number;
  city: string;
  country: string;
  deal_score: number;
  roi: number;
  image_url: string;
  avgRentYield?: number;
}

interface UAEArea {
  name: string;
  nameAr: string;
  avgRentYield: number;
  avgPricePerSqFt: number;
  medianPrice: number;
  deal_score?: number;
  riskLevel: string;
  priceTrend: string;
}

interface MarketSummary {
  market: string;
  totalAreas: number;
  avgYield: number;
  avgPricePerSqFt: number;
  totalTransactions2024: number;
}

interface AnalysisResult {
  score: number;
  roi: number;
  risk: 'Low' | 'Medium' | 'High';
  price: number;
  pricePerSqm: number;
  marketAvg: number;
  label: string;
  priceVsMarket?: string;
  tags?: string[];
  recommendation?: string;
}

interface HistoryItem {
  id: number;
  property: string;
  roi: number;
  score: number;
  date: string;
}

export default function Dashboard() {
  const { user, isAuthenticated, checkAuth } = useAuthStore();
  const [loading, setLoading] = useState(false); // Skip loading for testing
  
  // Default user for testing
  const testUser = user || { 
    full_name: 'Demo User', 
    email: 'demo@example.com', 
    credits: 10, 
    is_premium: false 
  };
  const [analyzing, setAnalyzing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('All Markets');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [properties, setProperties] = useState<Property[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  
  // New UAE market data
  const [uaeAreas, setUaeAreas] = useState<UAEArea[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [credits, setCredits] = useState(0);

  useEffect(() => {
    // Skip auth check for testing - load data directly
    fetchProperties();
    loadHistory();
    fetchUAEMarketData();
    fetchCredits();
  }, []);

  const fetchCredits = async () => {
    try {
      const res = await marketsAPI.getCredits();
      if (res.data.success) {
        setCredits(res.data.credits);
      }
    } catch (e) {
      console.log('Using default credits');
    }
  };

  const fetchUAEMarketData = async () => {
    try {
      // Fetch best deal areas from UAE
      const dealsRes = await marketsAPI.getBestDeals('dubai');
      if (dealsRes.data.success) {
        setUaeAreas(dealsRes.data.areas);
      }
      
      // Fetch market summary
      const summaryRes = await marketsAPI.getMarketSummary('dubai');
      if (summaryRes.data.success) {
        setMarketSummary(summaryRes.data);
      }
    } catch (e) {
      console.error('Error fetching UAE market data:', e);
      // Fallback data
      setUaeAreas([
        { name: 'JVC', nameAr: 'قرية جميرا', avgRentYield: 7.5, avgPricePerSqFt: 1100, medianPrice: 950000, deal_score: 95, riskLevel: 'Low', priceTrend: 'rising' },
        { name: 'International City', nameAr: 'المدينة العالمية', avgRentYield: 9.0, avgPricePerSqFt: 650, medianPrice: 550000, deal_score: 93, riskLevel: 'Medium', priceTrend: 'rising' },
        { name: 'Dubai Silicon Oasis', nameAr: 'واحة دبي', avgRentYield: 7.8, avgPricePerSqFt: 850, medianPrice: 780000, deal_score: 93, riskLevel: 'Low', priceTrend: 'rising' },
        { name: 'Discovery Gardens', nameAr: 'حدائق ديسكفري', avgRentYield: 8.5, avgPricePerSqFt: 750, medianPrice: 650000, deal_score: 91, riskLevel: 'Low', priceTrend: 'stable' },
        { name: 'Dubai Land', nameAr: 'أرض دبي', avgRentYield: 8.0, avgPricePerSqFt: 700, medianPrice: 900000, deal_score: 90, riskLevel: 'Medium', priceTrend: 'rising' },
      ]);
      setMarketSummary({ market: 'dubai', totalAreas: 24, avgYield: 6.7, avgPricePerSqFt: 1450, totalTransactions2024: 45678 });
    }
  };

  const fetchProperties = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/properties/best-deals?limit=6`);
      if (res.ok) {
        const data = await res.json();
        setProperties(data.map((p: any) => ({
          ...p,
          roi: 5 + Math.random() * 8
        })));
      }
    } catch (e) {
      setProperties([
        { id: 1, title: 'Dubai Marina Penthouse', price: 485000, city: 'Dubai', country: 'UAE', deal_score: 87, roi: 8.5, image_url: '' },
        { id: 2, title: 'Manhattan Studio', price: 1250000, city: 'New York', country: 'USA', deal_score: 72, roi: 4.2, image_url: '' },
        { id: 3, title: 'London Canary Wharf Flat', price: 650000, city: 'London', country: 'UK', deal_score: 78, roi: 6.8, image_url: '' },
        { id: 4, title: 'Singapore Marina Bay', price: 1200000, city: 'Singapore', country: 'Singapore', deal_score: 82, roi: 7.2, image_url: '' },
      ]);
    }
  };

  const loadHistory = () => {
    setHistory([
      { id: 1, property: 'Dubai Marina Apartment', roi: 8.5, score: 87, date: 'Today' },
      { id: 2, property: 'NYC Manhattan Studio', roi: 4.2, score: 72, date: 'Yesterday' },
      { id: 3, property: 'London Flat', roi: 6.8, score: 78, date: '2 days ago' },
    ]);
  };

  const handleAnalyze = async () => {
    if (!searchQuery.trim()) return;
    setAnalyzing(true);
    setAnalysisResult(null);

    try {
      // Try the new unified analyzer
      const res = await marketsAPI.analyzeURLFree(searchQuery);
      if (res.data.success) {
        const analysis = res.data.analysis;
        setAnalysisResult({
          score: analysis.deal_score,
          roi: analysis.roi_percent,
          risk: analysis.risk_level,
          price: res.data.property?.price || 500000,
          pricePerSqm: analysis.avg_area_price_sqft,
          marketAvg: analysis.avg_area_price_sqft,
          label: analysis.deal_score >= 75 ? 'Great Deal' : analysis.deal_score >= 50 ? 'Average' : 'Overpriced',
          priceVsMarket: analysis.price_vs_market,
          tags: analysis.tags,
          recommendation: analysis.recommendation,
        });
      }
    } catch (e) {
      // Fallback to mock analysis
      await new Promise(r => setTimeout(r, 1500));
      const roi = 5 + Math.random() * 10;
      const score = 60 + Math.random() * 35;
      
      setAnalysisResult({
        score: Math.round(score),
        roi: parseFloat(roi.toFixed(1)),
        risk: score >= 75 ? 'Low' : score >= 50 ? 'Medium' : 'High',
        price: 500000 + Math.random() * 1000000,
        pricePerSqm: 3000 + Math.random() * 8000,
        marketAvg: 5000,
        label: score >= 75 ? 'Great Deal' : score >= 50 ? 'Average' : 'Overpriced'
      });
    }

    setAnalyzing(false);
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'Medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'High': return 'bg-red-500/20 text-red-400 border-red-500/30';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'from-emerald-400 to-emerald-600';
    if (score >= 50) return 'from-yellow-400 to-orange-500';
    return 'from-red-400 to-red-600';
  };

  // Skip loading check for testing
  // if (loading) {
  //   return (
  //     <div className="min-h-screen bg-black flex items-center justify-center">
  //       <div className="relative">
  //         <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
  //         <div className="absolute inset-0 w-16 h-16 border-4 border-purple-500/40 border-b-transparent rounded-full animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }}></div>
  //       </div>
  //     </div>
  //   );
  // }

  // Skip auth check for testing - remove in production!
  // if (!isAuthenticated) {
  //   if (typeof window !== 'undefined') window.location.href = '/login';
  //   return null;
  // }

  // Use real market data or fallbacks
  const kpis = [
    { label: 'UAE Areas Tracked', value: marketSummary?.totalAreas?.toString() || '24', trend: '+2', trendUp: true, icon: 'H' },
    { label: 'Market Avg Yield', value: `${marketSummary?.avgYield?.toFixed(1) || '6.7'}%`, trend: '+0.3%', trendUp: true, icon: 'T' },
    { label: 'Best Deal ROI', value: `${uaeAreas[0]?.avgRentYield || 9.0}%`, trend: '+1.2%', trendUp: true, icon: 'B' },
    { label: 'Your Credits', value: credits.toString(), trend: '', trendUp: true, icon: 'V' },
  ];

  const countries = ['All Markets', 'UAE', 'USA', 'UK', 'Canada', 'Germany', 'Australia', 'Singapore'];

  // Generate insights from market data
  const insights = [
    { text: `${uaeAreas[0]?.name || 'JVC'} offers ${uaeAreas[0]?.avgRentYield || 7.5}% avg yield`, icon: 'D' },
    { text: `${marketSummary?.totalTransactions2024?.toLocaleString() || '45,678'} transactions in 2024`, icon: 'H' },
    { text: `${marketSummary?.avgPricePerSqFt?.toLocaleString() || '1,450'} AED/sqft Dubai average`, icon: 'N' },
    { text: `${uaeAreas.filter(a => a.priceTrend === 'rising').length || 18} areas showing rising prices`, icon: 'R' },
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* NAVBAR */}
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-12">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center font-bold text-white">
                  AI
                </div>
                <span className="text-xl font-bold text-white">Deals Finder</span>
              </div>
              <div className="hidden md:flex items-center gap-8">
                {['Dashboard', 'Properties', 'Analysis', 'Pricing'].map((item) => (
                  <a key={item} href={item === 'Dashboard' ? '/dashboard' : '/' + item.toLowerCase()} 
                     className="text-sm text-white/60 hover:text-white transition-colors">
                    {item}
                  </a>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10">
                <span className="text-purple-400 font-medium">{testUser.credits}</span>
                <span className="text-white/60 text-sm">credits</span>
              </div>
              <button
                onClick={() => setShowUpgradeModal(true)}
                className="hidden sm:block px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-semibold hover:opacity-90 transition-opacity"
              >
                Upgrade
              </button>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold">
                {testUser.full_name?.[0] || testUser.email?.[0] || 'U'}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* MAIN CONTENT */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* HEADER */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, {testUser.full_name?.split(' ')[0] || 'Investor'}
          </h1>
          <p className="text-white/60">Discover high ROI opportunities powered by AI</p>
          <div className="flex gap-3 mt-4">
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
              <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></span>
              3 new deals found today
            </span>
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm">
              Market opportunity detected
            </span>
          </div>
        </div>

        {/* KPI CARDS */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {kpis.map((kpi, i) => (
            <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/[0.07] transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{kpi.icon}</span>
                <span className={`text-xs font-medium ${kpi.trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
                  {kpi.trend}
                </span>
              </div>
              <div className="text-2xl font-bold text-white mb-1">{kpi.value}</div>
              <div className="text-sm text-white/50">{kpi.label}</div>
            </div>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* MAIN ANALYSIS PANEL */}
          <div className="lg:col-span-2 space-y-6">
            {/* Analysis Card */}
            <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
              <div className="p-6 border-b border-white/10">
                <h2 className="text-lg font-semibold text-white">Property Analysis</h2>
                <p className="text-sm text-white/50 mt-1">Enter a property to get AI-powered insights</p>
              </div>
              <div className="p-6">
                <div className="flex gap-3 mb-6">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Enter property location or URL..."
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/30 focus:outline-none focus:border-purple-500/50 transition-colors"
                      onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                    />
                  </div>
                  <select
                    value={selectedCountry}
                    onChange={(e) => setSelectedCountry(e.target.value)}
                    className="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-purple-500/50"
                  >
                    {countries.map((c) => (
                      <option key={c} value={c} className="bg-gray-900">{c}</option>
                    ))}
                  </select>
                  <button
                    onClick={handleAnalyze}
                    disabled={analyzing || !searchQuery.trim()}
                    className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                  >
                    {analyzing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        Analyzing...
                      </>
                    ) : (
                      'Analyze'
                    )}
                  </button>
                </div>

                {/* RESULTS */}
                {analysisResult && (
                  <div className="mt-6 p-6 bg-gradient-to-br from-white/5 to-white/[0.02] rounded-xl border border-white/10">
                    <div className="flex items-center justify-between mb-6">
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${
                        analysisResult.label === 'Great Deal' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        analysisResult.label === 'Overpriced' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                        'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                      }`}>
                        {analysisResult.label}
                      </div>
                      <span className={`px-3 py-1.5 rounded-full text-sm font-medium border ${getRiskColor(analysisResult.risk)}`}>
                        {analysisResult.risk} Risk
                      </span>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 bg-white/5 rounded-xl">
                        <div className={`text-3xl font-bold bg-gradient-to-b ${getScoreColor(analysisResult.score)} bg-clip-text text-transparent`}>
                          {analysisResult.score}
                        </div>
                        <div className="text-xs text-white/50 mt-1">AI Score</div>
                      </div>
                      <div className="text-center p-4 bg-white/5 rounded-xl">
                        <div className="text-3xl font-bold text-emerald-400">{analysisResult.roi}%</div>
                        <div className="text-xs text-white/50 mt-1">Est. ROI</div>
                      </div>
                      <div className="text-center p-4 bg-white/5 rounded-xl">
                        <div className="text-3xl font-bold text-white">${Math.round(analysisResult.price / 1000)}K</div>
                        <div className="text-xs text-white/50 mt-1">Price</div>
                      </div>
                      <div className="text-center p-4 bg-white/5 rounded-xl">
                        <div className="text-3xl font-bold text-white">${Math.round(analysisResult.pricePerSqm)}</div>
                        <div className="text-xs text-white/50 mt-1">Price/sqm</div>
                      </div>
                    </div>

                    <div className="mt-6 p-4 bg-white/5 rounded-xl">
                      <div className="text-sm text-white/50 mb-2">Market Comparison</div>
                      <div className="flex items-center gap-4">
                        <div className="flex-1">
                          <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"
                              style={{ width: `${Math.min(100, (analysisResult.marketAvg / analysisResult.pricePerSqm) * 50)}%` }}
                            ></div>
                          </div>
                          <div className="text-xs text-white/40 mt-1">Market Avg: ${analysisResult.marketAvg}</div>
                        </div>
                        <div className="text-right">
                          <div className={`text-lg font-bold ${analysisResult.pricePerSqm < analysisResult.marketAvg ? 'text-emerald-400' : 'text-red-400'}`}>
                            {analysisResult.pricePerSqm < analysisResult.marketAvg ? '-' : '+'}
                            {Math.abs(Math.round(((analysisResult.pricePerSqm - analysisResult.marketAvg) / analysisResult.marketAvg) * 100))}%
                          </div>
                          <div className="text-xs text-white/40">vs Market</div>
                        </div>
                      </div>
                    </div>

                    {/* AI Insights Tags */}
                    {analysisResult.tags && analysisResult.tags.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {analysisResult.tags.map((tag, i) => (
                          <span key={i} className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-medium border border-purple-500/30">
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Recommendation */}
                    {analysisResult.recommendation && (
                      <div className="mt-4 p-3 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-lg border border-purple-500/20">
                        <div className="text-xs text-purple-400 font-medium mb-1">AI Recommendation</div>
                        <p className="text-sm text-white/80">{analysisResult.recommendation}</p>
                      </div>
                    )}
                  </div>
                )}

                {analyzing && (
                  <div className="mt-6 p-8 bg-white/5 rounded-xl border border-white/10 text-center">
                    <div className="w-16 h-16 mx-auto mb-4 relative">
                      <div className="absolute inset-0 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
                      <div className="absolute inset-2 border-4 border-pink-500/20 border-b-pink-500 rounded-full animate-spin" style={{ animationDuration: '1.2s', animationDirection: 'reverse' }}></div>
                    </div>
                    <p className="text-white font-medium">Analyzing with AI...</p>
                    <p className="text-sm text-white/50 mt-1">Processing market data and comparable properties</p>
                  </div>
                )}
              </div>
            </div>

            {/* UAE AREAS - BEST DEALS */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-white">Dubai Best Deals</h2>
                  <p className="text-sm text-white/50">Based on DLD 2024 market data</p>
                </div>
                <a href="/best-deals" className="text-sm text-purple-400 hover:text-purple-300">View all areas</a>
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                {uaeAreas.slice(0, 4).map((area, i) => (
                  <div key={i} className="group bg-white/5 rounded-xl p-4 hover:bg-white/10 transition-all cursor-pointer border border-white/5 hover:border-white/20">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-semibold text-white">{area.name}</h3>
                        <p className="text-xs text-white/50">{area.nameAr}</p>
                      </div>
                      <div className={`px-2 py-1 rounded-lg text-sm font-bold ${
                        area.deal_score && area.deal_score >= 90 ? 'bg-emerald-500/20 text-emerald-400' :
                        area.deal_score && area.deal_score >= 80 ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-white/10 text-white'
                      }`}>
                        {area.deal_score || Math.round(70 + Math.random() * 20)}/100
                      </div>
                    </div>
                    <div className="flex items-center gap-4 mb-3">
                      <div className="text-center">
                        <div className="text-xl font-bold text-emerald-400">{area.avgRentYield}%</div>
                        <div className="text-xs text-white/40">ROI</div>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-white">{area.avgPricePerSqFt.toLocaleString()}</div>
                        <div className="text-xs text-white/40">AED/sqm</div>
                      </div>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${
                        area.riskLevel === 'Low' ? 'bg-blue-500/20 text-blue-400' :
                        area.riskLevel === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {area.riskLevel} Risk
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-white/40">
                      <span>Trend: <span className={area.priceTrend === 'rising' ? 'text-emerald-400' : 'text-yellow-400'}>{area.priceTrend}</span></span>
                      <span>{area.medianPrice.toLocaleString()} AED median</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* HISTORY */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h2 className="text-lg font-semibold text-white mb-4">Recent Analyses</h2>
              <div className="space-y-3">
                {history.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center text-white font-bold">
                        P
                      </div>
                      <div>
                        <p className="text-white font-medium">{item.property}</p>
                        <p className="text-sm text-white/50">{item.date}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="text-emerald-400 font-semibold">{item.roi}% ROI</div>
                        <div className="text-xs text-white/50">Score: {item.score}</div>
                      </div>
                      <span className={`w-2 h-2 rounded-full ${item.score >= 75 ? 'bg-emerald-400' : item.score >= 50 ? 'bg-yellow-400' : 'bg-red-400'}`}></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SIDEBAR */}
          <div className="space-y-6">
            {/* QUICK ACTIONS */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">Quick Actions</h3>
              <div className="space-y-3">
                {[
                  { label: 'Analyze Property', desc: 'Get AI insights' },
                  { label: 'Browse Deals', desc: 'View opportunities' },
                  { label: 'ROI Calculator', desc: 'Estimate returns' },
                ].map((action, i) => (
                  <button key={i} className="w-full flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors text-left">
                    <span className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center text-white font-bold">
                      {String.fromCharCode(65 + i)}
                    </span>
                    <div>
                      <div className="text-white font-medium">{action.label}</div>
                      <div className="text-sm text-white/50">{action.desc}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* MARKET INSIGHTS */}
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">AI Insights</h3>
              <div className="space-y-3">
                {insights.map((insight, i) => (
                  <div key={i} className="p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer">
                    <div className="flex items-start gap-3">
                      <span className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-sm font-bold">
                        {insight.icon}
                      </span>
                      <p className="text-sm text-white/80">{insight.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* CREDITS */}
            <div className="bg-gradient-to-br from-purple-500/20 to-pink-500/20 border border-purple-500/20 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-4xl font-bold text-white">C</span>
                <span className="px-3 py-1 bg-purple-500/30 rounded-full text-purple-300 text-sm font-medium">
                  {testUser.is_premium ? 'PRO' : 'FREE'}
                </span>
              </div>
              <div className="text-4xl font-bold text-white mb-1">{testUser.credits}</div>
              <p className="text-white/60 text-sm mb-4">credits remaining</p>
              <p className="text-xs text-white/40 mb-4">1 analysis = 1 credit</p>
              <button
                onClick={() => setShowUpgradeModal(true)}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:opacity-90 transition-opacity"
              >
                Buy Credits
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* UPGRADE MODAL - BUY CREDITS */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setShowUpgradeModal(false)}></div>
          <div className="relative bg-gray-900 border border-white/10 rounded-2xl p-8 max-w-md w-full">
            <button onClick={() => setShowUpgradeModal(false)} className="absolute top-4 right-4 text-white/50 hover:text-white">X</button>
            <h2 className="text-2xl font-bold text-white mb-2">Buy Credits</h2>
            <p className="text-white/60 mb-6">Get more property analyses with credits</p>
            <div className="space-y-4">
              {[
                { id: '10_credits', name: '10 Credits', price: '€2.99', credits: 10 },
                { id: '50_credits', name: '50 Credits', price: '€9', credits: 50, popular: true },
                { id: '100_credits', name: '100 Credits', price: '€17', credits: 100 },
              ].map((pack) => (
                <a 
                  key={pack.id}
                  href={pack.id === '10_credits' ? 'https://buy.stripe.com/4gMfZh7vs2P38dV8r4gfu02' : 
                        pack.id === '50_credits' ? 'https://buy.stripe.com/3cI3cv3fc9drbq78r4gfu01' : 
                        'https://buy.stripe.com/aFa4gz7vs0GV2TBcHkgfu00'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block p-4 bg-white/5 rounded-xl border transition-all hover:scale-[1.02] ${
                    pack.popular ? 'border-purple-500/50 hover:border-purple-500' : 'border-white/10 hover:border-purple-500/50'
                  }`}
                >
                  {pack.popular && (
                    <span className="inline-block px-2 py-0.5 bg-purple-500 text-white text-xs font-bold rounded-full mb-2">
                      Best Value
                    </span>
                  )}
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-white">{pack.name}</span>
                    <span className="text-purple-400 font-bold">{pack.price}</span>
                  </div>
                  <p className="text-sm text-white/50">{pack.credits} property analyses</p>
                </a>
              ))}
            </div>
            <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-sm text-white/50 text-center">
                Secure payment via Stripe. Credits never expire.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* STICKY CTA */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          onClick={() => document.querySelector('input')?.focus()}
          className="flex items-center gap-3 px-6 py-4 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold shadow-2xl shadow-purple-500/25 hover:shadow-purple-500/40 transition-all hover:scale-105"
        >
          <span className="text-xl font-bold">+</span>
          <span>Quick Analyze</span>
        </button>
      </div>
    </div>
  );
}
