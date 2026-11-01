import React, { useCallback, useState } from 'react';
import { Upload, FileText, AlertCircle, Zap, Brain } from 'lucide-react';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
  compact?: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, compact = false }) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    const maxSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['application/json', 'text/csv', 'application/vnd.ms-excel'];
    
    if (file.size > maxSize) {
      return 'File size must be less than 16MB';
    }
    
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv')) {
      return 'Only JSON and CSV files are supported';
    }
    
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }
    
    setError(null);
    onFileUpload(file);
  }, [onFileUpload]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  }, [handleFile]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  }, [handleFile]);

  if (compact) {
    return (
      <div className="relative">
        <input
          type="file"
          id="file-upload-compact"
          className="sr-only"
          onChange={handleChange}
          accept=".json,.csv"
        />
        <label
          htmlFor="file-upload-compact"
          className="group flex items-center space-x-3 px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-xl hover:from-cyan-400 hover:to-blue-500 transition-all duration-300 cursor-pointer shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-105"
        >
          <Upload className="w-5 h-5" />
          <span className="font-semibold">Upload New Data</span>
        </label>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div
        className={`relative border-2 border-dashed rounded-3xl p-12 text-center transition-all duration-300 ${
          dragActive
            ? 'border-cyan-400 bg-cyan-500/10 shadow-2xl shadow-cyan-500/20'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/20'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          id="file-upload"
          className="sr-only"
          onChange={handleChange}
          accept=".json,.csv"
        />
        
        <div className="space-y-6">
          <div className="relative">
            <div className="w-20 h-20 bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-500 rounded-3xl flex items-center justify-center mx-auto shadow-2xl shadow-cyan-500/25">
              <Upload className="w-10 h-10 text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-6 h-6 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
              <Brain className="w-3 h-3 text-white" />
            </div>
          </div>
          
          <div>
            <h3 className="text-2xl font-bold text-white mb-4">
              Upload Portfolio Data for AI Analysis
            </h3>
            <p className="text-slate-400 mb-8 text-lg">
              Drag and drop your file here, or click to browse and unleash the power of AI
            </p>
            <label
              htmlFor="file-upload"
              className="group inline-flex items-center px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-2xl hover:from-cyan-400 hover:to-blue-500 transition-all duration-300 cursor-pointer font-bold shadow-2xl shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-105"
            >
              <FileText className="w-5 h-5 mr-3" />
              Choose File for AI Processing
            </label>
          </div>
          
          <div className="flex items-center justify-center space-x-8 text-sm text-slate-500">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <span>JSON & CSV supported</span>
            </div>
            <div className="flex items-center space-x-2">
              <Brain className="w-4 h-4 text-purple-400" />
              <span>Up to 16MB</span>
            </div>
          </div>
        </div>
      </div>
      
      {error && (
        <div className="mt-6 p-6 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center space-x-3 backdrop-blur-xl">
          <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
          <span className="text-red-300 font-medium">{error}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;