// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5,       // Data fresh for 5 minutes
            gcTime: 1000 * 60 * 30,         // Keep in memory 30 minutes
            refetchOnWindowFocus: false,    // No refetch on tab switch
            retry: 1,                        // Single retry on failure
        },
    },
});
