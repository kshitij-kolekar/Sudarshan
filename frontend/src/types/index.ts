/**
 * SUDARSHAN - Core Domain Types & Data Contracts
 * Designed for municipal road-operations and GIS field survey telemetry.
 */

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type DefectType = 
  | 'pothole' 
  | 'transverse_crack' 
  | 'longitudinal_crack' 
  | 'alligator_crack' 
  | 'rutting' 
  | 'edge_break' 
  | 'ravelling';

export type InspectionStatus = 
  | 'pending'
  | 'in_progress' 
  | 'completed' 
  | 'under_review' 
  | 'approved';

export interface GPSCoordinates {
  latitude: number;
  longitude: number;
  altitudeMeters?: number;
  accuracyMeters?: number;
}

export interface Defect {
  id: string;
  roadSection: string;
  roadId?: string;
  latitude: number;
  longitude: number;
  severity: Severity;
  defectType: DefectType;
  depthMm?: number;
  areaSqMeters?: number;
  chainageMeters?: number; // Distance along road chainage (e.g., KM 14+320)
  detectedAt?: string;
  inspectionId?: string;
  photoUrl?: string;
  status?: 'flagged' | 'scheduled_repair' | 'repaired' | 'verified';
}

export interface Inspection {
  id: string;
  inspectionNumber: string;
  roadSection: string;
  roadId: string;
  date: string;
  defectsCount: number;
  criticalCount: number;
  status: InspectionStatus;
  gpsCoordinates?: GPSCoordinates;
  inspectorName?: string;
  surveyDistanceKm?: number;
  notes?: string;
}

export interface Road {
  id: string;
  code: string;
  name: string;
  category: 'primary_arterial' | 'secondary_collector' | 'local_access' | 'expressway';
  jurisdiction: string;
  surfaceType: 'asphalt' | 'concrete' | 'composite';
  lengthKm: number;
  lastSurveyDate?: string;
}

export interface Survey {
  id: string;
  surveyCode: string;
  corridorName: string;
  roadId: string;
  date: string;
  distanceKm: number;
  gpsCoveragePercent: number;
  status: 'active' | 'completed' | 'queued';
}

export interface InspectionReport {
  id: string;
  reportCode: string;
  inspectionId: string;
  roadSection: string;
  date: string;
  defectsCount: number;
  criticalCount: number;
  gpsCoordinates: GPSCoordinates;
  status: InspectionStatus;
  estimatedCostValue?: number;
  auditHash?: string;
  fileSizeKb?: number;
}

export interface OperationalMetrics {
  potholesDetected: number | null;
  roadsSurveyedKm: number | null;
  gpsCoveragePercent: number | null;
  estimatedRepairValue: number | null;
}

export interface ReportSummaryMetrics {
  totalDefects: number | null;
  critical: number | null;
  high: number | null;
  medium: number | null;
  low: number | null;
}

/**
 * Standard Async State container for UI components
 */
export interface AsyncState<T> {
  data: T;
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  isConnected: boolean;
}
