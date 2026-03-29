'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { PropertyWithScore } from '@/lib/types';

interface PropertyMapProps {
  properties: PropertyWithScore[];
  center?: [number, number];
  zoom?: number;
  selectedProperty?: PropertyWithScore | null;
  onPropertySelect?: (property: PropertyWithScore) => void;
}

export default function PropertyMap({
  properties,
  center = [25.2048, 55.2708],
  zoom = 11,
  selectedProperty,
  onPropertySelect,
}: PropertyMapProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const markersRef = useRef<L.Marker[]>([]);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    mapRef.current = L.map(mapContainerRef.current).setView(center, zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(mapRef.current);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    properties.forEach((property) => {
      if (!property.latitude || !property.longitude) return;

      const score = property.deal_score ?? 50;
      const scoreColor = score >= 80 ? '#22c55e' :
                        score >= 60 ? '#3b82f6' :
                        score >= 40 ? '#eab308' : '#ef4444';

      const icon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            background-color: ${scoreColor};
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
          ">
            ${score.toFixed(0)}
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([property.latitude, property.longitude], { icon })
        .addTo(mapRef.current!);

      const priceFormatted = property.price >= 1000000
        ? `AED ${(property.price / 1000000).toFixed(1)}M`
        : `AED ${(property.price / 1000).toFixed(0)}K`;

      marker.bindPopup(`
        <div style="min-width: 200px; font-family: sans-serif;">
          <h3 style="font-weight: 600; margin-bottom: 4px; font-size: 14px;">${property.title}</h3>
          <p style="color: #3b82f6; font-weight: 700; font-size: 16px; margin-bottom: 4px;">${priceFormatted}</p>
          <p style="color: #6b7280; font-size: 12px; margin-bottom: 8px;">${property.location || property.district || property.city}</p>
          <div style="display: flex; justify-content: space-between; font-size: 12px;">
            <span>${property.area} sqm</span>
            <span>Score: <strong>${score.toFixed(0)}</strong></span>
          </div>
        </div>
      `, {
        closeButton: false,
        minWidth: 220,
      });

      marker.on('click', () => {
        onPropertySelect?.(property);
      });

      markersRef.current.push(marker);
    });
  }, [properties, onPropertySelect]);

  useEffect(() => {
    if (!mapRef.current || !selectedProperty?.latitude || !selectedProperty?.longitude) return;
    mapRef.current.setView([selectedProperty.latitude, selectedProperty.longitude], 14);
  }, [selectedProperty]);

  return (
    <div className="relative w-full h-full min-h-[400px] rounded-xl overflow-hidden">
      <div ref={mapContainerRef} className="w-full h-full" />
      <div className="absolute bottom-4 left-4 bg-white p-3 rounded-lg shadow-lg z-[1000]">
        <h4 className="text-sm font-semibold mb-2">Deal Score Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-green-500 mr-2"></div>
            <span>80+ Excellent</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-blue-500 mr-2"></div>
            <span>60-79 Good</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-yellow-500 mr-2"></div>
            <span>40-59 Fair</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 rounded-full bg-red-500 mr-2"></div>
            <span>&lt;40 Poor</span>
          </div>
        </div>
      </div>
    </div>
  );
}
