import { Survey, OperationalMetrics } from '../types';
import { apiRequest } from './apiClient';

/**
 * Survey Service
 * Prepared for endpoint: GET /api/surveys and GET /api/surveys/metrics
 * Zero-seeded-data mode.
 */
export const surveyService = {
  /**
   * Fetches active or completed surveys.
   */
  async getSurveys(): Promise<Survey[]> {
    try {
      const data = await apiRequest<Survey[]>('/surveys');
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.warn('[SurveyService] Survey feed disconnected.', error);
      return [];
    }
  },

  /**
   * Fetches aggregate operational metrics.
   * Returns null values when unseeded/unconnected.
   */
  async getOperationalMetrics(): Promise<OperationalMetrics> {
    try {
      const metrics = await apiRequest<OperationalMetrics>('/surveys/metrics');
      if (metrics && typeof metrics.potholesDetected === 'number') {
        return metrics;
      }
      return {
        potholesDetected: null,
        roadsSurveyedKm: null,
        gpsCoveragePercent: null,
        estimatedRepairValue: null,
      };
    } catch {
      return {
        potholesDetected: null,
        roadsSurveyedKm: null,
        gpsCoveragePercent: null,
        estimatedRepairValue: null,
      };
    }
  }
};
