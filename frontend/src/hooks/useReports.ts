import { useState, useEffect, useCallback } from 'react';
import { InspectionReport, ReportSummaryMetrics, AsyncState } from '../types';

/**
 * Seed data — shown until a real reporting backend is connected.
 * Replace this block (or swap loadReportData's body for real
 * reportService calls) once the live API is wired up.
 */
const SEED_REPORTS: InspectionReport[] = [
  {
    id: 'rep-24091',
    reportCode: 'INS-24091',
    inspectionId: 'insp-24091',
    roadSection: 'Western Express Highway',
    date: '24 Sept 2026',
    defectsCount: 18,
    criticalCount: 3,
    gpsCoordinates: { latitude: 19.1197, longitude: 72.8468, accuracyMeters: 2 },
    status: 'approved',
    estimatedCostValue: 486000,
    auditHash: 'a1f9c8-88de-4b21',
    fileSizeKb: 842,
  },
  {
    id: 'rep-24088',
    reportCode: 'INS-24088',
    inspectionId: 'insp-24088',
    roadSection: 'LBS Marg',
    date: '23 Sept 2026',
    defectsCount: 11,
    criticalCount: 1,
    gpsCoordinates: { latitude: 19.0728, longitude: 72.9006, accuracyMeters: 1 },
    status: 'approved',
    estimatedCostValue: 215000,
    auditHash: 'b47e21-0c9a-4f13',
    fileSizeKb: 511,
  },
  {
    id: 'rep-24084',
    reportCode: 'INS-24084',
    inspectionId: 'insp-24084',
    roadSection: 'Sion–Panvel Highway',
    date: '22 Sept 2026',
    defectsCount: 24,
    criticalCount: 5,
    gpsCoordinates: { latitude: 19.0466, longitude: 73.0169, accuracyMeters: 4 },
    status: 'under_review',
    estimatedCostValue: 742000,
    auditHash: 'c9021d-77bf-4a06',
    fileSizeKb: 1180,
  },
  {
    id: 'rep-24079',
    reportCode: 'INS-24079',
    inspectionId: 'insp-24079',
    roadSection: 'Link Road, Andheri',
    date: '21 Sept 2026',
    defectsCount: 7,
    criticalCount: 0,
    gpsCoordinates: { latitude: 19.1290, longitude: 72.8460, accuracyMeters: 1 },
    status: 'approved',
    estimatedCostValue: 96000,
    auditHash: 'd3f870-1e5c-49aa',
    fileSizeKb: 298,
  },
];

const SEED_SUMMARY: ReportSummaryMetrics = {
  totalDefects: 60,
  critical: 9,
  high: 18,
  medium: 24,
  low: 9,
};

export function useReports() {
  const [reportsState, setReportsState] = useState<AsyncState<InspectionReport[]>>({
    data: [],
    isLoading: true,
    isError: false,
    errorMessage: null,
    isConnected: false,
  });

  const [metrics, setMetrics] = useState<ReportSummaryMetrics>({
    totalDefects: null,
    critical: null,
    high: null,
    medium: null,
    low: null,
  });

  const loadReportData = useCallback(async () => {
    setReportsState(prev => ({ ...prev, isLoading: true, isError: false }));
    try {
      // Seeded directly here instead of going through reportService/apiClient.
      setReportsState({
        data: SEED_REPORTS,
        isLoading: false,
        isError: false,
        errorMessage: null,
        isConnected: false,
      });
      setMetrics(SEED_SUMMARY);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to retrieve reports';
      setReportsState({
        data: [],
        isLoading: false,
        isError: true,
        errorMessage: msg,
        isConnected: false,
      });
    }
  }, []);

  useEffect(() => {
    loadReportData();
  }, [loadReportData]);

  return {
    reports: reportsState.data,
    metrics,
    isLoading: reportsState.isLoading,
    isError: reportsState.isError,
    errorMessage: reportsState.errorMessage,
    isEmpty: !reportsState.isLoading && reportsState.data.length === 0,
    refetch: loadReportData,
  };
}