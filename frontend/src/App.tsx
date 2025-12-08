import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api/client';
import { DocumentItem } from './types';
import PreviewPanel from './components/PreviewPanel';
import FileList from './components/FileList';
import StepIndicator from './components/StepIndicator';

type Step = 'scan' | 'classify' | 'review' | 'move';

export default function App() {
  const [currentStep, setCurrentStep] = useState<Step>('scan');
  const [selectedItem, setSelectedItem] = useState<DocumentItem | null>(null);
  const [reviewView, setReviewView] = useState<'ready' | 'needs_review'>('ready');
  const [inputPath, setInputPath] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch items
  const { data: items = [], refetch: refetchItems } = useQuery({
    queryKey: ['items'],
    queryFn: () => apiClient.getItems(),
    enabled: currentStep !== 'scan',
  });

  // Fetch taxonomy
  const { data: taxonomy } = useQuery({
    queryKey: ['taxonomy'],
    queryFn: () => apiClient.getTaxonomy(),
  });

  // Poll classification status
  const { data: classifyStatus } = useQuery({
    queryKey: ['classify-status'],
    queryFn: () => apiClient.getClassifyStatus(),
    refetchInterval: currentStep === 'classify' ? 1000 : false,
    enabled: currentStep === 'classify',
  });

  // Update classification progress
  useEffect(() => {
    if (classifyStatus && !classifyStatus.is_classifying && currentStep === 'classify') {
      setCurrentStep('review');
      refetchItems();
    }
  }, [classifyStatus, currentStep]);

  // Update item mutation
  const updateItemMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: any }) =>
      apiClient.updateItem(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
    },
  });

  // Migrate mutation
  const migrateMutation = useMutation({
    mutationFn: () => apiClient.migrateFiles(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
      alert('Migration started!');
    },
  });

  const handleStartScan = async () => {
    setIsScanning(true);
    try {
      const response = await apiClient.startScan(inputPath);
      setSessionId(response.session_id);
      setCurrentStep('classify');
      // Trigger classification immediately for now (or wait for user?)
      // For this flow, let's assume scan -> classify is automatic or user triggers it.
      // But wait, the API might separate them.
      // Let's trigger classification.
      await apiClient.startClassification(inputPath, response.session_id);
    } catch (error) {
      console.error('Error starting scan:', error);
      alert('Failed to start scan. Please check the input path and try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleBrowse = async () => {
    try {
      const result = await apiClient.browseFolder();
      if (result.success && result.path) {
        setInputPath(result.path);
      } else if (result.error) {
        console.error('Browse error:', result.error);
      }
    } catch (error) {
      console.error('Error browsing:', error);
    }
  };

  const handleItemClick = (item: DocumentItem) => {
    setSelectedItem(item);
  };

  const handleItemUpdate = (id: string, updates: any) => {
    updateItemMutation.mutate({ id, updates });
  };

  const handleMigrate = () => {
    if (confirm('Are you sure you want to move approved files? This cannot be undone.')) {
      migrateMutation.mutate();
    }
  };

  // Filter items based on current step and view
  const filteredItems = items.filter(item => {
    if (currentStep === 'classify') {
      return item.status === 'pending';
    }
    if (currentStep === 'review') {
      if (reviewView === 'needs_review') {
        // Show pending items with low confidence
        return item.status === 'pending' && (item.confidence || 0) < 90;
      }
      // Show approved items OR high confidence pending items
      return item.status === 'approved' || (item.status === 'pending' && (item.confidence || 0) >= 90);
    }
    return true;
  });

  const readyToApprove = items.filter(item => item.status === 'approved' || (item.status === 'pending' && (item.confidence || 0) >= 90));
  const needsReview = items.filter(item => item.status === 'pending' && (item.confidence || 0) < 90);

  const progress = classifyStatus?.progress || 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-slate-900 border-r border-slate-700/50 flex flex-col">
          <div className="p-4 border-b border-slate-700/50">
            <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <span className="text-cyan-500">📂</span> FileOrg
            </h1>
          </div>

          <nav className="flex-1 p-4 space-y-2">
            <StepIndicator
              step={1}
              title="Scan"
              description="Select input folder"
              isActive={currentStep === 'scan'}
              isCompleted={currentStep !== 'scan'}
              onClick={() => setCurrentStep('scan')}
            />
            <StepIndicator
              step={2}
              title="Classify"
              description="AI Analysis"
              isActive={currentStep === 'classify'}
              isCompleted={currentStep === 'review' || currentStep === 'move'}
              onClick={() => setCurrentStep('classify')}
            />
            <StepIndicator
              step={3}
              title="Review"
              description="Verify & Edit"
              isActive={currentStep === 'review'}
              isCompleted={currentStep === 'move'}
              onClick={() => setCurrentStep('review')}
            />
            <StepIndicator
              step={4}
              title="Move"
              description="Execute changes"
              isActive={currentStep === 'move'}
              isCompleted={false}
              onClick={() => setCurrentStep('move')}
            />
          </nav>

          <div className="p-4 border-t border-slate-700/50 space-y-3">
            <a
              href="/taxonomy-editor"
              className="flex items-center gap-2 px-3 py-2 text-sm text-cyan-500 hover:bg-slate-800/50 rounded-lg transition-all hover:text-cyan-400"
            >
              <span>🏷️</span>
              <span className="font-medium">Taxonomy Editor</span>
              <svg className="w-3 h-3 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
            <div className="text-xs text-slate-500">
              Session ID: {sessionId?.substring(0, 8)}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Bar */}
          <div className="h-16 bg-slate-900/50 border-b border-slate-700/50 flex items-center justify-between px-6 backdrop-blur-sm">
            <h2 className="text-lg font-semibold text-slate-100">
              {currentStep === 'scan' && 'Select Input Directory'}
              {currentStep === 'classify' && 'AI Classification'}
              {currentStep === 'review' && 'Review & Approve'}
              {currentStep === 'move' && 'Execute Changes'}
            </h2>
            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-400">
                {items.length} files found
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-auto p-6">
            {currentStep === 'scan' && (
              <div className="max-w-2xl mx-auto bg-slate-800 p-8 rounded-lg border border-slate-700">
                <h3 className="text-lg font-semibold mb-4 text-slate-100">Input Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                      Input Directory
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={inputPath}
                        onChange={(e) => setInputPath(e.target.value)}
                        className="flex-1 p-3 bg-slate-900 border border-slate-600 rounded-lg text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-cyan-500 focus:border-transparent transition-all"
                        placeholder="/path/to/files"
                      />
                      <button
                        onClick={handleBrowse}
                        className="px-4 py-2 bg-slate-700 text-slate-300 rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        Browse
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={handleStartScan}
                    disabled={isScanning || !inputPath}
                    className={`w-full py-3 rounded-lg text-white font-semibold transition-all ${isScanning || !inputPath
                      ? 'bg-slate-700 cursor-not-allowed text-slate-500'
                      : 'bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 shadow-lg shadow-cyan-500/20'
                      }`}
                  >
                    {isScanning ? 'Scanning...' : 'Start Organization'}
                  </button>
                </div>
              </div>
            )}

            {currentStep === 'classify' && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
                <h3 className="text-lg font-semibold text-slate-100">Classifying Files...</h3>
                <p className="text-slate-400 mt-2">AI is analyzing document content</p>
                <div className="mt-8 max-w-md mx-auto bg-slate-700 rounded-full h-2.5">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-cyan-400 h-2.5 rounded-full transition-all duration-500 shadow-lg shadow-cyan-500/50"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-slate-400 mt-2 font-medium">{progress}% Complete</p>
              </div>
            )}

            {currentStep === 'review' && (
              <div className="flex h-full gap-6">
                {/* File List */}
                <div className={`${selectedItem ? 'w-1/2' : 'w-full'} bg-slate-800 rounded-lg border border-slate-700 overflow-hidden flex flex-col`}>
                  <div className="p-4 border-b border-slate-700 bg-slate-900/50 flex justify-between items-center">
                    <h3 className="font-semibold text-slate-100">Files ({filteredItems.length})</h3>
                    <div className="flex gap-2">
                      <div className="flex bg-slate-900 rounded-lg p-1">
                        <button
                          onClick={() => setReviewView('needs_review')}
                          className={`px-3 py-1 text-sm rounded-lg font-medium transition-all ${reviewView === 'needs_review'
                            ? 'bg-slate-700 shadow-lg text-cyan-400'
                            : 'text-slate-400 hover:text-slate-200'
                            }`}
                        >
                          Needs Review ({needsReview.length})
                        </button>
                        <button
                          onClick={() => setReviewView('ready')}
                          className={`px-3 py-1 text-sm rounded-lg font-medium transition-all ${reviewView === 'ready'
                            ? 'bg-slate-700 shadow-lg text-green-400'
                            : 'text-slate-400 hover:text-slate-200'
                            }`}
                        >
                          Ready to Approve ({readyToApprove.length})
                        </button>
                      </div>
                      <button className="text-sm text-cyan-500 hover:text-cyan-400 font-medium transition-colors">
                        Approve All High Confidence
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 overflow-auto">
                    <FileList
                      items={filteredItems}
                      onSelect={handleItemClick}
                      selectedId={selectedItem?.id}
                    />
                  </div>
                </div>

                {/* Preview Panel */}
                {selectedItem && (
                  <div className="w-1/2 bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                    <PreviewPanel
                      item={selectedItem}
                      onUpdate={handleItemUpdate}
                      onClose={() => setSelectedItem(null)}
                      workspaces={taxonomy?.workspaces || []}
                    />
                  </div>
                )}
              </div>
            )}

            {currentStep === 'move' && (
              <div className="max-w-2xl mx-auto text-center py-12">
                <div className="bg-cyan-500/20 rounded-full h-20 w-20 flex items-center justify-center mx-auto mb-6 border border-cyan-500/30">
                  <span className="text-3xl">✅</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-100 mb-2">Ready to Move Files</h3>
                <p className="text-slate-300 mb-8">
                  {items.filter(i => i.status === 'approved').length} files will be moved to their new locations.
                </p>
                <button
                  onClick={handleMigrate}
                  disabled={migrateMutation.isPending}
                  className="px-8 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg font-semibold hover:from-green-600 hover:to-green-700 shadow-lg shadow-green-500/20 disabled:from-slate-700 disabled:to-slate-700 disabled:shadow-none disabled:text-slate-500 transition-all"
                >
                  {migrateMutation.isPending ? 'Moving...' : 'Execute Move'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}



