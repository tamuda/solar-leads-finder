'use client';

import React from 'react';
import { 
  X, Zap, Building2, MapPin, TrendingUp, 
  DollarSign, Leaf, Phone, Globe, Star, 
  ShieldCheck, Layout, Calendar
} from 'lucide-react';

interface Building {
  building_id: string;
  address: string;
  city: string;
  state: string;
  building_type: string;
  building_area_sqft: number;
  solar_capacity_kw: number;
  score: number;
  // Enriched fields
  business_name: string | null;
  business_rating: number | null;
  business_reviews_count: number | null;
  business_website: string | null;
  business_phone: string | null;
  business_status: string | null;
  business_types: string[];
  
  solar_max_panels: number | null;
  solar_optimal_energy_kwh_year: number | null;
  solar_payback_years: number | null;
  solar_financially_viable: boolean;
  solar_sunshine_hours_year: number | null;
  solar_carbon_offset_kg_mwh: number | null;
  solar_roof_area_m2: number | null;
  solar_roof_segment_count: number;
  solar_min_panels: number | null;
  solar_min_energy_kwh: number | null;
  solar_percentage: number | null;
  solar_monthly_savings: number | null;
  icp_bucket: string;
  ineligible: boolean;
  lat: number | null;
  lng: number | null;
}

interface LeadDetailModalProps {
  building: Building | null;
  onClose: () => void;
}

