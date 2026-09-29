import { useState, useEffect, useCallback } from 'react';
import { OperationalMetrics } from '../types';
import { surveyService } from '../services/surveyService';

export function useSurveys() {
  const [metrics, setMetrics] = useState<OperationalMetrics>({
    potholesDetected: null,
    roadsSurveyedKm: null,
    gpsCoveragePercent: null,
    estimatedRepairValue: null,
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isError, setIsError] = useState<boolean>(false);

  const loadMetrics = useCallback(async () => {
    setIsLoading(true);
    setIsError(false);
    try {
      const data = await surveyService.getOperationalMetrics();
      setMetrics(data);
      setIsLoading(false);
    } catch {
      setIsError(true);
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  const isEmpty =
    metrics.potholesDetected === null &&
    metrics.roadsSurveyedKm === null &&
    metrics.gpsCoveragePercent === null &&
    metrics.estimatedRepairValue === null;

  return {
    metrics,
    isLoading,
    isError,
    isEmpty,
    refetch: loadMetrics,
  };
}
