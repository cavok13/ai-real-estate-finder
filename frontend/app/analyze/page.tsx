'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import PropertyCard from '@/components/PropertyCard';
import { useAuthStore } from '@/lib/store';
import { analysisAPI } from '@/lib/api';
import { AnalysisResponse } from '@/lib/types';

const CITIES = ['Dubai', 'Abu Dhabi', 'Sharjah', 'New York', 'London', 'Toronto', 'Berlin', 'Paris', 'Sydney', 'Tokyo'];
const PROPERTY_TYPES = ['apartment', 'villa', 'studio', 'penthouse', 'house', 'condo', 'flat', 'loft'];

type TabType = 'search' | 'url';

interface URLAnalysisResult {
  success: boolean;
  source?: string;
  url?: string;
  price?: number;
  currency?: string;
  currency_symbol?: string;
  area?: number;
  bedrooms?: number;
  bathrooms?: number;
  address?: string;
  city?: string;
  country?: string;
  price_per_m2?: number;
  deal_score?: number;
  market_comparison?: {
    market_avg_price_per_m2?: number;
    your_price_per_m2?: number;
    difference_percent?: number;
    note?: string;
  };
  error?: string;
}

export default function Analyze() {
  const router = useRouter();
  const { user, isAuthenticated, updateCredits } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [urlResult, setUrlResult] = useState<URLAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('search');

  const [formData, setFormData] = useState({
    budget_min: '',
    budget_max: '',
    preferred_city: 'Dubai',
    property_type: '',
    bedrooms_min: '',
  });

  const [urlData, setUrlData] = useState({
    url: '',
  });

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      router.push('/login?redirect=/analyze');
      return;
    }

    if (user!.credits < 1) {
      setError('You need credits to analyze. Please purchase more.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await analysisAPI.create({
        budget_min: formData.budget_min ? parseFloat(formData.budget_min) : undefined,
        budget_max: formData.budget_max ? parseFloat(formData.budget_max) : undefined,
        preferred_city: formData.preferred_city,
        property_type: formData.property_type || undefined,
        bedrooms_min: formData.bedrooms_min ? parseInt(formData.bedrooms_min) : undefined,
      });

      setAnalysis(response.data);
      updateCredits(user!.credits - 1);
    } catch (err: any) {
      if (err.response?.status === 402) {
        setError('Insufficient credits. Please purchase more credits.');
      } else {
        setError('Analysis failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isAuthenticated) {
      router.push('/login?redirect=/analyze');
      return;
    }

    if (user!.credits < 1) {
      setError('You need credits to analyze. Please purchase more.');
      return;
    }

    if (!urlData.url) {
      setError('Please enter a property URL.');
      return;
    }

    setLoading(true);
    setError(null);
    setUrlResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analyze/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ url: urlData.url }),
      });

      if (!response.ok) {
        if (response.status === 402) {
          setError('Insufficient credits. Please purchase more credits.');
          return;
        }
        throw new Error('Analysis failed');
      }

      const result = await response.json();
      setUrlResult(result);
      
      if (result.success) {
        updateCredits(user!.credits - 1);
      }
    } catch (err: any) {
      setError('Failed to analyze URL. Please check the URL and try again.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 60) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (score >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent Deal';
    if (score >= 60) return 'Good Deal';
    if (score >= 40) return 'Fair Deal';
    return 'Overpriced';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <div>
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                AI Property Analysis
              </h1>

              {/* Credits Info */}
              <div className="bg-primary-50 rounded-lg p-4 mb-6">
                <div className="flex justify-between items-center">
                  <span className="text-primary-700 font-medium">Your Credits</span>
                  <span className="text-2xl font-bold text-primary-600">
                    {isAuthenticated ? user?.credits : '0'}
                  </span>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-gray-200 mb-6">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`pb-3 px-4 font-medium text-sm ${
                    activeTab === 'search'
                      ? 'border-b-2 border-primary-500 text-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Search Analysis
                </button>
                <button
                  onClick={() => setActiveTab('url')}
                  className={`pb-3 px-4 font-medium text-sm ${
                    activeTab === 'url'
                      ? 'border-b-2 border-primary-500 text-primary-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  URL Analysis
                </button>
              </div>

              {activeTab === 'search' && (
                <form onSubmit={handleSearchSubmit} className="space-y-5">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Min Budget
                      </label>
                      <input
                        type="number"
                        value={formData.budget_min}
                        onChange={(e) => setFormData({ ...formData, budget_min: e.target.value })}
                        placeholder="100,000"
                        className="input-field"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Budget
                      </label>
                      <input
                        type="number"
                        value={formData.budget_max}
                        onChange={(e) => setFormData({ ...formData, budget_max: e.target.value })}
                        placeholder="5,000,000"
                        className="input-field"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      City
                    </label>
                    <select
                      value={formData.preferred_city}
                      onChange={(e) => setFormData({ ...formData, preferred_city: e.target.value })}
                      className="input-field"
                    >
                      {CITIES.map((city) => (
                        <option key={city} value={city}>{city}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Property Type
                    </label>
                    <select
                      value={formData.property_type}
                      onChange={(e) => setFormData({ ...formData, property_type: e.target.value })}
                      className="input-field"
                    >
                      <option value="">Any Type</option>
                      {PROPERTY_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {type.charAt(0).toUpperCase() + type.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Min Bedrooms
                    </label>
                    <select
                      value={formData.bedrooms_min}
                      onChange={(e) => setFormData({ ...formData, bedrooms_min: e.target.value })}
                      className="input-field"
                    >
                      <option value="">Any</option>
                      {[1, 2, 3, 4, 5].map((num) => (
                        <option key={num} value={num}>{num}+</option>
                      ))}
                    </select>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                      {error}
                      {error.includes('credits') && (
                        <a href="/dashboard" className="underline ml-2">Buy Credits</a>
                      )}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Analyzing...' : 'Find Best Deals'}
                  </button>
                </form>
              )}

              {activeTab === 'url' && (
                <form onSubmit={handleUrlSubmit} className="space-y-5">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Property Listing URL
                    </label>
                    <input
                      type="url"
                      value={urlData.url}
                      onChange={(e) => setUrlData({ url: e.target.value })}
                      placeholder="https://www.zillow.com/..."
                      className="input-field"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Supports: Zillow, Realtor, Rightmove, Redfin, and more
                    </p>
                  </div>

                  <div className="bg-blue-50 rounded-lg p-4">
                    <p className="text-sm text-blue-700">
                      <strong>How it works:</strong> Paste any property listing URL and our AI will:
                    </p>
                    <ul className="text-sm text-blue-600 mt-2 space-y-1">
                      <li>• Extract property details (price, size, location)</li>
                      <li>• Compare against market averages</li>
                      <li>• Score the deal (0-100)</li>
                    </ul>
                  </div>

                  {error && (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                      {error}
                      {error.includes('credits') && (
                        <a href="/dashboard" className="underline ml-2">Buy Credits</a>
                      )}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Scraping & Analyzing...' : 'Analyze URL'}
                  </button>
                </form>
              )}

              {!isAuthenticated && (
                <p className="text-sm text-gray-500 text-center mt-4">
                  <a href="/login" className="text-primary-600 hover:underline">Login</a>
                  {' or '}
                  <a href="/register" className="text-primary-600 hover:underline">Register</a>
                  {' to start analyzing'}
                </p>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div>
            {activeTab === 'search' && analysis && (
              <div className="space-y-6">
                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Analysis Results</h2>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-green-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-green-600">
                        {analysis.deal_score}
                      </div>
                      <div className="text-sm text-green-700">Best Deal Score</div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {analysis.insights.total_properties_found}
                      </div>
                      <div className="text-sm text-blue-700">Properties Found</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Matching Properties</h3>
                  <div className="space-y-4">
                    {analysis.top_properties.map((property) => (
                      <PropertyCard key={property.id} property={property} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'url' && urlResult && (
              <div className="space-y-6">
                {urlResult.success ? (
                  <>
                    <div className="bg-white rounded-xl shadow-lg p-6">
                      <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-bold text-gray-900">URL Analysis Result</h2>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(urlResult.deal_score || 0)}`}>
                          {getScoreLabel(urlResult.deal_score || 0)}
                        </span>
                      </div>

                      <div className={`text-center rounded-xl p-6 mb-6 ${getScoreColor(urlResult.deal_score || 0)}`}>
                        <div className="text-5xl font-bold">{urlResult.deal_score}</div>
                        <div className="text-lg mt-2">Deal Score</div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-6">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500">Price</div>
                          <div className="text-xl font-bold">
                            {urlResult.currency_symbol}{urlResult.price?.toLocaleString()}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500">Area</div>
                          <div className="text-xl font-bold">{urlResult.area} sqft</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500">Bedrooms</div>
                          <div className="text-xl font-bold">{urlResult.bedrooms || 'N/A'}</div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="text-sm text-gray-500">Price/sqft</div>
                          <div className="text-xl font-bold">
                            {urlResult.currency_symbol}{urlResult.price_per_m2?.toFixed(2)}
                          </div>
                        </div>
                      </div>

                      {urlResult.address && (
                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                          <div className="text-sm text-gray-500">Location</div>
                          <div className="font-medium">{urlResult.address}</div>
                          <div className="text-sm text-gray-600">
                            {urlResult.city}, {urlResult.country}
                          </div>
                        </div>
                      )}

                      {urlResult.market_comparison && (
                        <div className="bg-blue-50 rounded-lg p-4">
                          <h3 className="font-semibold text-blue-900 mb-3">Market Comparison</h3>
                          {urlResult.market_comparison.note ? (
                            <p className="text-sm text-blue-700">{urlResult.market_comparison.note}</p>
                          ) : (
                            <div className="space-y-2">
                              <div className="flex justify-between">
                                <span className="text-sm text-blue-700">Market Avg:</span>
                                <span className="font-medium">{urlResult.currency_symbol}{urlResult.market_comparison.market_avg_price_per_m2?.toFixed(2)}/sqft</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-sm text-blue-700">This Property:</span>
                                <span className="font-medium">{urlResult.currency_symbol}{urlResult.market_comparison.your_price_per_m2?.toFixed(2)}/sqft</span>
                              </div>
                              <div className="flex justify-between border-t pt-2">
                                <span className="text-sm text-blue-700">Difference:</span>
                                <span className={`font-bold ${(urlResult.market_comparison.difference_percent || 0) > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {(urlResult.market_comparison.difference_percent || 0) > 0 ? '+' : ''}{urlResult.market_comparison.difference_percent}%
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      <div className="mt-4 text-sm text-gray-500">
                        Source: <span className="font-medium capitalize">{urlResult.source}</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white rounded-xl shadow-lg p-6">
                    <div className="text-center">
                      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 mb-2">Analysis Failed</h3>
                      <p className="text-gray-600">{urlResult.error}</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {(!analysis && activeTab === 'search') && (
              <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Ready for AI Analysis
                </h3>
                <p className="text-gray-600">
                  {activeTab === 'search' 
                    ? 'Fill in your requirements and click analyze to find the best property deals.'
                    : 'Paste a property listing URL to analyze the deal instantly.'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
