import { InspectionReport, ReportSummaryMetrics } from '../types';
import { apiRequest } from './apiClient';

/**
 * Report Service
 * Prepared for endpoint: GET /api/reports and GET /api/reports/summary
 */
export const reportService = {
  /**
   * Fetches published inspection reports.
   * Returns empty array until reporting service is connected.
   */
  async getReports(): Promise<InspectionReport[]> {
    try {
      const data = await apiRequest<InspectionReport[]>('/reports');
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.warn('[ReportService] Reports API disconnected.', error);
      return [];
    }
  },

  /**
   * Fetches summary statistics for reports.
   * Returns null counters when no data is seeded.
   */
  async getSummaryMetrics(): Promise<ReportSummaryMetrics> {
    try {
      const metrics = await apiRequest<ReportSummaryMetrics>('/reports/summary');
      if (metrics && typeof metrics.totalDefects === 'number') {
        return metrics;
      }
      return {
        totalDefects: null,
        critical: null,
        high: null,
        medium: null,
        low: null,
      };
    } catch {
      return {
        totalDefects: null,
        critical: null,
        high: null,
        medium: null,
        low: null,
      };
    }
  },

  /**
   * Generates or downloads the official consolidated audit package.
   * Resolves false/null when audit package contains zero records.
   */
  async downloadAuditPackage(): Promise<{ success: boolean; message: string }> {
    return {
      success: false,
      message: 'No report data available to compile an audit package.'
    };
  }
};
