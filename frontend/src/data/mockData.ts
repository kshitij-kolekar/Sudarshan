/**
 * DRONACHARYA — Seed / Demo Data
 *
 * Frontend-only demo dataset used while no live backend is connected
 * (see VITE_ENABLE_LIVE_API in src/services/apiClient.ts). Swap or
 * delete this file once the real telemetry API is wired up.
 */
import {
  Inspection,
  InspectionReport,
  ReportSummaryMetrics,
  Defect,
  Survey,
  OperationalMetrics,
} from '../types';

export const mockInspections: Inspection[] = [
  {
    id: 'insp-24095',
    inspectionNumber: 'INS-24095',
    roadSection: 'Eastern Express Highway',
    roadId: 'EEH-MUM',
    date: '26 Sept 2026',
    defectsCount: 9,
    criticalCount: 1,
    status: 'in_progress',
    inspectorName: 'R. Deshmukh',
    surveyDistanceKm: 12.4,
  },
  {
    id: 'insp-24091',
    inspectionNumber: 'INS-24091',
    roadSection: 'Western Express Highway',
    roadId: 'WEH-MUM',
    date: '24 Sept 2026',
    defectsCount: 18,
    criticalCount: 3,
    status: 'approved',
    inspectorName: 'A. Kulkarni',
    surveyDistanceKm: 22.1,
  },
  {
    id: 'insp-24088',
    inspectionNumber: 'INS-24088',
    roadSection: 'LBS Marg',
    roadId: 'LBS-MUM',
    date: '23 Sept 2026',
    defectsCount: 11,
    criticalCount: 1,
    status: 'approved',
    inspectorName: 'S. Nair',
    surveyDistanceKm: 14.7,
  },
  {
    id: 'insp-24084',
    inspectionNumber: 'INS-24084',
    roadSection: 'Sion–Panvel Highway',
    roadId: 'SPH-MUM',
    date: '22 Sept 2026',
    defectsCount: 24,
    criticalCount: 5,
    status: 'under_review',
    inspectorName: 'V. Iyer',
    surveyDistanceKm: 18.9,
  },
  {
    id: 'insp-24079',
    inspectionNumber: 'INS-24079',
    roadSection: 'Link Road, Andheri',
    roadId: 'LRA-MUM',
    date: '21 Sept 2026',
    defectsCount: 7,
    criticalCount: 0,
    status: 'approved',
    inspectorName: 'P. Shetty',
    surveyDistanceKm: 6.3,
  },
];

