// src/components/shared/DataPreviewModal.tsx
import React from 'react';
import { CloseIcon } from '@/components/shared/Icons';
// Import Card components for modularity
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
// Import StatusBadge for the new header requirement
import StatusBadge from './StatusBadge';

/**
 * A "dumb" modal shell component that utilizes Card components 
 * for structurally consistent internal content presentation.
 */
interface DataPreviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode; 
    footer: React.ReactNode;
    status: string; 
    headerActions?: React.ReactNode; // <-- ADD THIS LINE
}

function DataPreviewModal({
    isOpen,
    onClose,
    title,
    children,
    footer,
    status, // Destructure new prop
    headerActions // <-- ADD THIS LINE
}: DataPreviewModalProps) {

    if (!isOpen) return null;

    return (
        // Modal Backdrop/Primitive: Handles positioning, background, z-index
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">

            {/* Modal Content: Use Card as the container */}
            <Card className="max-w-6xl w-full flex flex-col overflow-hidden">
                
                {/* Header: Use CardHeader and CardTitle */}
                <CardHeader className="flex-row items-center justify-between p-5 border-b gap-3">
                    <CardTitle className="text-xl text-gray-800 p-0 m-0 flex items-center gap-3 min-w-0 flex-1">
                        <span className="truncate max-w-[50%]">{title}</span>
                        <div className="flex-shrink-0">
                            <StatusBadge status={status} />
                        </div>
                    </CardTitle>

                    {/* --- Right side actions --- */}
                    <div className="flex items-center gap-3 flex-shrink-0">
                        {headerActions} {/* <-- RENDER THE NEW BUTTON SLOT HERE */}
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 transition-colors"
                            aria-label="Close modal"
                        >
                            <CloseIcon />
                        </button>
                    </div>
                </CardHeader>

                {/* Body: Use CardContent for padding, but customize for scrolling/background */}
                <CardContent className="p-6 bg-gray-50 max-h-[75vh] overflow-y-auto">
                    {children}
                </CardContent>

                {/* Footer: Use CardFooter to hold the action buttons/status */}
                <CardFooter className="p-0 border-t">
                    {footer}
                </CardFooter>

            </Card>
        </div>
    );
}

export default DataPreviewModal;