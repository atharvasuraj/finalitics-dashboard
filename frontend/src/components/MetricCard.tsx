import React from 'react';
import { DivideIcon as LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  color: 'cyan' | 'emerald' | 'purple' | 'orange' | 'red';
  subtitle?: string;
  trend?: 'up' | 'down';
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
  trend
}) => {
  const colorClasses = {
    cyan: 'from-cyan-400 to-blue-500',
    emerald: 'from-emerald-400 to-cyan-500',
    purple: 'from-purple-400 to-pink-500',
    orange: 'from-orange-400 to-red-500',
    red: 'from-red-400 to-pink-500',
  };

  const shadowClasses = {
    cyan: 'shadow-cyan-500/25',
    emerald: 'shadow-emerald-500/25',
    purple: 'shadow-purple-500/25',
    orange: 'shadow-orange-500/25',
    red: 'shadow-red-500/25',
  };

  const trendClasses = {
    up: 'text-emerald-400',
    down: 'text-red-400',
  };

  return (
    <div className="group bg-slate-800/30 backdrop-blur-xl rounded-2xl border border-slate-700/50 p-6 hover:border-slate-600/50 transition-all duration-300 shadow-2xl hover:shadow-xl hover:scale-105">
      <div className="flex items-center justify-between mb-6">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-r ${colorClasses[color]} shadow-lg ${shadowClasses[color]} group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        {trend && (
          <div className={`text-sm font-bold ${trendClasses[trend]} flex items-center space-x-1`}>
            <span>{trend === 'up' ? '↗' : '↘'}</span>
          </div>
        )}
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-400 mb-2 uppercase tracking-wider">{title}</h3>
        <div className="text-3xl font-bold text-white mb-1">{value}</div>
        {subtitle && (
          <p className="text-sm text-slate-500">{subtitle}</p>
        )}
      </div>
    </div>
  );
};

export default MetricCard;