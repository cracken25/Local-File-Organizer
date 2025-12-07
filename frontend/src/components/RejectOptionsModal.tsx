

interface RejectOptionsModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (action: 'reject' | 'reject_and_move' | 'delete') => void;
    selectedCount: number;
}

export default function RejectOptionsModal({ isOpen, onClose, onConfirm, selectedCount }: RejectOptionsModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
                <h3 className="text-lg font-semibold mb-4">Reject {selectedCount} Files</h3>
                <p className="text-gray-600 mb-6">How would you like to handle these rejected files?</p>

                <div className="space-y-3">
                    <button
                        onClick={() => onConfirm('reject')}
                        className="w-full text-left p-4 border rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 transition-colors group"
                    >
                        <div className="font-medium text-gray-900 group-hover:text-blue-700">Mark as Rejected</div>
                        <div className="text-sm text-gray-500">Keep in list but mark as rejected. Good for later review.</div>
                    </button>

                    <button
                        onClick={() => onConfirm('reject_and_move')}
                        className="w-full text-left p-4 border rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 transition-colors group"
                    >
                        <div className="font-medium text-gray-900 group-hover:text-blue-700">Move to _Rejected Folder</div>
                        <div className="text-sm text-gray-500">Move files to a "_Rejected" folder next to the input directory.</div>
                    </button>

                    <button
                        onClick={() => onConfirm('delete')}
                        className="w-full text-left p-4 border border-red-200 rounded-lg hover:bg-red-50 focus:ring-2 focus:ring-red-500 transition-colors group"
                    >
                        <div className="font-medium text-red-700">Delete Files</div>
                        <div className="text-sm text-red-500">Permanently delete files from disk. This cannot be undone.</div>
                    </button>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:text-gray-800"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}
