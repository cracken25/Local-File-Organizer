import React, { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../api/client';

interface FileSelectorProps {
  onScanComplete: () => void;
  onClassifyStart: () => void;
}

export default function FileSelector({ onScanComplete, onClassifyStart }: FileSelectorProps) {
  const [inputPath, setInputPath] = useState('');
  const [outputPath, setOutputPath] = useState('');
  const [mode, setMode] = useState<'content' | 'date' | 'type'>('content');
  
  // Refs to directly access input elements
  const inputRef = useRef<HTMLInputElement>(null);
  const outputRef = useRef<HTMLInputElement>(null);

  // Load saved paths from API on mount
  useEffect(() => {
    console.log('=== LOADING SAVED PATHS FROM SERVER ===');
    
    const loadSavedPaths = async () => {
      try {
        const savedPaths = await apiClient.getSavedPaths();
        console.log('Retrieved saved paths:', savedPaths);
        
        if (savedPaths.input_path) {
          console.log('Setting inputPath to:', savedPaths.input_path);
          setInputPath(savedPaths.input_path);
          if (inputRef.current) {
            inputRef.current.value = savedPaths.input_path;
          }
        }
        
        if (savedPaths.output_path) {
          console.log('Setting outputPath to:', savedPaths.output_path);
          setOutputPath(savedPaths.output_path);
          if (outputRef.current) {
            outputRef.current.value = savedPaths.output_path;
          }
        }
        
        if (savedPaths.mode && (savedPaths.mode === 'content' || savedPaths.mode === 'date' || savedPaths.mode === 'type')) {
          console.log('Setting mode to:', savedPaths.mode);
          setMode(savedPaths.mode as 'content' | 'date' | 'type');
        }
        
        console.log('=== FINISHED LOADING PATHS ===');
      } catch (error) {
        console.error('Error loading saved paths:', error);
      }
    };
    
    loadSavedPaths();
  }, []);

  // Save paths to server whenever they change
  useEffect(() => {
    console.log('inputPath state changed to:', inputPath);
    if (inputPath) {
      apiClient.savePaths({ input_path: inputPath }).catch(err => 
        console.error('Error saving input path:', err)
      );
    }
    // Also directly set the input value
    if (inputRef.current) {
      inputRef.current.value = inputPath;
    }
  }, [inputPath]);

  useEffect(() => {
    console.log('outputPath state changed to:', outputPath);
    if (outputPath) {
      apiClient.savePaths({ output_path: outputPath }).catch(err =>
        console.error('Error saving output path:', err)
      );
    }
    // Also directly set the output value
    if (outputRef.current) {
      outputRef.current.value = outputPath;
    }
  }, [outputPath]);

  useEffect(() => {
    console.log('mode changed to:', mode);
    if (mode) {
      apiClient.savePaths({ mode }).catch(err =>
        console.error('Error saving mode:', err)
      );
    }
  }, [mode]);

  const handleBrowseInput = async () => {
    console.log('Browse input clicked');
    console.log('Current inputPath state:', inputPath);
    try {
      // Check if PyWebView API is available
      if (window.pywebview?.api?.select_folder) {
        console.log('Calling select_folder...');
        const path = await window.pywebview.api.select_folder('Select Input Directory');
        console.log('Returned path:', path, 'Type:', typeof path);
        if (path && path !== null && path !== 'null' && path !== '') {
          console.log('Setting input path to:', path);
          setInputPath(path);
        } else {
          console.log('No valid path selected (got:', path, ')');
        }
      } else {
        console.error('PyWebView API not available');
        alert('Folder picker not available. Please enter path manually or ensure you\'re running the desktop app.');
      }
    } catch (error) {
      console.error('Browse error:', error);
      alert('Error opening folder picker. Please enter path manually.');
    }
  };

  const handleBrowseOutput = async () => {
    console.log('Browse output clicked');
    console.log('Current outputPath state:', outputPath);
    try {
      // Check if PyWebView API is available
      if (window.pywebview?.api?.select_folder) {
        console.log('Calling select_folder...');
        const path = await window.pywebview.api.select_folder('Select Output Directory');
        console.log('Returned path:', path, 'Type:', typeof path);
        if (path && path !== null && path !== 'null' && path !== '') {
          console.log('Setting output path to:', path);
          setOutputPath(path);
        } else {
          console.log('No valid path selected (got:', path, ')');
        }
      } else {
        console.error('PyWebView API not available');
        alert('Folder picker not available. Please enter path manually or ensure you\'re running the desktop app.');
      }
    } catch (error) {
      console.error('Browse error:', error);
      alert('Error opening folder picker. Please enter path manually.');
    }
  };

  const scanMutation = useMutation({
    mutationFn: apiClient.scan.bind(apiClient),
    onSuccess: () => {
      onScanComplete();
      // Automatically start classification
      classifyMutation.mutate({ mode });
    },
  });

  const classifyMutation = useMutation({
    mutationFn: apiClient.classify.bind(apiClient),
    onSuccess: () => {
      onClassifyStart();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputPath) {
      scanMutation.mutate({ input_path: inputPath, output_path: outputPath || undefined });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Input Directory
        </label>
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="/path/to/your/files"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            style={{ color: '#000', backgroundColor: '#fff' }}
            required
          />
          <button
            type="button"
            onClick={handleBrowseInput}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
          >
            Browse...
          </button>
        </div>
        {inputPath && (
          <p className="mt-1 text-xs text-green-600 font-mono">
            Selected: {inputPath}
          </p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          Click Browse to select a folder, or enter the full path
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Output Directory (optional)
        </label>
        <div className="flex space-x-2">
          <input
            ref={outputRef}
            type="text"
            value={outputPath}
            onChange={(e) => setOutputPath(e.target.value)}
            placeholder="/path/to/output (default: organized_folder)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            style={{ color: '#000', backgroundColor: '#fff' }}
          />
          <button
            type="button"
            onClick={handleBrowseOutput}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium"
          >
            Browse...
          </button>
        </div>
        {outputPath && (
          <p className="mt-1 text-xs text-green-600 font-mono">
            Selected: {outputPath}
          </p>
        )}
        <p className="mt-1 text-sm text-gray-500">
          Click Browse to select a folder, or leave empty for default
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Classification Mode
        </label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="radio"
              value="content"
              checked={mode === 'content'}
              onChange={() => setMode('content')}
              className="mr-2"
            />
            <span className="text-sm">
              <strong>By Content</strong> - AI-powered taxonomy classification (recommended)
            </span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="date"
              checked={mode === 'date'}
              onChange={() => setMode('date')}
              className="mr-2"
            />
            <span className="text-sm">
              <strong>By Date</strong> - Organize by modification date
            </span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="type"
              checked={mode === 'type'}
              onChange={() => setMode('type')}
              className="mr-2"
            />
            <span className="text-sm">
              <strong>By Type</strong> - Organize by file extension
            </span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={scanMutation.isPending || !inputPath}
        className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium text-lg"
      >
        {scanMutation.isPending ? 'Processing...' : 'Start Organization'}
      </button>

      {scanMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          Error: {scanMutation.error.message}
        </div>
      )}
    </form>
  );
}

// Declare window.pywebview for TypeScript
declare global {
  interface Window {
    pywebview?: {
      api: {
        select_folder: (title: string) => Promise<string | null>;
      };
    };
  }
}

