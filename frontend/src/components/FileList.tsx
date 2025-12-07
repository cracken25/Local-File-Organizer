import { DocumentItem } from '../types';
import ConfidenceIndicator from './ConfidenceIndicator';

interface FileListProps {
    items: DocumentItem[];
    onSelect: (item: DocumentItem) => void;
    selectedId?: string;
}

export default function FileList({ items, onSelect, selectedId }: FileListProps) {
    if (items.length === 0) {
        return (
            <div className="p-8 text-center text-gray-500">
                No files found.
            </div>
        );
    }

    return (
        <div className="divide-y divide-gray-200">
            {items.map((item) => (
                <div
                    key={item.id}
                    onClick={() => onSelect(item)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${selectedId === item.id ? 'bg-blue-50 hover:bg-blue-50' : ''
                        }`}
                >
                    <div className="flex justify-between items-start mb-1">
                        <div className="font-medium text-gray-900 truncate pr-4">
                            {item.original_filename}
                        </div>
                        <ConfidenceIndicator confidence={item.confidence || 0} />
                    </div>

                    <div className="flex justify-between items-center text-sm">
                        <div className="text-gray-500 truncate max-w-[200px]">
                            {item.proposed_workspace} / {item.proposed_subpath}
                        </div>
                        <div className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${item.status === 'approved' ? 'bg-green-100 text-green-800' :
                                item.status === 'ignored' ? 'bg-gray-100 text-gray-800' :
                                    item.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                        'bg-yellow-100 text-yellow-800'
                            }`}>
                            {item.status}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
