import { Inspection } from '../types';
import { apiRequest } from './apiClient';

/**
 * Inspection Service
 * Prepared for endpoint: GET /api/inspections
 * Currently operating in zero-seeded-data mode.
 */
export const inspectionService = {
  /**
   * Fetches recent inspection records from municipal telemetry API.
   * Returns empty array until live survey backend is connected.
   */
  async getRecentInspections(limit = 10): Promise<Inspection[]> {
    try {
      const data = await apiRequest<Inspection[]>(`/inspections?limit=${limit}`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.warn('[InspectionService] Telemetry endpoint disconnected. Operating in unseeded state.', error);
      return [];
    }
  },

  /**
   * Fetches inspection by specific ID.
   */
  async getInspectionById(id: string): Promise<Inspection | null> {
    try {
      return await apiRequest<Inspection>(`/inspections/${id}`);
    } catch {
      return null;
    }
  }
};
