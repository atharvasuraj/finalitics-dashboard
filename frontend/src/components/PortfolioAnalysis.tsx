import React from 'react';
import { Upload, FileText, TrendingUp, Shield, BarChart3, Activity, Brain, Sparkles, Zap, Target } from 'lucide-react';
import FileUpload from './FileUpload';
import MetricCard from './MetricCard';
import { PortfolioData } from '../App';

interface PortfolioAnalysisProps {
  data: PortfolioData | null;
  onFileUpload: (file: File) => void;
  onSampleData: () => void;
}

const PortfolioAnalysis: React.FC<PortfolioAnalysisProps> = ({
  data,
  onFileUpload,
  onSampleData,
}) => {
  if (!data) {
    return (
      <div className="space-y-12">
        {/* Hero Section */}
        <div className="text-center py-16">
          <div className="relative mb-8">
            <div className="w-24 h-24 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-cyan-500/25">
              <Brain className="w-12 h-12 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
              AI-Powered Portfolio
            </span>
            <br />
            <span className="text-white">Intelligence Platform</span>
          </h1>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto mb-12 leading-relaxed">
            Harness the power of advanced machine learning algorithms to analyze your portfolio with 
            unprecedented precision and generate actionable insights for optimal performance.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <button
              onClick={onSampleData}
              className="group relative px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-2xl hover:from-cyan-400 hover:to-blue-500 transition-all duration-300 font-semibold shadow-2xl shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-105"
            >
              <div className="flex items-center space-x-3">
                <Zap className="w-5 h-5" />
                <span>Experience AI Demo</span>
              </div>
              <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/20 to-blue-500/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>
            <a
              href="#upload"
              className="group px-8 py-4 border-2 border-slate-600 text-slate-300 rounded-2xl hover:border-cyan-400 hover:text-cyan-400 transition-all duration-300 font-semibold hover:bg-slate-800/50"
            >
              <div className="flex items-center space-x-3">
                <Upload className="w-5 h-5" />
                <span>Upload Portfolio Data</span>
              </div>
            </a>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 py-16">
          <div className="group text-center p-8 rounded-3xl bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 hover:border-cyan-500/50 transition-all duration-300 hover:shadow-2xl hover:shadow-cyan-500/10">
            <div className="w-16 h-16 bg-gradient-to-r from-emerald-400 to-cyan-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-emerald-500/25">
              <TrendingUp className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-4">Performance Analytics</h3>
            <p className="text-slate-400 leading-relaxed">
              Advanced quantitative analysis including CAGR, volatility, Sharpe ratio, and sophisticated risk-adjusted performance metrics.
            </p>
          </div>
          <div className="group text-center p-8 rounded-3xl bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 hover:border-purple-500/50 transition-all duration-300 hover:shadow-2xl hover:shadow-purple-500/10">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-purple-500/25">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-4">Risk Intelligence</h3>
            <p className="text-slate-400 leading-relaxed">
              Comprehensive risk assessment through beta analysis, alpha generation, maximum drawdown evaluation, and correlation matrices.
            </p>
          </div>
          <div className="group text-center p-8 rounded-3xl bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 hover:border-orange-500/50 transition-all duration-300 hover:shadow-2xl hover:shadow-orange-500/10">
            <div className="w-16 h-16 bg-gradient-to-r from-orange-400 to-red-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-300 shadow-lg shadow-orange-500/25">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-xl font-bold text-white mb-4">Neural Insights</h3>
            <p className="text-slate-400 leading-relaxed">
              AI-powered interpretation and strategic recommendations based on deep learning analysis of market patterns and portfolio dynamics.
            </p>
          </div>
        </div>

        {/* Upload Section */}
        <div id="upload" className="bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50 p-12 shadow-2xl">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Upload Portfolio Data</h2>
            <p className="text-slate-400 text-lg">
              Advanced AI processing supports JSON and CSV formats up to 16MB. Get instant intelligent analysis.
            </p>
          </div>
          <FileUpload onFileUpload={onFileUpload} />
        </div>
      </div>
    );
  }

  const funds = Object.values(data.quantitative_data.funds);
  const portfolioAnalysis = data.quantitative_data.portfolio_analysis;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6 p-8 bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">AI Portfolio Analysis Results</h1>
          <p className="text-slate-400 text-lg">
            Intelligent analysis of {portfolioAnalysis.total_funds} funds • {new Date(data.quantitative_data.timestamp).toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={onSampleData}
            className="px-6 py-3 text-cyan-400 border border-cyan-500/30 rounded-xl hover:bg-cyan-500/10 transition-all duration-300 font-medium"
          >
            Load AI Demo
          </button>
          <FileUpload onFileUpload={onFileUpload} compact />
        </div>
      </div>

      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Funds"
          value={portfolioAnalysis.total_funds.toString()}
          icon={FileText}
          color="cyan"
        />
        <MetricCard
          title="Portfolio Overlap"
          value={`${portfolioAnalysis.portfolio_overlap.overlap_percentage.toFixed(1)}%`}
          icon={Activity}
          color="purple"
        />
        <MetricCard
          title="Common Holdings"
          value={portfolioAnalysis.portfolio_overlap.common_holdings.length.toString()}
          icon={BarChart3}
          color="emerald"
        />
        <MetricCard
          title="Avg Holdings"
          value={Math.round(funds.reduce((sum, fund) => sum + fund.holdings_count, 0) / funds.length).toString()}
          icon={Target}
          color="orange"
        />
      </div>

      {/* Fund Performance */}
      <div className="bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50 overflow-hidden shadow-2xl">
        <div className="px-8 py-6 border-b border-slate-700/50 bg-slate-800/50">
          <h2 className="text-xl font-bold text-white flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span>Fund Performance Intelligence</span>
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/80">
              <tr>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Fund Name
                </th>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  CAGR
                </th>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Volatility
                </th>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Sharpe Ratio
                </th>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Max Drawdown
                </th>
                <th className="px-8 py-4 text-left text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Beta
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {funds.map((fund, index) => (
                <tr key={fund.fund_id} className="hover:bg-slate-700/30 transition-colors duration-200">
                  <td className="px-8 py-6 whitespace-nowrap">
                    <div className="text-sm font-semibold text-white">{fund.fund_name}</div>
                    <div className="text-sm text-slate-400">{fund.fund_id}</div>
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-sm font-semibold">
                    <span className={fund.cagr >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                      {fund.cagr.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-sm text-slate-300 font-medium">
                    {fund.volatility.toFixed(2)}%
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-sm text-slate-300 font-medium">
                    {fund.sharpe_ratio.toFixed(2)}
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-sm text-red-400 font-medium">
                    {fund.max_drawdown.toFixed(2)}%
                  </td>
                  <td className="px-8 py-6 whitespace-nowrap text-sm text-slate-300 font-medium">
                    {fund.beta.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Common Holdings */}
      {portfolioAnalysis.portfolio_overlap.common_holdings.length > 0 && (
        <div className="bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50 shadow-2xl">
          <div className="px-8 py-6 border-b border-slate-700/50 bg-slate-800/50">
            <h2 className="text-xl font-bold text-white flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-500 rounded-lg flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <span>Common Holdings Analysis</span>
            </h2>
          </div>
          <div className="p-8">
            <div className="grid gap-6">
              {portfolioAnalysis.portfolio_overlap.common_holdings.slice(0, 10).map((holding, index) => (
                <div key={index} className="flex items-center justify-between p-6 bg-slate-700/30 rounded-2xl border border-slate-600/30 hover:border-slate-500/50 transition-all duration-300">
                  <div>
                    <h3 className="font-semibold text-white text-lg">{holding.security_name}</h3>
                    <p className="text-slate-400 mt-1">
                      Found in {holding.funds_count} funds • Avg weight: {holding.average_weight.toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-cyan-400">{holding.funds_count} funds</div>
                    <div className="text-sm text-slate-500 mt-1">
                      {holding.funds.slice(0, 2).join(', ')}
                      {holding.funds.length > 2 && ` +${holding.funds.length - 2} more`}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* AI Analysis */}
      <div className="bg-slate-800/30 backdrop-blur-xl rounded-3xl border border-slate-700/50 shadow-2xl">
        <div className="px-8 py-6 border-b border-slate-700/50 bg-slate-800/50">
          <h2 className="text-xl font-bold text-white flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-orange-400 to-red-500 rounded-lg flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span>Neural Network Insights</span>
            <div className="w-2 h-2 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full animate-pulse"></div>
          </h2>
        </div>
        <div className="p-8">
          <div 
            className="prose prose-invert max-w-none text-slate-300 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: data.ai_analysis }}
          />
        </div>
      </div>
    </div>
  );
};

export default PortfolioAnalysis;