import { Building2, Zap, MapPin, TrendingUp, DollarSign } from 'lucide-react';

interface StatsCardsProps {
  stats: {
    totalBuildings: number;
    totalRoofArea: number;
    totalSolarCapacity: number;
    avgScore: number;
    totalPanels?: number;
    avgPayback?: number;
  };
}

export default function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: 'Buildings Enriched',
      value: stats.totalBuildings,
      icon: Building2,
      color: 'from-blue-500 to-cyan-600',
      suffix: '',
    },
    {
      title: 'Max Panel Capacity',
      value: stats.totalPanels?.toLocaleString() || '0',
      icon: Zap,
      color: 'from-orange-500 to-red-600',
      suffix: 'panels',
    },
    {
      title: 'Solar Yield Potential',
      value: Math.round(stats.totalSolarCapacity).toLocaleString(),
      icon: TrendingUp,
      color: 'from-emerald-500 to-teal-600',
      suffix: 'kWh/yr',
    },
    {
      title: 'Avg Payback',
      value: stats.avgPayback?.toFixed(1) || 'N/A',
      icon: DollarSign,
      color: 'from-purple-500 to-pink-600',
      suffix: 'years',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-xl p-6 hover:shadow-xl hover:shadow-emerald-500/10 transition-all"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`bg-gradient-to-br ${card.color} p-3 rounded-lg`}>
              <card.icon className="w-6 h-6 text-white" />
            </div>
          </div>
          <h3 className="text-slate-400 text-sm font-medium mb-1">{card.title}</h3>
          <p className="text-white text-3xl font-bold">
            {card.value} <span className="text-lg text-slate-400 font-normal">{card.suffix}</span>
          </p>
        </div>
      ))}
    </div>
  );
}
