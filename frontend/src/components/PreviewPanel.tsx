import { useState, useEffect } from 'react';
import { DocumentItem, Taxonomy, Workspace } from '../types';
import { API_BASE_URL } from '../config';
import ConfidenceIndicator from './ConfidenceIndicator';
import { X } from 'lucide-react';

interface PreviewPanelProps {
  item: DocumentItem | null;
  onUpdate: (id: string, updates: any) => void;
  onClose: () => void;
  workspaces: Workspace[];
}

export default function PreviewPanel({ item, onUpdate, onClose }: PreviewPanelProps) {
  const [proposedWorkspace, setProposedWorkspace] = useState('');
  const [proposedSubpath, setProposedSubpath] = useState('');
  const [proposedFilename, setProposedFilename] = useState('');
  const [status, setStatus] = useState('');
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [taxonomy, setTaxonomy] = useState<Taxonomy | null>(null);
  const [isLoadingTaxonomy, setIsLoadingTaxonomy] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'metadata' | 'debug'>('preview');

  useEffect(() => {
    if (item) {
      setProposedWorkspace(item.proposed_workspace || '');
      setProposedSubpath(item.proposed_subpath || '');
      setProposedFilename(item.proposed_filename || '');
      setStatus(item.status || 'pending');
      setReviewerNotes(item.reviewer_notes || '');
    }
  }, [item]);

  useEffect(() => {
    const fetchTaxonomy = async () => {
      setIsLoadingTaxonomy(true);
      try {
        const response = await fetch(`${API_BASE_URL}/taxonomy`);
        if (response.ok) {
          const data = await response.json();
          setTaxonomy(data);
        }
      } catch (error) {
        console.error('Error fetching taxonomy:', error);
      } finally {
        setIsLoadingTaxonomy(false);
      }
    };

    fetchTaxonomy();
  }, []);

  if (!item) {
    return (
      <div className="p-6 text-center text-gray-500">
        Select an item to view details
      </div>
    );
  }

  const hasChanges =
    proposedWorkspace !== (item.proposed_workspace || '') ||
    proposedSubpath !== (item.proposed_subpath || '') ||
    proposedFilename !== (item.proposed_filename || '') ||
    status !== (item.status || 'pending') ||
    reviewerNotes !== (item.reviewer_notes || '');

  const handleSave = () => {
    onUpdate(item.id, {
      proposed_workspace: proposedWorkspace,
      proposed_subpath: proposedSubpath,
      proposed_filename: proposedFilename,
      status: status,
      reviewer_notes: reviewerNotes,
    });
  };

  const handleReset = () => {
    setProposedWorkspace(item.proposed_workspace || '');
    setProposedSubpath(item.proposed_subpath || '');
    setProposedFilename(item.proposed_filename || '');
    setStatus(item.status || 'pending');
    setReviewerNotes(item.reviewer_notes || '');
  };

  const handleApprove = () => {
    onUpdate(item.id, { status: 'approved' });
  };

  const handleIgnore = () => {
    onUpdate(item.id, { status: 'ignored' });
  };

  return (
    <div className="h-full flex flex-col bg-white border-l border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
        <h3 className="font-semibold text-gray-800">File Preview</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          <X size={20} />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button
          className={`flex-1 py-3 text-sm font-medium ${activeTab === 'preview'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
          onClick={() => setActiveTab('preview')}
        >
          Preview
        </button>
        <button
          className={`flex-1 py-3 text-sm font-medium ${activeTab === 'metadata'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
          onClick={() => setActiveTab('metadata')}
        >
          Metadata
        </button>
        <button
          className={`flex-1 py-3 text-sm font-medium ${activeTab === 'debug'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
            }`}
          onClick={() => setActiveTab('debug')}
        >
          AI Debug
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'preview' ? (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 min-h-[200px] whitespace-pre-wrap font-mono text-sm text-gray-700">
              {item.extracted_text || 'No text extracted'}
            </div>
          </div>
        ) : activeTab === 'metadata' ? (
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
              <div className="col-span-2">
                <span className="text-gray-600">SHA256:</span>{' '}
                <span className="font-mono text-xs text-gray-500">
                  {item.sha256 ? item.sha256.substring(0, 16) + '...' : 'N/A'}
                </span>
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
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Workspace
                  </label>
                  {isLoadingTaxonomy ? (
                    <div className="text-sm text-gray-500">Loading taxonomy...</div>
                  ) : taxonomy ? (
                    <div className="relative">
                      <select
                        value={proposedWorkspace}
                        onChange={(e) => {
                          if (e.target.value === 'PROPOSE_NEW') {
                            alert("Category Proposal Workflow:\n\n1. Identify the cluster\n2. Draft definition\n3. Map to Domain\n4. Check neighbors\n5. Size check (>10 items)\n6. Name cleanly\n\n(Full workflow UI coming in Iteration 2)");
                            return;
                          }
                          setProposedWorkspace(e.target.value);
                        }}
                        className="w-full p-2 border border-gray-300 rounded focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option value="">Select a workspace...</option>
                        {taxonomy.workspaces.map((ws: Workspace) => (
                          <option key={ws.id} value={ws.id}>
                            {ws.id}
                          </option>
                        ))}
                        <option disabled>──────────</option>
                        <option value="PROPOSE_NEW">➕ Propose New Category...</option>
                      </select>
                      {proposedWorkspace && (
                        <p className="mt-1 text-xs text-gray-500">
                          {taxonomy.workspaces.find(ws => ws.id === proposedWorkspace)?.description}
                        </p>
                      )}
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={proposedWorkspace}
                      onChange={(e) => setProposedWorkspace(e.target.value)}
                      className="w-full p-2 border border-gray-300 rounded"
                    />
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Subpath
                  </label>
                  <input
                    type="text"
                    value={proposedSubpath}
                    onChange={(e) => setProposedSubpath(e.target.value)}
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
                    value={proposedFilename}
                    onChange={(e) => setProposedFilename(e.target.value)}
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

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reviewer Notes
                  </label>
                  <textarea
                    value={reviewerNotes}
                    onChange={(e) => setReviewerNotes(e.target.value)}
                    placeholder="Add notes about this classification..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 h-20"
                  />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                AI Reasoning
              </label>
              <div className="text-sm text-gray-800 bg-blue-50 p-3 rounded border border-blue-100">
                {item.description || 'No reasoning provided'}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                System Prompt
              </label>
              <div className="text-xs font-mono text-gray-600 bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap max-h-60 overflow-y-auto">
                {item.ai_prompt || 'No prompt recorded'}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 uppercase mb-1">
                Raw Response
              </label>
              <div className="text-xs font-mono text-gray-600 bg-gray-50 p-3 rounded border border-gray-200 whitespace-pre-wrap">
                {item.ai_response || 'No response recorded'}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
        {hasChanges && (
          <>
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Reset
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 shadow-sm"
            >
              Save Changes
            </button>
          </>
        )}
        {!hasChanges && (
          <>
            <button
              onClick={handleIgnore}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Ignore
            </button>
            <button
              onClick={handleApprove}
              className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 shadow-sm"
            >
              Approve
            </button>
          </>
        )}
      </div>
    </div>
  );
}
