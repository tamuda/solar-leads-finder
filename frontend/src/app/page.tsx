'use client';

import { useState, useEffect } from 'react';
import { Building2, Zap, MapPin, TrendingUp, Filter, Download, Search } from 'lucide-react';
import LeadsTable from '@/components/LeadsTable';
import StatsCards from '@/components/StatsCards';
import ChartsSection from '@/components/ChartsSection';
import MapView from '@/components/MapView';

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
  ineligible: boolean;
  icp_bucket: string;
}

export default function Dashboard() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  
  // Filtering & Sorting State
  const [filter, setFilter] = useState('all'); // Priority
  const [cityFilter, setCityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'score', direction: 'desc' });

  const [selectedBuildingId, setSelectedBuildingId] = useState<string | null>(null);

  useEffect(() => {
    // Load the building data
    fetch('/api/buildings')
      .then(res => res.json())
      .then(data => {
        // Hard filter for 5000 sq ft minimum
        const eligible = data.filter((b: Building) => !b.ineligible);
        setBuildings(eligible);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error loading buildings:', err);
        setLoading(false);
      });
  }, []);

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await fetch('/api/discover', { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'Discovery started!');
    } catch (err) {
      console.error('Discovery error:', err);
      alert('Failed to start discovery.');
    } finally {
      setTimeout(() => setDiscovering(false), 2000);
    }
  };

  const handleSelectBuilding = (id: string) => {
    setSelectedBuildingId(id);
    // Scroll map into view if needed? Or just let it happen.
  };

  const uniqueCities = Array.from(new Set(buildings.map(b => b.city))).sort();

  const filteredBuildings = buildings.filter(b => {
      // 1. Text Search
      if (searchTerm) {
          const searchLower = searchTerm.toLowerCase();
          const matchesName = b.business_name?.toLowerCase().includes(searchLower) || false;
          const matchesAddr = b.address.toLowerCase().includes(searchLower);
          if (!matchesName && !matchesAddr) return false;
      }

      // 2. Priority Filter
      if (filter === 'high' && b.score < 70) return false;
      if (filter === 'medium' && (b.score < 50 || b.score >= 70)) return false;
      if (filter === 'low' && b.score >= 50) return false;

      // 3. City Filter
      if (cityFilter !== 'all' && b.city !== cityFilter) return false;

      // 4. Type Filter (Enhanced)
      if (typeFilter !== 'all') {
         const typeStr = (b.building_type || '').toLowerCase();
         // Check business types array if available (assuming b.business_types exists)
         const bizTypes = (b.business_types || []).map((t: string) => t.toLowerCase());
         const combinedTypes = [typeStr, ...bizTypes].join(' ');

         if (typeFilter === 'industrial') {
             if (!combinedTypes.includes('industrial') && !combinedTypes.includes('warehouse') && !combinedTypes.includes('manufacturing')) return false;
         }
         else if (typeFilter === 'non_profit') {
             // Broad net for non-profits
             const npKeywords = ['church', 'religious', 'school', 'university', 'college', 'museum', 'community', 'non_profit', 'charity'];
             if (!npKeywords.some(k => combinedTypes.includes(k))) return false;
         }
         else if (typeFilter === 'commercial') {
             const commKeywords = ['retail', 'store', 'shop', 'office', 'restaurant', 'mall', 'commercial'];
             if (!commKeywords.some(k => combinedTypes.includes(k))) return false;
         }
         else if (typeFilter === 'church') {
             if (!combinedTypes.includes('church') && !combinedTypes.includes('religious')) return false;
         }
         // Fallback for direct match
         else if (!combinedTypes.includes(typeFilter)) {
             return false;
         }
      }

      return true;
  }).sort((a, b) => {
      const dir = sortConfig.direction === 'asc' ? 1 : -1;
      
      if (sortConfig.key === 'score') return (a.score - b.score) * dir;
      if (sortConfig.key === 'roof') return ((a.estimated_roof_area || 0) - (b.estimated_roof_area || 0)) * dir;
      if (sortConfig.key === 'panels') return ((a.solar_max_panels || 0) - (b.solar_max_panels || 0)) * dir;
      if (sortConfig.key === 'savings') return ((a.solar_monthly_savings || 0) - (b.solar_monthly_savings || 0)) * dir;
      
      return 0;
  });
  
    const stats = {
      totalBuildings: buildings.length,
      totalRoofArea: buildings.reduce((sum, b) => sum + (b.estimated_roof_area || 0), 0),
      totalSolarCapacity: buildings.reduce((sum, b) => sum + (b.solar_optimal_energy_kwh_year || (b.solar_capacity_kw * 1200)), 0),
      avgScore: buildings.length > 0 
        ? buildings.reduce((sum, b) => sum + b.score, 0) / buildings.length 
        : 0,
      totalPanels: buildings.reduce((sum, b) => sum + (b.solar_max_panels || 0), 0),
      avgPayback: buildings.filter(b => b.solar_payback_years).length > 0
        ? buildings.filter(b => b.solar_payback_years).reduce((sum, b) => sum + (b.solar_payback_years || 0), 0) / buildings.filter(b => b.solar_payback_years).length
        : 0,
    };
  
    if (loading) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-500 mx-auto mb-4"></div>
            <p className="text-slate-300 text-lg">Loading solar leads...</p>
          </div>
        </div>
      );
    }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-xl border-b border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="bg-gradient-to-br from-emerald-500 to-teal-600 p-2 rounded-xl">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Solar Leads Dashboard</h1>
                <p className="text-sm text-slate-400">Upstate New York Commercial Buildings</p>
              </div>
            </div>
            <div className="flex gap-2">
                <button 
                  onClick={handleDiscover}
                  disabled={discovering}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all border border-blue-500/30 ${
                    discovering 
                    ? 'bg-blue-500/20 text-blue-200 cursor-wait' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-500/20'
                  }`}
                >
                  <Search className={`w-4 h-4 ${discovering ? 'animate-pulse' : ''}`} />
                  {discovering ? 'Hunting Leads...' : 'Discover More Leads'}
                </button>
                <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg transition-colors">
                  <Download className="w-4 h-4" />
                  Export CSV
                </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Stats Cards */}
        <StatsCards stats={stats} />

        {/* Charts */}
        <ChartsSection buildings={buildings} />

        {/* Lead Discovery & Filtering Engine */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Filter className="w-5 h-5 text-emerald-500" />
              Lead Discovery Engine
            </h2>
            <div className="text-sm text-slate-400">
              Showing {filteredBuildings.length} matches
            </div>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-xl p-4 flex flex-col xl:flex-row gap-4 justify-between">
             
             {/* Primary Filters */}
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 flex-1">
                {/* Search */}
                <div className="relative group">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400 group-focus-within:text-emerald-500 transition-colors" />
                  <input 
                    type="text" 
                    placeholder="Search name, address..." 
                    className="bg-slate-900/50 border border-slate-700 text-white pl-9 pr-4 py-2 rounded-lg w-full focus:ring-2 focus:ring-emerald-500 outline-none placeholder:text-slate-500 transition-all"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>

                {/* Priority */}
                <select 
                  value={filter} 
                  onChange={(e) => setFilter(e.target.value)}
                  className="bg-slate-900/50 border border-slate-700 text-white px-4 py-2 rounded-lg outline-none cursor-pointer focus:ring-2 focus:ring-emerald-500 hover:bg-slate-800 transition-colors"
                >
                  <option value="all">Any Score</option>
                  <option value="high">High Priority (70+)</option>
                  <option value="medium">Medium (50-70)</option>
                  <option value="low">Low Priority</option>
                </select>

                {/* City */}
                <select 
                  value={cityFilter} 
                  onChange={(e) => setCityFilter(e.target.value)}
                  className="bg-slate-900/50 border border-slate-700 text-white px-4 py-2 rounded-lg outline-none cursor-pointer focus:ring-2 focus:ring-emerald-500 hover:bg-slate-800 transition-colors"
                >
                  <option value="all">All Cities</option>
                  {uniqueCities.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
                
                {/* Entity Type - Enhanced */}
                 <select 
                  value={typeFilter} 
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-slate-900/50 border border-slate-700 text-white px-4 py-2 rounded-lg outline-none cursor-pointer focus:ring-2 focus:ring-emerald-500 hover:bg-slate-800 transition-colors"
                >
                  <option value="all">All Sector Entities</option>
                  <option value="industrial">Industrial & Warehousing</option>
                  <option value="non_profit">Non-Profit / Faith / Edu</option>
                  <option value="commercial">Commercial / Retail</option>
                  <option value="church">Churches Only</option>
                </select>
             </div>

             {/* Secondary: Sort */}
             <div className="flex items-center gap-2 border-l border-slate-700/50 pl-0 xl:pl-4 mt-2 xl:mt-0 pt-2 xl:pt-0 border-t xl:border-t-0">
                <span className="text-slate-500 text-xs uppercase font-bold tracking-wider">Sort:</span>
                <select 
                  value={sortConfig.key} 
                  onChange={(e) => setSortConfig({ ...sortConfig, key: e.target.value })}
                  className="bg-slate-900/50 border border-slate-700 text-white px-3 py-2 rounded-lg outline-none cursor-pointer text-sm"
                >
                  <option value="score">Score</option>
                  <option value="roof">Roof Size</option>
                  <option value="panels">Panels</option>
                  <option value="savings">Savings</option>
                </select>
                <button 
                  onClick={() => setSortConfig({ ...sortConfig, direction: sortConfig.direction === 'asc' ? 'desc' : 'asc' })}
                  className="p-2 bg-slate-900/50 border border-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors hover:bg-slate-700"
                  title={sortConfig.direction === 'asc' ? 'Ascending' : 'Descending'}
                >
                  {sortConfig.direction === 'desc' ? <TrendingUp className="w-4 h-4 rotate-180" /> : <TrendingUp className="w-4 h-4" />}
                </button>
             </div>
          </div>
        </div>

        {/* Leads Table */}
        <LeadsTable 
          buildings={filteredBuildings} 
          onSelectBuilding={handleSelectBuilding}
        />
      </main>


      {/* Footer */}
      <footer className="bg-slate-900/50 backdrop-blur-xl border-t border-slate-700/50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-slate-400 text-sm">
            Solar Lead Identification System • Powered by AI & OpenStreetMap
          </p>
        </div>
      </footer>
    </div>
  );
}
