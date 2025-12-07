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
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <span className="text-blue-600">📂</span> FileOrg
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

          <div className="p-4 border-t border-gray-200">
            <div className="text-xs text-gray-500">
              Session ID: {sessionId?.substring(0, 8)}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Bar */}
          <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
            <h2 className="text-lg font-semibold text-gray-800">
              {currentStep === 'scan' && 'Select Input Directory'}
              {currentStep === 'classify' && 'AI Classification'}
              {currentStep === 'review' && 'Review & Approve'}
              {currentStep === 'move' && 'Execute Changes'}
            </h2>
            <div className="flex items-center gap-4">
              <div className="text-sm text-gray-600">
                {items.length} files found
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-auto p-6">
            {currentStep === 'scan' && (
              <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-sm border border-gray-200">
                <h3 className="text-lg font-medium mb-4">Input Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Input Directory
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={inputPath}
                        onChange={(e) => setInputPath(e.target.value)}
                        className="flex-1 p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                        placeholder="/path/to/files"
                      />
                      <button
                        onClick={handleBrowse}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                      >
                        Browse
                      </button>
                    </div>
                  </div>
                  <button
                    onClick={handleStartScan}
                    disabled={isScanning || !inputPath}
                    className={`w-full py-3 rounded-lg text-white font-medium ${isScanning || !inputPath
                      ? 'bg-blue-400 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                  >
                    {isScanning ? 'Scanning...' : 'Start Organization'}
                  </button>
                </div>
              </div>
            )}

            {currentStep === 'classify' && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <h3 className="text-lg font-medium text-gray-900">Classifying Files...</h3>
                <p className="text-gray-500 mt-2">AI is analyzing document content</p>
                <div className="mt-8 max-w-md mx-auto bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{progress}% Complete</p>
              </div>
            )}

            {currentStep === 'review' && (
              <div className="flex h-full gap-6">
                {/* File List */}
                <div className={`${selectedItem ? 'w-1/2' : 'w-full'} bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden flex flex-col`}>
                  <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                    <h3 className="font-medium text-gray-700">Files ({filteredItems.length})</h3>
                    <div className="flex gap-2">
                      <div className="flex bg-gray-100 rounded p-1">
                        <button
                          onClick={() => setReviewView('needs_review')}
                          className={`px-3 py-1 text-sm rounded ${reviewView === 'needs_review'
                            ? 'bg-white shadow text-blue-600'
                            : 'text-gray-600 hover:text-gray-900'
                            }`}
                        >
                          Needs Review ({needsReview.length})
                        </button>
                        <button
                          onClick={() => setReviewView('ready')}
                          className={`px-3 py-1 text-sm rounded ${reviewView === 'ready'
                            ? 'bg-white shadow text-green-600'
                            : 'text-gray-600 hover:text-gray-900'
                            }`}
                        >
                          Ready to Approve ({readyToApprove.length})
                        </button>
                      </div>
                      <button className="text-sm text-blue-600 hover:text-blue-800">
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
                  <div className="w-1/2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
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
                <div className="bg-green-100 rounded-full h-20 w-20 flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">✅</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">Ready to Move Files</h3>
                <p className="text-gray-600 mb-8">
                  {items.filter(i => i.status === 'approved').length} files will be moved to their new locations.
                </p>
                <button
                  onClick={handleMigrate}
                  disabled={migrateMutation.isPending}
                  className="px-8 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 shadow-lg disabled:bg-gray-400"
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

