import { useState, useEffect, useCallback } from 'react';
import { Inspection, AsyncState } from '../types';
import { inspectionService } from '../services/inspectionService';

export function useInspections(limit = 10) {
  const [state, setState] = useState<AsyncState<Inspection[]>>({
    data: [],
    isLoading: true,
    isError: false,
    errorMessage: null,
    isConnected: false,
  });

  const loadInspections = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, isError: false }));
    try {
      const records = await inspectionService.getRecentInspections(limit);
      setState({
        data: records,
        isLoading: false,
        isError: false,
        errorMessage: null,
        isConnected: false, // Disconnected / Unseeded frontend mode
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve inspections';
      setState({
        data: [],
        isLoading: false,
        isError: true,
        errorMessage: msg,
        isConnected: false,
      });
    }
  }, [limit]);

  useEffect(() => {
    loadInspections();
  }, [loadInspections]);

  return {
    ...state,
    refetch: loadInspections,
    isEmpty: !state.isLoading && state.data.length === 0,
  };
}
