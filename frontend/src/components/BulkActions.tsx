import { useState } from 'react';
import { Workspace } from '../types';
import RejectOptionsModal from './RejectOptionsModal';

interface BulkActionsProps {
  selectedCount: number;
  onBulkAction: (action: string, workspace?: string) => void;
  workspaces: Workspace[];
}

export default function BulkActions({ selectedCount, onBulkAction }: BulkActionsProps) {
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);

  const handleBulkAction = (action: string) => {
    if (action === 'reject') {
      setIsRejectModalOpen(true);
    } else {
      onBulkAction(action);
    }
  };

  const handleRejectConfirm = (action: 'reject' | 'reject_and_move' | 'delete') => {
    onBulkAction(action);
    setIsRejectModalOpen(false);
  };

  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-gray-600">
        <span className="font-medium">{selectedCount} items selected</span>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={() => onBulkAction('approve')}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
        >
          Approve Selected
        </button>
        <button
          onClick={() => handleBulkAction('reject')}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 text-sm font-medium"
        >
          Reject ({selectedCount})
        </button>
        <button
          onClick={() => handleBulkAction('ignore')}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm font-medium"
        >
          Ignore Selected
        </button>
      </div>

      <RejectOptionsModal
        isOpen={isRejectModalOpen}
        onClose={() => setIsRejectModalOpen(false)}
        onConfirm={handleRejectConfirm}
        selectedCount={selectedCount}
      />
    </div>
  );
}
