import { useState, useEffect, useCallback } from 'react';
import { Defect, Severity, AsyncState } from '../types';
import { defectService } from '../services/defectService';

export function useDefects(initialSeverityFilter?: Severity) {
  const [severityFilter, setSeverityFilter] = useState<Severity | undefined>(initialSeverityFilter);
  const [selectedDefectId, setSelectedDefectId] = useState<string | null>(null);
  const [state, setState] = useState<AsyncState<Defect[]>>({
    data: [],
    isLoading: true,
    isError: false,
    errorMessage: null,
    isConnected: false,
  });

  const loadDefects = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, isError: false }));
    try {
      const defects = await defectService.getDefects({ severity: severityFilter });
      setState({
        data: defects,
        isLoading: false,
        isError: false,
        errorMessage: null,
        isConnected: false,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve defect telemetry';
      setState({
        data: [],
        isLoading: false,
        isError: true,
        errorMessage: msg,
        isConnected: false,
      });
    }
  }, [severityFilter]);

  useEffect(() => {
    loadDefects();
  }, [loadDefects]);

  const selectedDefect = state.data.find(d => d.id === selectedDefectId) || null;

  return {
    ...state,
    selectedDefect,
    selectedDefectId,
    setSelectedDefectId,
    severityFilter,
    setSeverityFilter,
    refetch: loadDefects,
    isEmpty: !state.isLoading && state.data.length === 0,
  };
}
