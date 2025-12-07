import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import { apiClient } from './api/client';

// Mock the API client
vi.mock('./api/client', () => ({
    apiClient: {
        getItems: vi.fn(),
        getTaxonomy: vi.fn(),
        getClassifyStatus: vi.fn(),
        updateItem: vi.fn(),
        bulkAction: vi.fn(),
        migrate: vi.fn(),
    },
}));

// Mock child components to simplify testing
vi.mock('./components/FileSelector', () => ({
    default: ({ onScanComplete }: any) => (
        <button onClick={onScanComplete}>Mock FileSelector Scan Complete</button>
    ),
}));

vi.mock('./components/DocumentTable', () => ({
    default: ({ items }: any) => (
        <div data-testid="document-table">
            {items.map((item: any) => (
                <div key={item.id} data-testid={`item-${item.id}`}>
                    {item.name}
                </div>
            ))}
        </div>
    ),
}));

vi.mock('./components/BulkActions', () => ({
    default: () => <div>Mock BulkActions</div>,
}));

vi.mock('./components/PreviewPanel', () => ({
    default: () => <div>Mock PreviewPanel</div>,
}));

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
        },
    },
});

const renderApp = () => {
    render(
        <QueryClientProvider client={queryClient}>
            <App />
        </QueryClientProvider>
    );
};

describe('App Triage View', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Default mocks
        (apiClient.getItems as any).mockResolvedValue([]);
        (apiClient.getTaxonomy as any).mockResolvedValue({ workspaces: [] });
        (apiClient.getClassifyStatus as any).mockResolvedValue({ is_classifying: false, progress: 100 });
    });

    it('renders Triage View tabs in Review step', async () => {
        // Setup items for triage
        const mockItems = [
            { id: '1', name: 'High Conf', confidence: 0.9, status: 'pending' },
            { id: '2', name: 'Low Conf', confidence: 0.5, status: 'pending' },
            { id: '3', name: 'Approved', confidence: 0.9, status: 'approved' },
        ];
        (apiClient.getItems as any).mockResolvedValue(mockItems);

        renderApp();

        // Navigate to Review step (simulate scan complete)
        fireEvent.click(screen.getByText('Mock FileSelector Scan Complete'));

        // Wait for items to load and tabs to appear
        await waitFor(() => {
            expect(screen.getByText(/Ready to Approve/)).toBeInTheDocument();
            expect(screen.getByText(/Needs Review/)).toBeInTheDocument();
        });

        // Check counts
        expect(screen.getByText('Ready to Approve (1)')).toBeInTheDocument();
        expect(screen.getByText('Needs Review (1)')).toBeInTheDocument();

        // Verify "High Conf" is shown by default (Ready tab)
        expect(screen.getByTestId('item-1')).toBeInTheDocument();
        expect(screen.queryByTestId('item-2')).not.toBeInTheDocument();

        // Switch to "Needs Review" tab
        fireEvent.click(screen.getByText(/Needs Review/));

        // Verify "Low Conf" is shown
        expect(screen.getByTestId('item-2')).toBeInTheDocument();
        expect(screen.queryByTestId('item-1')).not.toBeInTheDocument();
    });
});
