import { Defect, Severity } from '../types';
import { apiRequest } from './apiClient';

/**
 * Defect Service
 * Prepared for endpoint: GET /api/defects
 * Operates in strict zero-seeded-data mode.
 */
export const defectService = {
  /**
   * Fetches detected road defects.
   * Returns empty array until field inspection feed is hooked up.
   */
  async getDefects(filters?: { severity?: Severity; roadId?: string }): Promise<Defect[]> {
    try {
      const queryParams = new URLSearchParams();
      if (filters?.severity) queryParams.set('severity', filters.severity);
      if (filters?.roadId) queryParams.set('roadId', filters.roadId);

      const endpoint = `/defects${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
      const data = await apiRequest<Defect[]>(endpoint);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.warn('[DefectService] Defect telemetry endpoint disconnected.', error);
      return [];
    }
  },

  /**
   * Fetches single defect record with telemetry and imagery.
   */
  async getDefectById(id: string): Promise<Defect | null> {
    try {
      return await apiRequest<Defect>(`/defects/${id}`);
    } catch {
      return null;
    }
  }
};
