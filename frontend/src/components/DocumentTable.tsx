import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
} from '@tanstack/react-table';
import { DocumentItem } from '../types';
import ConfidenceIndicator from './ConfidenceIndicator';

interface DocumentTableProps {
  items: DocumentItem[];
  selectedIds: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
  onItemClick: (item: DocumentItem) => void;
  onItemUpdate: (id: string, updates: any) => void;
  loading?: boolean;
}

const columnHelper = createColumnHelper<DocumentItem>();

export default function DocumentTable({
  items,
  selectedIds,
  onSelectionChange,
  onItemClick,
  loading
}: DocumentTableProps) {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: 'confidence', desc: false } // Start with lowest confidence first
  ]);

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: 'select',
        header: ({ table }) => (
          <input
            type="checkbox"
            checked={table.getIsAllRowsSelected()}
            onChange={table.getToggleAllRowsSelectedHandler()}
            className="rounded"
          />
        ),
        cell: ({ row }) => (
          <input
            type="checkbox"
            checked={selectedIds.has(row.original.id)}
            onChange={(e) => {
              const newSelected = new Set(selectedIds);
              if (e.target.checked) {
                newSelected.add(row.original.id);
              } else {
                newSelected.delete(row.original.id);
              }
              onSelectionChange(newSelected);
            }}
            className="rounded"
          />
        ),
      }),
      columnHelper.accessor('original_filename', {
        header: 'ORIGINAL FILE',
        cell: (info) => (
          <div className="max-w-xs truncate" title={info.row.original.source_path}>
            {info.getValue()}
          </div>
        ),
      }),
      columnHelper.accessor('proposed_workspace', {
        header: 'WORKSPACE',
        cell: (info) => (
          <div className="text-sm font-mono text-blue-600">
            {info.getValue()}
          </div>
        ),
      }),
      columnHelper.accessor('proposed_subpath', {
        header: 'SUBPATH',
        cell: (info) => (
          <div className="text-sm text-gray-600">
            {info.getValue() || '-'}
          </div>
        ),
      }),
      columnHelper.accessor('proposed_filename', {
        header: 'NEW FILENAME',
        cell: (info) => (
          <div className="text-sm max-w-xs truncate" title={info.getValue()}>
            {info.getValue()}
          </div>
        ),
      }),
      columnHelper.accessor('confidence', {
        header: 'CONFIDENCE',
        cell: (info) => <ConfidenceIndicator confidence={info.getValue()} />,
      }),
    ],
    [selectedIds, onSelectionChange]
  );

  const table = useReactTable({
    data: items,
    columns,
    state: {
      sorting,
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  if (loading) {
    return (
      <div className="p-8 text-center text-gray-500">
        Loading...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        No documents to display. Start by scanning a directory.
      </div>
    );
  }

  return (
    <div className="overflow-auto max-h-[600px]">
      <table className="w-full">
        <thead className="bg-gray-50 sticky top-0 z-10">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={header.column.getToggleSortingHandler()}
                >
                  <div className="flex items-center space-x-1">
                    <span>
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </span>
                    {header.column.getIsSorted() && (
                      <span>
                        {header.column.getIsSorted() === 'asc' ? ' ▲' : ' ▼'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              onClick={() => onItemClick(row.original)}
              className={`hover:bg-gray-50 cursor-pointer ${
                selectedIds.has(row.original.id) ? 'bg-blue-50' : ''
              }`}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3 text-sm">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}





