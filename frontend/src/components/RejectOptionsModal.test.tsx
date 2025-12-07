import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import RejectOptionsModal from './RejectOptionsModal';

describe('RejectOptionsModal', () => {
    it('renders correctly when open', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={true}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={5}
            />
        );

        expect(screen.getByText('Reject 5 Files')).toBeInTheDocument();
        expect(screen.getByText('Mark as Rejected')).toBeInTheDocument();
        expect(screen.getByText('Move to _Rejected Folder')).toBeInTheDocument();
        expect(screen.getByText('Delete Files')).toBeInTheDocument();
    });

    it('does not render when closed', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={false}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={5}
            />
        );

        expect(screen.queryByText('Reject 5 Files')).not.toBeInTheDocument();
    });

    it('calls onConfirm with correct action when "Mark as Rejected" is clicked', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={true}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={1}
            />
        );

        fireEvent.click(screen.getByText('Mark as Rejected'));
        expect(onConfirm).toHaveBeenCalledWith('reject');
    });

    it('calls onConfirm with correct action when "Move to _Rejected Folder" is clicked', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={true}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={1}
            />
        );

        fireEvent.click(screen.getByText('Move to _Rejected Folder'));
        expect(onConfirm).toHaveBeenCalledWith('reject_and_move');
    });

    it('calls onConfirm with correct action when "Delete Files" is clicked', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={true}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={1}
            />
        );

        fireEvent.click(screen.getByText('Delete Files'));
        expect(onConfirm).toHaveBeenCalledWith('delete');
    });

    it('calls onClose when Cancel is clicked', () => {
        const onClose = vi.fn();
        const onConfirm = vi.fn();

        render(
            <RejectOptionsModal
                isOpen={true}
                onClose={onClose}
                onConfirm={onConfirm}
                selectedCount={1}
            />
        );

        fireEvent.click(screen.getByText('Cancel'));
        expect(onClose).toHaveBeenCalled();
    });
});
