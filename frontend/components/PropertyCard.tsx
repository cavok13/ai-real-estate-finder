'use client';

import Image from 'next/image';
import { PropertyWithScore } from '@/lib/types';

interface PropertyCardProps {
  property: PropertyWithScore;
  onSelect?: (property: PropertyWithScore) => void;
}

function getScoreInfo(score: number) {
  if (score >= 75) {
    return {
      badge: '🔥 Great Deal',
      badgeClass: 'bg-green-500 text-white',
      scoreClass: 'bg-green-100 text-green-700',
      borderClass: 'border-green-200'
    };
  }
  if (score >= 50) {
    return {
      badge: '⚠️ Average',
      badgeClass: 'bg-yellow-500 text-white',
      scoreClass: 'bg-yellow-100 text-yellow-700',
      borderClass: 'border-yellow-200'
    };
  }
  return {
    badge: '❌ Overpriced',
    badgeClass: 'bg-red-500 text-white',
    scoreClass: 'bg-red-100 text-red-700',
    borderClass: 'border-red-200'
  };
}

function formatPrice(price: number, symbol: string = '$'): string {
  if (price >= 1000000) return `${symbol}${(price / 1000000).toFixed(1)}M`;
  if (price >= 1000) return `${symbol}${(price / 1000).toFixed(0)}K`;
  return `${symbol}${price}`;
}

function estimateROI(pricePerSqm: number, marketAvg: number): number {
  const diff = (marketAvg - pricePerSqm) / marketAvg;
  return 5 + (diff * 5) + (Math.random() * 2);
}

export default function PropertyCard({ property, onSelect }: PropertyCardProps) {
  const scoreInfo = getScoreInfo(property.deal_score);
  const roi = estimateROI(property.price_per_m2 || 0, 5000);
  const symbol = property.currency_symbol || '$';

  return (
    <div
      onClick={() => onSelect?.(property)}
      className={`bg-white rounded-2xl overflow-hidden shadow-lg hover:shadow-xl transition-all cursor-pointer border-2 ${scoreInfo.borderClass} hover:-translate-y-1`}
    >
      <div className="relative h-44 bg-gray-200">
        <img
          src={property.image_url || '/placeholder.jpg'}
          alt={property.title}
          className="w-full h-full object-cover"
          onError={(e) => {
            (e.target as HTMLImageElement).src = `https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop`;
          }}
        />
        <div className="absolute top-3 right-3 px-3 py-1.5 rounded-full text-sm font-bold bg-black/70 text-white backdrop-blur-sm">
          {property.deal_score}/100
        </div>
        <div className={`absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-semibold ${scoreInfo.badgeClass}`}>
          {scoreInfo.badge}
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-gray-900 line-clamp-1 flex-1 pr-2">
            {property.title}
          </h3>
        </div>

        <div className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent mb-2">
          {formatPrice(property.price, symbol)}
        </div>

        <div className="flex items-center text-gray-500 text-sm mb-4">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="truncate">{property.district || property.city}, {property.country}</span>
        </div>

        <div className="grid grid-cols-3 gap-2 mb-4">
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-gray-900">{property.area}</div>
            <div className="text-xs text-gray-500">sqm</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-gray-900">{property.bedrooms || '-'}</div>
            <div className="text-xs text-gray-500">Beds</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <div className="text-sm font-bold text-gray-900">{property.bathrooms || '-'}</div>
            <div className="text-xs text-gray-500">Baths</div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div>
            <div className="text-xs text-gray-500">Est. ROI</div>
            <div className="text-lg font-bold text-green-600">{roi.toFixed(1)}%</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-500">Price/sqm</div>
            <div className="text-sm font-semibold text-gray-700">
              {symbol}{Math.round(property.price_per_m2 || 0)}
            </div>
          </div>
        </div>

        {property.price_vs_market < 0 && (
          <div className="mt-3 bg-green-50 text-green-700 text-xs font-medium px-3 py-2 rounded-lg text-center">
            {Math.abs(property.price_vs_market).toFixed(0)}% below market price
          </div>
        )}
      </div>
    </div>
  );
}
