import React from 'react';
import { Metric } from '../common/Metric';
import { ReportSummaryMetrics as MetricsType } from '../../types';
import { ClipboardCheck } from 'lucide-react';

interface ReportSummaryMetricsProps {
  metrics: MetricsType;
  isLoading?: boolean;
}

export const ReportSummaryMetrics: React.FC<ReportSummaryMetricsProps> = ({
  metrics,
}) => {
  return (
    <div className="space-y-4">
      {/* Intentional Empty State Banner (Requirement 15) */}
      <div className="bg-surface border border-border rounded-lg p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-subtle">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded bg-surface-subtle border border-border flex items-center justify-center text-charcoal-500 shrink-0 mt-0.5">
            <ClipboardCheck className="w-4 h-4 text-terracotta" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-charcoal-900 tracking-tight">
              Awaiting inspection data
            </h3>
            <p className="text-xs text-charcoal-500 leading-relaxed mt-0.5 max-w-2xl">
              Connect survey data to populate inspection statistics. Defect severity breakdown, risk distribution and compliance metrics will compute automatically.
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded bg-surface-subtle border border-border text-xs font-mono text-charcoal-600 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-text" />
          <span>STATUS: UNPOPULATED</span>
        </div>
      </div>

      {/* The 5 Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 sm:gap-4">
        <Metric
          label="Total defects"
          value={metrics.totalDefects}
          emptyNote="No reports processed"
          badge="TOTAL"
        />

        <Metric
          label="Critical"
          value={metrics.critical}
          badge="CRITICAL"
          badgeVariant="critical"
          emptyNote="&gt; 50mm rut / failure"
        />

        <Metric
          label="High"
          value={metrics.high}
          badge="HIGH"
          badgeVariant="high"
          emptyNote="Structural fatigue"
        />

        <Metric
          label="Medium"
          value={metrics.medium}
          badge="MEDIUM"
          badgeVariant="medium"
          emptyNote="Surface distress"
        />

        <Metric
          label="Low"
          value={metrics.low}
          badge="LOW"
          badgeVariant="low"
          emptyNote="Minor ravelling"
        />
      </div>
    </div>
  );
};
