import React from 'react';
import { Brain, Zap, Sparkles } from 'lucide-react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-slate-900/80 backdrop-blur-xl flex items-center justify-center z-50">
      <div className="bg-slate-800/90 backdrop-blur-xl rounded-3xl p-12 flex flex-col items-center space-y-8 border border-slate-700/50 shadow-2xl">
        <div className="relative">
          <div className="w-20 h-20 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 rounded-3xl flex items-center justify-center animate-pulse shadow-2xl shadow-cyan-500/25">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <div className="absolute -top-2 -right-2 w-6 h-6 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full flex items-center justify-center animate-spin">
            <Zap className="w-3 h-3 text-white" />
          </div>
          <div className="absolute -bottom-2 -left-2 w-6 h-6 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center animate-bounce">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
        </div>
        <div className="text-center">
          <h3 className="text-2xl font-bold text-white mb-2">AI Processing...</h3>
          <p className="text-slate-400 text-lg">Neural networks analyzing your portfolio data</p>
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-100"></div>
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-200"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;