export const mockReports: InspectionReport[] = [
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

// Matches the "60 / 9 / 18 / 24 / 9" summary block
export const mockReportSummary: ReportSummaryMetrics = {
  totalDefects: 60,
  critical: 9,
  high: 18,
  medium: 24,
  low: 9,
};

export const mockDefects: Defect[] = [
  { id: 'def-001', roadSection: 'Western Express Highway', roadId: 'WEH-MUM', latitude: 19.1197, longitude: 72.8468, severity: 'critical', defectType: 'pothole', depthMm: 62, areaSqMeters: 0.8, chainageMeters: 14320, detectedAt: '2026-09-24', inspectionId: 'insp-24091', status: 'flagged' },
  { id: 'def-002', roadSection: 'Western Express Highway', roadId: 'WEH-MUM', latitude: 19.1201, longitude: 72.8471, severity: 'high', defectType: 'alligator_crack', areaSqMeters: 3.2, chainageMeters: 14410, detectedAt: '2026-09-24', inspectionId: 'insp-24091', status: 'scheduled_repair' },
  { id: 'def-003', roadSection: 'Western Express Highway', roadId: 'WEH-MUM', latitude: 19.1185, longitude: 72.8459, severity: 'medium', defectType: 'rutting', depthMm: 18, chainageMeters: 14210, detectedAt: '2026-09-24', inspectionId: 'insp-24091', status: 'flagged' },
  { id: 'def-004', roadSection: 'LBS Marg', roadId: 'LBS-MUM', latitude: 19.0728, longitude: 72.9006, severity: 'high', defectType: 'transverse_crack', chainageMeters: 5120, detectedAt: '2026-09-23', inspectionId: 'insp-24088', status: 'flagged' },
  { id: 'def-005', roadSection: 'LBS Marg', roadId: 'LBS-MUM', latitude: 19.0735, longitude: 72.9012, severity: 'critical', defectType: 'pothole', depthMm: 71, areaSqMeters: 1.1, chainageMeters: 5260, detectedAt: '2026-09-23', inspectionId: 'insp-24088', status: 'scheduled_repair' },
  { id: 'def-006', roadSection: 'Sion–Panvel Highway', roadId: 'SPH-MUM', latitude: 19.0466, longitude: 73.0169, severity: 'critical', defectType: 'pothole', depthMm: 88, areaSqMeters: 1.6, chainageMeters: 8940, detectedAt: '2026-09-22', inspectionId: 'insp-24084', status: 'flagged' },
  { id: 'def-007', roadSection: 'Sion–Panvel Highway', roadId: 'SPH-MUM', latitude: 19.0472, longitude: 73.0175, severity: 'high', defectType: 'edge_break', chainageMeters: 9040, detectedAt: '2026-09-22', inspectionId: 'insp-24084', status: 'flagged' },
  { id: 'def-008', roadSection: 'Sion–Panvel Highway', roadId: 'SPH-MUM', latitude: 19.0459, longitude: 73.0158, severity: 'low', defectType: 'ravelling', chainageMeters: 8820, detectedAt: '2026-09-22', inspectionId: 'insp-24084', status: 'verified' },
  { id: 'def-009', roadSection: 'Link Road, Andheri', roadId: 'LRA-MUM', latitude: 19.1290, longitude: 72.8460, severity: 'medium', defectType: 'longitudinal_crack', chainageMeters: 2140, detectedAt: '2026-09-21', inspectionId: 'insp-24079', status: 'repaired' },
  { id: 'def-010', roadSection: 'Link Road, Andheri', roadId: 'LRA-MUM', latitude: 19.1296, longitude: 72.8466, severity: 'low', defectType: 'ravelling', chainageMeters: 2260, detectedAt: '2026-09-21', inspectionId: 'insp-24079', status: 'verified' },
];

export const mockSurveys: Survey[] = [
  { id: 'srv-24091', surveyCode: 'SVY-24091', corridorName: 'Western Express Highway', roadId: 'WEH-MUM', date: '24 Sept 2026', distanceKm: 22.1, gpsCoveragePercent: 98, status: 'completed' },
  { id: 'srv-24088', surveyCode: 'SVY-24088', corridorName: 'LBS Marg', roadId: 'LBS-MUM', date: '23 Sept 2026', distanceKm: 14.7, gpsCoveragePercent: 100, status: 'completed' },
  { id: 'srv-24084', surveyCode: 'SVY-24084', corridorName: 'Sion–Panvel Highway', roadId: 'SPH-MUM', date: '22 Sept 2026', distanceKm: 18.9, gpsCoveragePercent: 96, status: 'completed' },
  { id: 'srv-24079', surveyCode: 'SVY-24079', corridorName: 'Link Road, Andheri', roadId: 'LRA-MUM', date: '21 Sept 2026', distanceKm: 6.3, gpsCoveragePercent: 100, status: 'completed' },
  { id: 'srv-24095', surveyCode: 'SVY-24095', corridorName: 'Eastern Express Highway', roadId: 'EEH-MUM', date: '26 Sept 2026', distanceKm: 12.4, gpsCoveragePercent: 91, status: 'active' },
];

export const mockOperationalMetrics: OperationalMetrics = {
  potholesDetected: 47820,
  roadsSurveyedKm: 12640,
  gpsCoveragePercent: 98,
  estimatedRepairValue: 1539000,
};