import { Workspace } from '../types';

interface BulkActionsProps {
  selectedCount: number;
  onBulkAction: (action: string, workspace?: string) => void;
  workspaces: Workspace[];
}

export default function BulkActions({ selectedCount, onBulkAction }: BulkActionsProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="text-sm text-gray-600">
        {selectedCount > 0 ? (
          <span className="font-medium">{selectedCount} items selected</span>
        ) : (
          <span>No items selected</span>
        )}
      </div>

      {selectedCount > 0 && (
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onBulkAction('approve')}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
          >
            Approve Selected
          </button>
          <button
            onClick={() => onBulkAction('ignore')}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm font-medium"
          >
            Ignore Selected
          </button>
        </div>
      )}
    </div>
  );
}

