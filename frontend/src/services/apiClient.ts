/**
 * DRONACHARYA API Client Base
 * Prepared for future integration with municipal road-operations REST/GraphQL backend.
 */
import {
  mockInspections,
  mockReports,
  mockReportSummary,
  mockDefects,
  mockSurveys,
  mockOperationalMetrics,
} from '../data/mockData';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Standard fetch wrapper structured for future backend integration.
 * In the current frontend-only environment with no active backend,
 * requests are routed to the local seed dataset in src/data/mockData.ts
 * so the UI renders populated. Set VITE_ENABLE_LIVE_API=true (and
 * VITE_API_BASE_URL) once a real telemetry API is connected.
 */
export async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  // When an actual backend URL is configured or proxy is enabled:
  if (import.meta.env.VITE_ENABLE_LIVE_API === 'true') {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new ApiError(response.status, `Request failed with status ${response.status}`);
    }

    return response.json();
  }

  // Frontend-only mode: serve seed data matching the requested endpoint
  return getMockResponse<T>(endpoint);
}

function getMockResponse<T>(endpoint: string): T {
  const [path, queryString] = endpoint.split('?');
  const query = new URLSearchParams(queryString || '');

  // GET /inspections/:id
  const inspectionMatch = path.match(/^\/inspections\/([^/]+)$/);
  if (inspectionMatch) {
    const id = inspectionMatch[1];
    const found = mockInspections.find(i => i.id === id || i.inspectionNumber === id) ?? null;
    return found as unknown as T;
  }

  // GET /inspections?limit=N
  if (path === '/inspections') {
    const limit = Number(query.get('limit')) || mockInspections.length;
    return mockInspections.slice(0, limit) as unknown as T;
  }

  // GET /reports/summary
  if (path === '/reports/summary') {
    return mockReportSummary as unknown as T;
  }

  // GET /reports
  if (path === '/reports') {
    return mockReports as unknown as T;
  }

  // GET /defects/:id
  const defectMatch = path.match(/^\/defects\/([^/]+)$/);
  if (defectMatch) {
    const id = defectMatch[1];
    const found = mockDefects.find(d => d.id === id) ?? null;
    return found as unknown as T;
  }

  // GET /defects?severity=&roadId=
  if (path === '/defects') {
    const severity = query.get('severity');
    const roadId = query.get('roadId');
    let results = mockDefects;
    if (severity) results = results.filter(d => d.severity === severity);
    if (roadId) results = results.filter(d => d.roadId === roadId);
    return results as unknown as T;
  }

  // GET /surveys/metrics
  if (path === '/surveys/metrics') {
    return mockOperationalMetrics as unknown as T;
  }

  // GET /surveys
  if (path === '/surveys') {
    return mockSurveys as unknown as T;
  }

  // Unknown endpoint: fall back to empty structure
  return [] as unknown as T;
}