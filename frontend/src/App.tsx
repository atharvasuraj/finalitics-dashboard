import React, { useState, useCallback } from 'react';
import { Upload, TrendingUp, PieChart, BarChart3, ArrowUp, ArrowDown, DollarSign, Shield, Users, Clock, Zap, Brain, Sparkles } from 'lucide-react';
import PortfolioAnalysis from './components/PortfolioAnalysis';
import StockOfferings from './components/StockOfferings';
import Navigation from './components/Navigation';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';

export interface PortfolioData {
  quantitative_data: {
    funds: Record<string, {
      fund_id: string;
      fund_name: string;
      cagr: number;
      volatility: number;
      max_drawdown: number;
      sharpe_ratio: number;
      beta: number;
      alpha: number;
      r_squared: number;
      holdings_count: number;
    }>;
    portfolio_analysis: {
      total_funds: number;
      portfolio_overlap: {
        overlap_percentage: number;
        common_holdings: Array<{
          security_name: string;
          funds_count: number;
          average_weight: number;
          funds: string[];
        }>;
      };
    };
    timestamp: string;
  };
  ai_analysis: string;
}

export interface StockOffering {
  description: string;
  strategy: string;
  risk_level: 'Low' | 'Medium' | 'High';
  min_investment: string;
  stocks: Array<{
    symbol: string;
    name: string;
    sector: string;
    industry: string;
    csv_industry: string;
    current_price: number;
    annual_return: number;
    volatility: number;
    pe_ratio: number;
    market_cap: number;
    dividend_yield: number;
    sharpe_ratio: number;
    max_drawdown: number;
    beta: number;
  }>;
  avg_return: number;
  avg_volatility: number;
  avg_pe: number;
  avg_sharpe: number;
}

export interface StockOfferingsData {
  baskets: Record<string, StockOffering>;
  total_stocks_analyzed: number;
  last_updated: string;
  market_summary: {
    total_market_cap: number;
    avg_pe_ratio: number;
    avg_dividend_yield: number;
    sectors_analyzed: number;
  };
}

function App() {
  const [activeTab, setActiveTab] = useState<'portfolio' | 'stocks'>('portfolio');
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [stockData, setStockData] = useState<StockOfferingsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      const data: PortfolioData = await response.json();
      setPortfolioData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSampleData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/sample-data');
      if (!response.ok) {
        throw new Error(`Failed to load sample data: ${response.statusText}`);
      }
      
      const data: PortfolioData = await response.json();
      setPortfolioData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sample data');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStockOfferings = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/stock-offerings');
      if (!response.ok) {
        throw new Error(`Failed to load stock offerings: ${response.statusText}`);
      }
      
      const data: StockOfferingsData = await response.json();
      setStockData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stock offerings');
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-r from-cyan-400/20 to-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-r from-purple-400/20 to-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-emerald-400/10 to-cyan-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <header className="relative bg-slate-900/80 backdrop-blur-xl border-b border-slate-700/50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/25">
                  <Brain className="w-7 h-7 text-white" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full animate-pulse"></div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
                  KVGAI
                </h1>
                <p className="text-xs text-slate-400 font-medium">Financial Intelligence Platform</p>
              </div>
            </div>
            <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-lg">
                <span className="text-white font-semibold text-sm">AI</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Loading Overlay */}
      {loading && <LoadingSpinner />}

      {/* Error Display */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 relative z-10">
          <ErrorMessage message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        {activeTab === 'portfolio' ? (
          <PortfolioAnalysis
            data={portfolioData}
            onFileUpload={handleFileUpload}
            onSampleData={handleSampleData}
          />
        ) : (
          <StockOfferings
            data={stockData}
            onLoadData={loadStockOfferings}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="relative bg-slate-900/50 backdrop-blur-xl border-t border-slate-700/50 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <span className="font-bold text-xl bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">KVGAI</span>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">
                Next-generation AI-powered financial analysis platform for intelligent portfolio optimization and market insights.
              </p>
              <div className="flex space-x-3">
                <div className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-slate-700 transition-colors cursor-pointer">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                </div>
                <div className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center hover:bg-slate-700 transition-colors cursor-pointer">
                  <Zap className="w-4 h-4 text-purple-400" />
                </div>
              </div>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">AI Platform</h3>
              <ul className="space-y-3 text-sm text-slate-400">
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Portfolio Intelligence</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Market Analysis</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Risk Assessment</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Predictive Analytics</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">Advanced Features</h3>
              <ul className="space-y-3 text-sm text-slate-400">
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Neural Networks</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Real-time Processing</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Quantum Computing</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Machine Learning</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-white mb-4">Enterprise</h3>
              <ul className="space-y-3 text-sm text-slate-400">
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">API Documentation</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Enterprise Solutions</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">24/7 Support</li>
                <li className="hover:text-cyan-400 transition-colors cursor-pointer">Custom Integration</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-slate-700/50 pt-8 mt-8">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <p className="text-sm text-slate-500">
                © 2025 KVGAI Platform. Powered by Advanced AI Technology.
              </p>
              <div className="flex items-center space-x-6 text-sm text-slate-400">
                <span className="hover:text-cyan-400 transition-colors cursor-pointer">Privacy Policy</span>
                <span className="hover:text-cyan-400 transition-colors cursor-pointer">Terms of Service</span>
                <span className="hover:text-cyan-400 transition-colors cursor-pointer">Security</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;