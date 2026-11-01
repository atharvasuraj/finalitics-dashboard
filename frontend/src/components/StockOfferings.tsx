import React, { useEffect } from 'react';
import { TrendingUp, Shield, DollarSign, BarChart3, Users, Clock, Zap, Target, Brain, Sparkles } from 'lucide-react';
import { StockOfferingsData } from '../App';
import MetricCard from './MetricCard';

interface StockOfferingsProps {
  data: StockOfferingsData | null;
  onLoadData: () => void;
}

const StockOfferings: React.FC<StockOfferingsProps> = ({ data, onLoadData }) => {
  useEffect(() => {
    if (!data) {
      onLoadData();
    }
  }, [data, onLoadData]);

  if (!data) {
    return (
      <div className="space-y-12">
        <div className="text-center py-16">
          <div className="relative mb-8">
            <div className="w-24 h-24 bg-gradient-to-r from-purple-400 via-pink-500 to-red-500 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-purple-500/25">
              <TrendingUp className="w-12 h-12 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
              <Zap className="w-4 h-4 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
              AI-Curated Market
            </span>
            <br />
            <span className="text-white">Intelligence Baskets</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed">
            Discover professionally curated investment baskets powered by advanced machine learning algorithms 
            and designed for optimal risk-adjusted returns across different market conditions.
          </p>
        </div>
      </div>
    );
  }

  const baskets = Object.entries(data.baskets);

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30';
      case 'Medium': return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30';
      case 'High': return 'text-red-400 bg-red-500/20 border-red-500/30';
      default: return 'text-slate-400 bg-slate-500/20 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center p-8 bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50">
        <h1 className="text-4xl font-bold mb-4">
          <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-red-400 bg-clip-text text-transparent">
            AI Market Intelligence
          </span>
        </h1>
        <p className="text-xl text-slate-400 max-w-3xl mx-auto">
          Neural network-powered investment baskets based on comprehensive quantum market analysis
        </p>
      </div>

      {/* Market Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Stocks Analyzed"
          value={data.total_stocks_analyzed.toLocaleString()}
          icon={BarChart3}
          color="cyan"
        />
        <MetricCard
          title="Market Cap"
          value={`$${(data.market_summary.total_market_cap / 1e12).toFixed(1)}T`}
          icon={DollarSign}
          color="emerald"
        />
        <MetricCard
          title="Avg P/E Ratio"
          value={data.market_summary.avg_pe_ratio.toFixed(1)}
          icon={TrendingUp}
          color="purple"
        />
        <MetricCard
          title="Sectors"
          value={data.market_summary.sectors_analyzed.toString()}
          icon={Users}
          color="orange"
        />
      </div>

      {/* Investment Baskets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {baskets.map(([basketName, basket]) => (
          <div key={basketName} className="group bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50 overflow-hidden hover:border-slate-600/50 transition-all duration-300 shadow-2xl hover:shadow-purple-500/10">
            {/* Basket Header */}
            <div className="p-8 border-b border-slate-700/50 bg-slate-800/50">
              <div className="flex items-start justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white">{basketName}</h3>
                </div>
                <span className={`px-4 py-2 rounded-xl text-sm font-semibold border ${getRiskColor(basket.risk_level)}`}>
                  {basket.risk_level} Risk
                </span>
              </div>
              <p className="text-slate-400 mb-6 leading-relaxed">{basket.description}</p>
              <div className="flex items-center text-sm text-slate-400">
                <DollarSign className="w-4 h-4 mr-2 text-emerald-400" />
                <span>Minimum Investment: <span className="text-white font-semibold">{basket.min_investment}</span></span>
              </div>
            </div>

            {/* Basket Metrics */}
            <div className="p-8 border-b border-slate-700/50 bg-gradient-to-r from-slate-800/30 to-slate-700/30">
              <div className="grid grid-cols-2 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-emerald-400 mb-2">
                    {basket.avg_return.toFixed(1)}%
                  </div>
                  <div className="text-sm text-slate-400 font-medium">Average Return</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-cyan-400 mb-2">
                    {basket.avg_volatility.toFixed(1)}%
                  </div>
                  <div className="text-sm text-slate-400 font-medium">Volatility</div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6 mt-6">
                <div className="text-center">
                  <div className="text-xl font-bold text-white mb-1">
                    {basket.avg_pe.toFixed(1)}
                  </div>
                  <div className="text-sm text-slate-400 font-medium">Average P/E</div>
                </div>
                <div className="text-center">
                  <div className="text-xl font-bold text-white mb-1">
                    {basket.avg_sharpe.toFixed(2)}
                  </div>
                  <div className="text-sm text-slate-400 font-medium">Sharpe Ratio</div>
                </div>
              </div>
            </div>

            {/* Top Holdings */}
            <div className="p-8">
              <h4 className="font-bold text-white mb-6 flex items-center space-x-2">
                <Brain className="w-5 h-5 text-purple-400" />
                <span>AI-Selected Holdings ({basket.stocks.length} stocks)</span>
              </h4>
              <div className="space-y-4">
                {basket.stocks.slice(0, 5).map((stock) => (
                  <div key={stock.symbol} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl border border-slate-600/30 hover:border-slate-500/50 transition-all duration-300">
                    <div className="flex-1">
                      <div className="font-semibold text-white text-lg">{stock.symbol}</div>
                      <div className="text-sm text-slate-400 truncate">{stock.name}</div>
                      <div className="text-xs text-slate-500 mt-1">{stock.sector}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-white text-lg">
                        ${stock.current_price.toFixed(2)}
                      </div>
                      <div className={`text-sm font-semibold ${stock.annual_return >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {stock.annual_return >= 0 ? '+' : ''}{stock.annual_return.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                ))}
                {basket.stocks.length > 5 && (
                  <div className="text-sm text-slate-500 text-center pt-4 font-medium">
                    +{basket.stocks.length - 5} more AI-selected stocks
                  </div>
                )}
              </div>
            </div>

            {/* Action Button */}
            <div className="p-8 bg-slate-800/50 border-t border-slate-700/50">
              <button className="w-full px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-2xl hover:from-purple-400 hover:to-pink-500 transition-all duration-300 font-bold shadow-2xl shadow-purple-500/25 hover:shadow-purple-500/40 hover:scale-105 flex items-center justify-center space-x-3">
                <Sparkles className="w-5 h-5" />
                <span>Analyze Full Basket</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Last Updated */}
      <div className="text-center text-sm text-slate-500 p-6 bg-slate-800/20 rounded-2xl border border-slate-700/30">
        <div className="flex items-center justify-center space-x-2">
          <Clock className="w-4 h-4" />
          <span>Neural network last updated: {new Date(data.last_updated).toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
};

export default StockOfferings;