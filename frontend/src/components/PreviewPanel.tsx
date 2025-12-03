import { useState, useEffect } from 'react';
import { DocumentItem, Workspace } from '../types';
import ConfidenceIndicator from './ConfidenceIndicator';

interface PreviewPanelProps {
  item: DocumentItem | null;
  onUpdate: (updates: any) => void;
  onClose: () => void;
  workspaces: Workspace[];
}

export default function PreviewPanel({ item, onUpdate, onClose }: PreviewPanelProps) {
  const [workspace, setWorkspace] = useState('');
  const [subpath, setSubpath] = useState('');
  const [filename, setFilename] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    console.log('PreviewPanel received item:', item);
    if (item) {
      console.log('Setting fields:', {
        workspace: item.proposed_workspace,
        subpath: item.proposed_subpath,
        filename: item.proposed_filename
      });
      setWorkspace(item.proposed_workspace || '');
      setSubpath(item.proposed_subpath || '');
      setFilename(item.proposed_filename || '');
      setStatus(item.status || 'pending');
    }
  }, [item]);

  if (!item) {
    return (
      <div className="p-6 text-center text-gray-500">
        Select an item to view details
      </div>
    );
  }

  const hasChanges = 
    workspace !== (item.proposed_workspace || '') ||
    subpath !== (item.proposed_subpath || '') ||
    filename !== (item.proposed_filename || '') ||
    status !== (item.status || 'pending');

  const handleSave = () => {
    onUpdate({
      proposed_workspace: workspace,
      proposed_subpath: subpath,
      proposed_filename: filename,
      status: status,
    });
  };

  const handleReset = () => {
    setWorkspace(item.proposed_workspace || '');
    setSubpath(item.proposed_subpath || '');
    setFilename(item.proposed_filename || '');
    setStatus(item.status || 'pending');
  };

  const handleApprove = () => {
    onUpdate({ status: 'approved' });
  };

  const handleIgnore = () => {
    onUpdate({ status: 'ignored' });
  };

  return (
    <div className="p-4 max-h-[600px] overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">File Details</h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>

      <div className="space-y-4">
        {/* Original Info */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Original Path
          </label>
          <div className="text-sm text-gray-600 break-all bg-gray-50 p-2 rounded">
            {item.source_path}
          </div>
        </div>

        {/* File Metadata */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-600">Size:</span>{' '}
            <span className="font-medium">
              {item.file_size ? `${(item.file_size / 1024).toFixed(1)} KB` : 'N/A'}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Type:</span>{' '}
            <span className="font-medium">{item.file_extension || 'N/A'}</span>
          </div>
        </div>

        {/* Confidence */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Confidence
          </label>
          <ConfidenceIndicator confidence={item.confidence || 0} />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded max-h-48 overflow-y-auto whitespace-pre-wrap">
            {item.description || 'No description available'}
          </div>
        </div>

        {/* Editable Fields */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-semibold mb-3">Classification</h4>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Workspace
              </label>
              <input
                type="text"
                value={workspace}
                onChange={(e) => setWorkspace(e.target.value)}
                placeholder="e.g., Finance"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subpath
              </label>
              <input
                type="text"
                value={subpath}
                onChange={(e) => setSubpath(e.target.value)}
                placeholder="e.g., Income/Paystubs"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filename
              </label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              />
              <div className="mt-1 text-xs text-gray-500">
                Extension: {item.file_extension || 'unknown'}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="ignored">Ignored</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="border-t pt-4 space-y-2">
          {hasChanges && (
            <div className="flex space-x-2">
              <button
                onClick={handleSave}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
              >
                Save Changes
              </button>
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 text-sm font-medium"
              >
                Reset
              </button>
            </div>
          )}
          
          <div className="flex space-x-2">
            <button
              onClick={handleApprove}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
            >
              Approve
            </button>
            <button
              onClick={handleIgnore}
              className="flex-1 px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm font-medium"
            >
              Ignore
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