export default function LeadDetailModal({ building, onClose }: LeadDetailModalProps) {
  if (!building) return null;

  const stats = [
    { 
      label: 'Potential Annual Yield', 
      value: building.solar_optimal_energy_kwh_year ? `${Math.round(building.solar_optimal_energy_kwh_year).toLocaleString()} kWh` : 'N/A',
      icon: TrendingUp,
      color: 'text-emerald-500'
    },
    { 
      label: 'Max Panel Capacity', 
      value: building.solar_max_panels ? `${building.solar_max_panels} Panels` : 'N/A',
      icon: Zap,
      color: 'text-orange-500'
    },
    { 
      label: 'Payback Period', 
      value: building.solar_payback_years ? `${building.solar_payback_years} Years` : 'N/A',
      icon: DollarSign,
      color: 'text-blue-500'
    },
    { 
      label: 'Financial Viability', 
      value: building.solar_financially_viable ? 'High' : 'Medium/Low',
      icon: ShieldCheck,
      color: building.solar_financially_viable ? 'text-emerald-500' : 'text-slate-500'
    }
  ];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-slate-900 border border-slate-700 w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-2xl shadow-2xl flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-700 flex justify-between items-start bg-slate-800/50">
          <div className="flex gap-4">
            <div className="bg-emerald-500/20 p-3 rounded-xl">
              <Building2 className="w-8 h-8 text-emerald-500" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white leading-tight">
                {building.business_name || 'Individual Property'}
              </h2>
              <div className="flex items-center gap-3 mt-1">
                <div className="flex items-center gap-2 text-slate-400">
                  <MapPin className="w-4 h-4" />
                  <span className="text-sm">{building.address}, {building.city}, {building.state}</span>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                  building.icp_bucket.includes('Tier 1') ? 'bg-emerald-500/10 text-emerald-400' : 
                  building.icp_bucket.includes('Tier 2') ? 'bg-blue-500/10 text-blue-400' :
                  building.icp_bucket.includes('De-prioritize') ? 'bg-red-500/10 text-red-400' :
                  'bg-slate-700 text-slate-400'
                }`}>
                  {building.icp_bucket}
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto p-6 space-y-8 flex-1">
          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {stats.map((stat, i) => (
              <div key={i} className="bg-slate-800 border border-slate-700/50 p-4 rounded-xl">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-slate-400 text-xs font-semibold uppercase">{stat.label}</span>
                </div>
                <div className="text-xl font-bold text-white">{stat.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left Column: Business & Contact */}
            <div className="space-y-6">
              <div>
                <h3 className="text-emerald-500 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                  <Star className="w-4 h-4" />
                  Business Information
                </h3>
                <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50 space-y-4">
                  {building.business_rating && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Google Rating</span>
                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1 bg-yellow-500/10 px-2 py-0.5 rounded text-yellow-500 font-bold">
                          <Star className="w-3 h-3 fill-current" />
                          {building.business_rating}
                        </div>
                        <span className="text-slate-500 text-xs">({building.business_reviews_count} reviews)</span>
                      </div>
                    </div>
                  )}
                  {building.business_phone && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Phone</span>
                      <a href={`tel:${building.business_phone}`} className="text-blue-400 hover:underline flex items-center gap-2">
                        <Phone className="w-3 h-3" />
                        {building.business_phone}
                      </a>
                    </div>
                  )}
                  {building.business_website && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Website</span>
                      <a href={building.business_website} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline flex items-center gap-2 max-w-[200px] truncate">
                        <Globe className="w-3 h-3" />
                        Visit Site
                      </a>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Status</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${building.business_status === 'OPERATIONAL' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-slate-500/10 text-slate-500'}`}>
                      {building.business_status || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-emerald-500 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                  <Layout className="w-4 h-4" />
                  Building Details
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                    <div className="text-slate-400 text-xs mb-1 uppercase">Roof Area</div>
                    <div className="text-white font-bold">{Math.round(building.solar_roof_area_m2 || 0).toLocaleString()} m²</div>
                  </div>
                  <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                    <div className="text-slate-400 text-xs mb-1 uppercase">Roof Segments</div>
                    <div className="text-white font-bold">{building.solar_roof_segment_count} Sections</div>
                  </div>
                </div>
              </div>

              {/* Map Preview */}
              <div>
                <h3 className="text-emerald-500 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Location Preview
                </h3>
                <div className="bg-slate-800/50 rounded-xl overflow-hidden border border-slate-700/50 h-[250px] relative group">
                  {building.lat && building.lng ? (
                    <iframe
                      width="100%"
                      height="100%"
                      style={{ border: 0 }}
                      loading="lazy"
                      allowFullScreen
                      src={`https://www.google.com/maps/embed/v1/search?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || ''}&q=${building.lat},${building.lng}&zoom=19&maptype=satellite`}
                    ></iframe>
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 gap-2">
                      <MapPin className="w-8 h-8 opacity-20" />
                      <span className="text-xs">Location coordinates unavailable</span>
                    </div>
                  )}
                  <div className="absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a 
                      href={`https://www.google.com/maps?q=${building.lat},${building.lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-slate-900/90 text-white text-[10px] px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 hover:bg-slate-800 transition-colors"
                    >
                      <MapPin className="w-3 h-3" />
                      Open Full Map
                    </a>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Detailed Solar Analysis */}
            <div className="space-y-6">
              <div>
                <h3 className="text-emerald-500 font-bold text-sm uppercase mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Detailed Solar Potential
                </h3>
                <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700/50 space-y-6">
                  {/* Energy Bar */}
                  <div>
                    <div className="flex justify-between items-end mb-2">
                      <span className="text-slate-400 text-xs font-bold uppercase">Solar Yield Offset</span>
                      <span className="text-white font-bold">{building.solar_percentage ? Math.round(building.solar_percentage) : '---'}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" 
                        style={{ width: `${building.solar_percentage || 0}%` }}
                      ></div>
                    </div>
                    <p className="text-slate-500 text-[10px] mt-2">Percentage of existing energy usage covered by solar.</p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Annual Sunshine Hours</span>
                      <span className="text-white font-medium">{Math.round(building.solar_sunshine_hours_year || 0).toLocaleString()} hrs</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Monthly Bill Savings</span>
                      <span className="text-emerald-400 font-bold">${building.solar_monthly_savings || '---'}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">Carbon Offset Potential</span>
                      <span className="text-white font-medium flex items-center gap-1">
                        <Leaf className="w-3 h-3 text-emerald-500" />
                        {Math.round(building.solar_carbon_offset_kg_mwh || 0)} kg/MWh
                      </span>
                    </div>
                  </div>

                  {/* Range Indicators */}
                  <div className="pt-4 border-t border-slate-700/50">
                    <div className="text-slate-400 text-xs font-bold uppercase mb-3">System Scalability</div>
                    <div className="space-y-2">
                       <div className="flex justify-between text-xs">
                         <span className="text-slate-500">Min Configuration ({building.solar_min_panels} panels)</span>
                         <span className="text-slate-300">{Math.round(building.solar_min_energy_kwh || 0).toLocaleString()} kWh</span>
                       </div>
                       <div className="flex justify-between text-xs">
                         <span className="text-slate-500">Max Configuration ({building.solar_max_panels} panels)</span>
                         <span className="text-emerald-400 font-bold">{Math.round(building.solar_optimal_energy_kwh_year || 0).toLocaleString()} kWh</span>
                       </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-700 bg-slate-800/30 flex justify-end gap-3">
           <button 
             onClick={onClose}
             className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors font-semibold"
           >
             Close
           </button>
           <button 
             className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg transition-all font-bold shadow-lg shadow-emerald-600/20 active:scale-95"
           >
             Contact Potential Lead
           </button>
        </div>
      </div>
    </div>
  );
}
