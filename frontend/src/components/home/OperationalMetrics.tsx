import React from 'react';
import { Metric } from '../common/Metric';
import { useSurveys } from '../../hooks/useSurveys';
import { Cable } from 'lucide-react';

export const OperationalMetrics: React.FC = () => {
  const { metrics } = useSurveys();

  return (
    <section className="space-y-4">
      {/* Intentional Empty State Banner - Polished & Engineering Styled */}
      <div className="bg-surface border border-border rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-subtle">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded bg-surface-subtle border border-border flex items-center justify-center text-charcoal-500 shrink-0 mt-0.5">
            <Cable className="w-4 h-4 text-terracotta" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-charcoal-900 tracking-tight">
              No survey data available
            </h3>
            <p className="text-xs text-charcoal-500 leading-relaxed mt-0.5 max-w-2xl">
              Connect a survey data source to populate road coverage, defect and inspection metrics. Operational telemetry will automatically aggregate in real-time once ingested.
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-surface-subtle border border-border text-xs font-mono text-charcoal-600 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-charcoal-400" />
          <span>DATA SOURCE: UNBOUND</span>
        </div>
      </div>

      {/* The Four Required Metric Areas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Metric
          label="Potholes detected"
          value={metrics.potholesDetected}
          unit="units"
          emptyNote="No defect survey connected"
          badge="DEFECTS"
        />

        <Metric
          label="Roads surveyed"
          value={metrics.roadsSurveyedKm}
          unit="km"
          emptyNote="No corridor tracks logged"
          badge="CORRIDOR"
        />

        <Metric
          label="GPS coverage"
          value={metrics.gpsCoveragePercent}
          unit="%"
          emptyNote="No GNSS track active"
          badge="GEOMETRY"
        />

        <Metric
          label="Estimated repair value"
          value={metrics.estimatedRepairValue !== null ? `₹${metrics.estimatedRepairValue}` : null}
          emptyNote="Awaiting defect classification"
          badge="WORK ORDER"
        />
      </div>
    </section>
  );
};
