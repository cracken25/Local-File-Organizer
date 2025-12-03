import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './api/client';
import { DocumentItem } from './types';
import FileSelector from './components/FileSelector';
import DocumentTable from './components/DocumentTable';
import PreviewPanel from './components/PreviewPanel';
import BulkActions from './components/BulkActions';

type Step = 'scan' | 'classify' | 'review' | 'migrate';

export default function App() {
  const [currentStep, setCurrentStep] = useState<Step>('scan');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedItem, setSelectedItem] = useState<DocumentItem | null>(null);
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

  // Bulk action mutation
  const bulkActionMutation = useMutation({
    mutationFn: apiClient.bulkAction.bind(apiClient),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['items'] });
      setSelectedIds(new Set());
    },
  });

  // Migrate mutation
  const migrateMutation = useMutation({
    mutationFn: apiClient.migrate.bind(apiClient),
    onSuccess: (data: any) => {
      alert(`Successfully migrated ${data.migrated} files!`);
      queryClient.invalidateQueries({ queryKey: ['items'] });
      setCurrentStep('scan');
    },
  });

  const handleScanComplete = () => {
    setCurrentStep('classify');
  };

  const handleClassifyStart = () => {
    // Classification starts automatically after scan
  };

  const handleItemClick = (item: DocumentItem) => {
    console.log('Item clicked:', item);
    setSelectedItem(item);
  };

  const handleItemUpdate = (id: string, updates: any) => {
    updateItemMutation.mutate({ id, updates });
  };

  const handleBulkAction = (action: string, workspace?: string) => {
    bulkActionMutation.mutate({
      item_ids: Array.from(selectedIds),
      action: action as any,
      workspace,
    });
  };

  const handleMigrate = () => {
    const approvedCount = items.filter((item) => item.status === 'approved').length;
    if (approvedCount === 0) {
      alert('No approved files to migrate. Please approve some files first.');
      return;
    }
    if (confirm(`Migrate ${approvedCount} approved files?`)) {
      migrateMutation.mutate({});
    }
  };

  const steps = [
    { id: 'scan', label: '1. Scan', active: currentStep === 'scan' },
    { id: 'classify', label: '2. Classify', active: currentStep === 'classify' },
    { id: 'review', label: '3. Review', active: currentStep === 'review' },
    { id: 'migrate', label: '4. Migrate', active: currentStep === 'migrate' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">File Organizer</h1>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex space-x-2">
          {steps.map((step) => (
            <button
              key={step.id}
              className={`px-4 py-2 rounded-md font-medium ${
                step.active
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {step.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 pb-8">
        {/* Step 1: Scan */}
        {currentStep === 'scan' && (
          <div className="bg-white rounded-lg shadow p-6">
            <FileSelector
              onScanComplete={handleScanComplete}
              onClassifyStart={handleClassifyStart}
            />
          </div>
        )}

        {/* Step 2: Classify */}
        {currentStep === 'classify' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Classifying Files...</h2>
            <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                style={{ width: `${classifyStatus?.progress || 0}%` }}
              />
            </div>
            <p className="text-sm text-gray-600">
              Progress: {classifyStatus?.progress || 0}%
            </p>
          </div>
        )}

        {/* Step 3: Review */}
        {currentStep === 'review' && (
          <div className="space-y-4">
            {/* Bulk Actions */}
            <div className="bg-white rounded-lg shadow p-4">
              <BulkActions
                selectedCount={selectedIds.size}
                onBulkAction={handleBulkAction}
                workspaces={taxonomy?.workspaces || []}
              />
            </div>

            {/* Table and Preview */}
            <div className="grid grid-cols-3 gap-4">
              <div className="col-span-2 bg-white rounded-lg shadow">
                <DocumentTable
                  items={items}
                  selectedIds={selectedIds}
                  onSelectionChange={setSelectedIds}
                  onItemClick={handleItemClick}
                  onItemUpdate={handleItemUpdate}
                />
              </div>
              <div className="bg-white rounded-lg shadow">
                <PreviewPanel
                  item={selectedItem}
                  onUpdate={(updates) => {
                    if (selectedItem) {
                      handleItemUpdate(selectedItem.id, updates);
                    }
                  }}
                  onClose={() => setSelectedItem(null)}
                  workspaces={taxonomy?.workspaces || []}
                />
              </div>
            </div>

            {/* Migrate Button */}
            <div className="bg-white rounded-lg shadow p-4">
              <button
                onClick={handleMigrate}
                disabled={migrateMutation.isPending}
                className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium text-lg"
              >
                {migrateMutation.isPending
                  ? 'Migrating...'
                  : `Migrate ${items.filter((i) => i.status === 'approved').length} Approved Files`}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

