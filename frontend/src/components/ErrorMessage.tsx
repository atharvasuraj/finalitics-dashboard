import React from 'react';
import { AlertCircle, X, Zap } from 'lucide-react';

interface ErrorMessageProps {
  message: string;
  onDismiss: () => void;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ message, onDismiss }) => {
  return (
    <div className="bg-red-500/10 backdrop-blur-xl border border-red-500/30 rounded-2xl p-6 flex items-start space-x-4 shadow-2xl">
      <div className="w-10 h-10 bg-gradient-to-r from-red-400 to-pink-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg">
        <AlertCircle className="w-5 h-5 text-white" />
      </div>
      <div className="flex-1">
        <h3 className="text-lg font-bold text-red-300 mb-2">System Alert</h3>
        <p className="text-red-200 leading-relaxed">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        className="w-8 h-8 bg-slate-700 hover:bg-slate-600 rounded-lg flex items-center justify-center transition-colors duration-200 text-slate-400 hover:text-white"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};

export default ErrorMessage;