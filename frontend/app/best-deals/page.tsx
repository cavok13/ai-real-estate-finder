'use client';

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import PropertyCard from '@/components/PropertyCard';
import { propertiesAPI } from '@/lib/api';
import { PropertyWithScore } from '@/lib/types';

const COUNTRIES = [
  { code: 'USA', name: 'United States', flag: '🇺🇸' },
  { code: 'UK', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'Canada', name: 'Canada', flag: '🇨🇦' },
  { code: 'Germany', name: 'Germany', flag: '🇩🇪' },
  { code: 'France', name: 'France', flag: '🇫🇷' },
  { code: 'Spain', name: 'Spain', flag: '🇪🇸' },
  { code: 'Netherlands', name: 'Netherlands', flag: '🇳🇱' },
  { code: 'Japan', name: 'Japan', flag: '🇯🇵' },
  { code: 'Singapore', name: 'Singapore', flag: '🇸🇬' },
  { code: 'China', name: 'Hong Kong', flag: '🇭🇰' },
  { code: 'South Korea', name: 'South Korea', flag: '🇰🇷' },
  { code: 'India', name: 'India', flag: '🇮🇳' },
  { code: 'Thailand', name: 'Thailand', flag: '🇹🇭' },
  { code: 'UAE', name: 'UAE', flag: '🇦🇪' },
  { code: 'South Africa', name: 'South Africa', flag: '🇿🇦' },
  { code: 'Kenya', name: 'Kenya', flag: '🇰🇪' },
  { code: 'Nigeria', name: 'Nigeria', flag: '🇳🇬' },
  { code: 'Morocco', name: 'Morocco', flag: '🇲🇦' },
  { code: 'Egypt', name: 'Egypt', flag: '🇪🇬' },
  { code: 'Australia', name: 'Australia', flag: '🇦🇺' },
];

export default function BestDeals() {
  const [deals, setDeals] = useState<PropertyWithScore[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState<string>('');
  const [selectedRegion, setSelectedRegion] = useState<string>('');

  useEffect(() => {
    loadDeals();
  }, [selectedCountry, selectedRegion]);

  const loadDeals = async () => {
    setLoading(true);
    try {
      const response = await propertiesAPI.getBestDeals(
        selectedCountry || undefined,
        50
      );
      setDeals(response.data);
    } catch (error) {
      console.error('Failed to load deals:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <section className="bg-white border-b py-8">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🌍 Best Real Estate Deals - Worldwide
          </h1>
          <p className="text-gray-600">
            AI-analyzed properties from 20+ countries. Find undervalued investments globally.
          </p>
        </div>
      </section>

      <section className="bg-white border-b py-4">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => { setSelectedCountry(''); setSelectedRegion(''); }}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                !selectedCountry && !selectedRegion
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🌍 All Countries
            </button>
            <button
              onClick={() => setSelectedRegion('North America')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedRegion === 'North America'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🌎 North America
            </button>
            <button
              onClick={() => setSelectedRegion('Europe')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedRegion === 'Europe'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🇪🇺 Europe
            </button>
            <button
              onClick={() => setSelectedRegion('Asia')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedRegion === 'Asia'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🌏 Asia
            </button>
            <button
              onClick={() => setSelectedRegion('Africa')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedRegion === 'Africa'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🌍 Africa
            </button>
          </div>
        </div>
      </section>

      <section className="py-8">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {loading ? 'Loading...' : `${deals.length} properties found`}
            </h2>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[1,2,3,4,5,6,7,8].map(i => (
                <div key={i} className="bg-gray-200 animate-pulse h-72 rounded-xl"></div>
              ))}
            </div>
          ) : deals.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No deals found. Try a different filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {deals.map((deal) => (
                <PropertyCard key={deal.id} property={deal} />
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="bg-primary-50 py-10">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-2xl font-bold mb-4">💡 How Deal Scoring Works</h2>
          <p className="text-gray-600 mb-6">
            Our AI compares each property's price per sqm against the local market average.
            Properties significantly below average get higher scores.
          </p>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-white p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-600">80-100</div>
              <div className="text-sm text-gray-600">Excellent Deal</div>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">60-79</div>
              <div className="text-sm text-gray-600">Good Deal</div>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">40-59</div>
              <div className="text-sm text-gray-600">Fair Price</div>
            </div>
            <div className="bg-white p-4 rounded-lg">
              <div className="text-2xl font-bold text-red-600">0-39</div>
              <div className="text-sm text-gray-600">Above Market</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
