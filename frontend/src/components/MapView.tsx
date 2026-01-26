'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import Map, { Marker, Popup, NavigationControl, MapRef } from 'react-map-gl/mapbox';
import { MapPin, ExternalLink, Zap, Info } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';

// @ts-ignore - mapbox-gl might be missing types or causing issues in some environments
import mapboxgl from 'mapbox-gl';

interface Building {
  building_id: string;
  address: string;
  city: string;
  lat: number | null;
  lng: number | null;
  building_type: string;
  estimated_roof_area: number;
  solar_capacity_kw: number;
  score: number;
  business_name?: string | null;
  solar_max_panels?: number | null;
}

interface MapViewProps {
  buildings: Building[];
  selectedBuildingId?: string | null;
  onSelectBuilding?: (id: string) => void;
}

// In a real app, this would be an environment variable
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN || '';

export default function MapView({ buildings, selectedBuildingId, onSelectBuilding }: MapViewProps) {
  const mapRef = useRef<MapRef>(null);
  const [popupInfo, setPopupInfo] = useState<Building | null>(null);
  const [viewState, setViewState] = useState({
    latitude: 43.1566,
    longitude: -77.6088,
    zoom: 11
  });

  const geocodedBuildings = buildings.filter(b => b.lat && b.lng);
  
  // Update view when selection changes
  useEffect(() => {
    if (selectedBuildingId) {
      const selected = geocodedBuildings.find(b => b.building_id === selectedBuildingId);
      if (selected && selected.lat && selected.lng) {
        mapRef.current?.flyTo({
          center: [selected.lng, selected.lat],
          zoom: 15,
          duration: 2000
        });
        setPopupInfo(selected);
      }
    }
  }, [selectedBuildingId, geocodedBuildings]);

  // Center map on data initially
  useEffect(() => {
    if (geocodedBuildings.length > 0 && !selectedBuildingId) {
      const avgLat = geocodedBuildings.reduce((sum, b) => sum + (b.lat || 0), 0) / geocodedBuildings.length;
      const avgLng = geocodedBuildings.reduce((sum, b) => sum + (b.lng || 0), 0) / geocodedBuildings.length;
      setViewState(prev => ({
        ...prev,
        latitude: avgLat,
        longitude: avgLng,
        zoom: 10
      }));
    }
  }, [geocodedBuildings.length, selectedBuildingId]);

  return (
    <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white text-lg font-semibold flex items-center gap-2">
          <MapPin className="w-5 h-5 text-emerald-500" />
          Interactive Lead Map
        </h3>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-sm">
            {geocodedBuildings.length} of {buildings.length} geocoded
          </span>
        </div>
      </div>

      <div className="relative h-[500px] w-full rounded-lg overflow-hidden border border-slate-700/50">
        <Map
          {...viewState}
          ref={mapRef}
          onMove={(evt: any) => setViewState(evt.viewState)}
          mapStyle="mapbox://styles/mapbox/dark-v11"
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
        >
          <NavigationControl position="top-right" />

          {geocodedBuildings.map(building => (
            <Marker
              key={building.building_id}
              latitude={building.lat!}
              longitude={building.lng!}
              anchor="bottom"
              onClick={(e: any) => {
                e.originalEvent.stopPropagation();
                setPopupInfo(building);
                if (onSelectBuilding) onSelectBuilding(building.building_id);
              }}
            >
              <div className={`cursor-pointer transition-transform hover:scale-110 ${
                selectedBuildingId === building.building_id ? 'scale-125 z-10' : ''
              }`}>
                <div className={`p-1.5 rounded-full border-2 ${
                  building.score >= 70 
                    ? 'bg-emerald-500 border-emerald-300' 
                    : building.score >= 50
                    ? 'bg-yellow-500 border-yellow-300'
                    : 'bg-slate-500 border-slate-300'
                } shadow-lg shadow-black/50`}>
                  <Zap className="w-3 h-3 text-white" />
                </div>
              </div>
            </Marker>
          ))}

          {popupInfo && (
            <Popup
              anchor="top"
              longitude={popupInfo.lng!}
              latitude={popupInfo.lat!}
              onClose={() => setPopupInfo(null)}
              closeButton={false}
              className="z-50"
            >
              <div className="p-3 min-w-[200px] bg-slate-900 text-white rounded-lg border border-slate-700 shadow-2xl">
                <div className="font-bold text-sm mb-1">{popupInfo.business_name || 'Commercial Building'}</div>
                <div className="text-slate-400 text-xs mb-2 flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {popupInfo.address.split(',')[0]}
                </div>
                
                <div className="grid grid-cols-2 gap-2 mb-3">
                  <div className="bg-slate-800 p-2 rounded">
                    <div className="text-[10px] text-slate-500 uppercase">Score</div>
                    <div className={`text-sm font-bold ${
                      popupInfo.score >= 70 ? 'text-emerald-400' : 'text-yellow-400'
                    }`}>
                      {popupInfo.score}/100
                    </div>
                  </div>
                  <div className="bg-slate-800 p-2 rounded">
                    <div className="text-[10px] text-slate-500 uppercase">Panels</div>
                    <div className="text-sm font-bold text-white">
                      {popupInfo.solar_max_panels || '---'}
                    </div>
                  </div>
                </div>

                <a
                  href={`https://www.google.com/maps?q=${popupInfo.lat},${popupInfo.lng}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 py-1.5 rounded text-xs font-bold transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                  Street View
                </a>
              </div>
            </Popup>
          )}
        </Map>

        {/* Fallback info if token is missing */}
        {!MAPBOX_TOKEN.startsWith('pk.') && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm z-[100] text-center p-6">
            <div className="max-w-md">
              <Info className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
              <h4 className="text-white font-bold mb-2">Mapbox Token Required</h4>
              <p className="text-slate-400 text-sm mb-4">
                Please add <code>NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN</code> to your <code>.env.local</code> file to enable the interactive map.
              </p>
              <div className="bg-slate-800 p-3 rounded text-left text-xs font-mono text-emerald-400">
                # .env.local <br />
                NEXT_PUBLIC_MAPBOX_ACCESS_TOKEN=your_token_here
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
