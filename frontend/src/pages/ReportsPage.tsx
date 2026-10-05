import React from 'react';
import { PageHeader } from '../components/common/PageHeader';
import { ReportSummaryMetrics } from '../components/reports/ReportSummaryMetrics';
import { InspectionTable } from '../components/common/InspectionTable';
import { AuditSection } from '../components/reports/AuditSection';
import { useReports } from '../hooks/useReports';
import { RefreshCw } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const { reports, metrics, isLoading, refetch } = useReports();

  return (
    <div className="flex-1 flex flex-col bg-canvas pb-16">
      {/* Page Header */}
      <PageHeader
        title="Inspection Reports"
        description="Official municipal pavement condition assessments, road defect logs, and spatial work-order archives."
        actions={
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-surface border border-border text-xs font-mono text-charcoal-700 hover:text-charcoal-900 shadow-subtle hover:bg-surface-subtle transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-terracotta' : ''}`} />
            <span>REFRESH REGISTRY</span>
          </button>
        }
      />

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full pt-8 space-y-10">
        
        {/* Summary Metric Blocks (Requirement 15) */}
        <section aria-label="Inspection Summary Statistics">
          <ReportSummaryMetrics metrics={metrics} isLoading={isLoading} />
        </section>

        {/* Reports Table (Requirement 16) */}
        <section className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-charcoal-900 font-sans">
                Official Corridor Records
              </h2>
            </div>
            <div className="text-xs font-mono text-charcoal-500">
              AUDIT RETENTION: 10 YEARS
            </div>
          </div>

          <InspectionTable
            variant="reports"
            reports={reports}
            emptyTitle="No inspection reports available"
            emptyDescription="Inspection reports will appear here once survey data is connected."
          />
        </section>

        {/* Audit Section (Requirement 17) */}
        <AuditSection hasReports={reports.length > 0}
         reports={reports}
         metrics={metrics} 
         />

      </div>
    </div>
  );
};
