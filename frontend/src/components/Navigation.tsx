import React from 'react';
import { PieChart, TrendingUp, Sparkles, Zap } from 'lucide-react';

interface NavigationProps {
  activeTab: 'portfolio' | 'stocks';
  setActiveTab: (tab: 'portfolio' | 'stocks') => void;
}

const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav className="flex space-x-2">
      <button
        onClick={() => setActiveTab('portfolio')}
        className={`group relative flex items-center space-x-3 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
          activeTab === 'portfolio'
            ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 shadow-lg shadow-cyan-500/25 border border-cyan-500/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/50 border border-transparent'
        }`}
      >
        <div className={`p-1.5 rounded-lg transition-all duration-300 ${
          activeTab === 'portfolio' 
            ? 'bg-gradient-to-r from-cyan-500 to-blue-500 shadow-lg' 
            : 'bg-slate-700 group-hover:bg-slate-600'
        }`}>
          <PieChart className="w-4 h-4 text-white" />
        </div>
        <span>Portfolio Intelligence</span>
        {activeTab === 'portfolio' && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full animate-pulse"></div>
        )}
      </button>
      <button
        onClick={() => setActiveTab('stocks')}
        className={`group relative flex items-center space-x-3 px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-300 ${
          activeTab === 'stocks'
            ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-400 shadow-lg shadow-purple-500/25 border border-purple-500/30'
            : 'text-slate-400 hover:text-white hover:bg-slate-800/50 border border-transparent'
        }`}
      >
        <div className={`p-1.5 rounded-lg transition-all duration-300 ${
          activeTab === 'stocks' 
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg' 
            : 'bg-slate-700 group-hover:bg-slate-600'
        }`}>
          <TrendingUp className="w-4 h-4 text-white" />
        </div>
        <span>Market Intelligence</span>
        {activeTab === 'stocks' && (
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full animate-pulse"></div>
        )}
      </button>
    </nav>
  );
};

export default Navigation;