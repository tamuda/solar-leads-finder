'use client';

import { useState } from 'react';
import { 
  Building2, MapPin, Zap, TrendingUp, 
  ExternalLink, ChevronRight, DollarSign 
} from 'lucide-react';
import LeadDetailModal from './LeadDetailModal';

interface Building {
  building_id: string;
  address: string;
  normalized_address: string;
  city: string;
  state: string;
  building_type: string;
  building_area_sqft: number;
  num_stories: number;
  estimated_roof_area: number;
  solar_capacity_kw: number;
  score: number;
  lat: number | null;
  lng: number | null;
  geocoded: boolean;
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
}

interface LeadsTableProps {
  buildings: Building[];
  onSelectBuilding?: (id: string) => void;
}

export default function LeadsTable({ buildings, onSelectBuilding }: LeadsTableProps) {
  const [selectedLead, setSelectedLead] = useState<Building | null>(null);

  const handleRowClick = (building: Building) => {
    setSelectedLead(building);
    if (onSelectBuilding) {
      onSelectBuilding(building.building_id);
    }
  };

  // Sort by score descending
  const sortedBuildings = [...buildings].sort((a, b) => b.score - a.score);

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400 bg-emerald-500/20';
    if (score >= 50) return 'text-yellow-400 bg-yellow-500/20';
    return 'text-slate-400 bg-slate-500/20';
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      industrial: 'bg-purple-500/20 text-purple-400',
      warehouse: 'bg-blue-500/20 text-blue-400',
      office: 'bg-cyan-500/20 text-cyan-400',
      retail: 'bg-pink-500/20 text-pink-400',
      commercial: 'bg-orange-500/20 text-orange-400',
      mixed_use: 'bg-indigo-500/20 text-indigo-400',
      institutional: 'bg-teal-500/20 text-teal-400',
    };
    return colors[type] || 'bg-slate-500/20 text-slate-400';
  };

  return (
    <>
      <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-700/50 flex items-center justify-between">
          <div>
            <h3 className="text-white text-lg font-semibold flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-500" />
              Comprehensive Lead Explorer
            </h3>
            <p className="text-slate-400 text-sm mt-1">
              Deep enrichment via Google Places & Solar Insights. Click a row for full analysis.
            </p>
          </div>
          <div className="text-xs text-slate-500">
            Total Matches: {sortedBuildings.length}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-900/50">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Rank
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Entity / Business
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Solar Potential
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Financials
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  Score
                </th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {sortedBuildings.map((building, index) => (
                <tr
                  key={building.building_id}
                  onClick={() => handleRowClick(building)}
                  className="group hover:bg-slate-700/30 transition-all cursor-pointer"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-slate-400 font-medium group-hover:text-emerald-500 transition-colors">#{index + 1}</span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-start gap-3">
                       <div className={`p-2 rounded-lg ${building.business_name ? 'bg-emerald-500/10' : 'bg-slate-700'} mt-0.5`}>
                          <Building2 className={`w-4 h-4 ${building.business_name ? 'text-emerald-500' : 'text-slate-400'}`} />
                       </div>
                       <div>
                        <div className="text-white font-bold leading-tight">
                          {building.business_name || 'Owner/Operator'}
                        </div>
                        <div className="text-slate-400 text-xs mt-0.5 flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {building.address.split(',')[0]}, {building.city}
                        </div>
                        <div className="mt-1.5 flex gap-2">
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
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-emerald-500" />
                      <div>
                        <div className="text-white font-medium">
                          {building.solar_max_panels ? `${building.solar_max_panels} panels` : 'N/A'}
                        </div>
                        <div className="text-slate-500 text-[10px]">
                          {building.solar_optimal_energy_kwh_year 
                            ? `${Math.round(building.solar_optimal_energy_kwh_year).toLocaleString()} kWh / Year`
                            : 'Scanning capacity...'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {building.solar_payback_years ? (
                      <div className="space-y-1">
                        <div className="text-white font-medium flex items-center gap-1">
                          <DollarSign className="w-3 h-3 text-emerald-500" />
                          {building.solar_payback_years}y Payback
                        </div>
                        <div className="flex items-center gap-2">
                           <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-500">
                             {building.solar_financially_viable ? 'PROFITABLE' : 'VIABLE'}
                           </span>
                           {building.solar_percentage && (
                             <span className="text-slate-500 text-[10px]">
                               {Math.round(building.solar_percentage)}% Coverage
                             </span>
                           )}
                        </div>
                      </div>
                    ) : (
                      <span className="text-slate-600 text-xs italic">Awaiting calculation...</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">
                    <span className={`px-4 py-1.5 rounded-lg text-sm font-black border border-current shadow-lg shadow-emerald-500/5 ${getScoreColor(building.score)}`}>
                      {building.score}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                       <button
                         onClick={(e) => {
                           e.stopPropagation();
                           if (onSelectBuilding) onSelectBuilding(building.building_id);
                         }}
                         className="p-2 hover:bg-emerald-500/20 rounded-lg text-slate-500 hover:text-emerald-500 transition-colors"
                         title="View on Map"
                       >
                         <MapPin className="w-5 h-5" />
                       </button>
                       <ChevronRight className="w-5 h-5 text-slate-700 group-hover:text-emerald-500 translate-x-0 group-hover:translate-x-1 transition-all" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <LeadDetailModal 
        building={selectedLead} 
        onClose={() => setSelectedLead(null)} 
      />
    </>
  );
}
