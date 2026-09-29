import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Download, AlertCircle } from 'lucide-react';
import {
  InspectionReport,
  ReportSummaryMetrics,
} from '../../types';
import { generatePotholeReportPdf } from '../../utils/generatePotholeReportPdf';

interface AuditSectionProps {
  hasReports?: boolean;
  reports: InspectionReport[];
  metrics: ReportSummaryMetrics;
}

export const AuditSection: React.FC<AuditSectionProps> = ({
  hasReports = false,
  reports,
  metrics,
}) => {
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);

  const handleDownloadClick = () => {
    try {
      if (!hasReports || reports.length === 0) {
        setDownloadNotice('No report data available to export.');
        return;
      }

      // Generate and download PDF
      generatePotholeReportPdf(reports, metrics);

      setDownloadNotice(
        `Audit package downloaded successfully — ${reports.length} records included.`
      );

      setTimeout(() => {
        setDownloadNotice(null);
      }, 4500);
    } catch (error) {
      console.error('PDF generation failed:', error);

      setDownloadNotice(
        'Unable to generate the audit package. Please try again.'
      );

      setTimeout(() => {
        setDownloadNotice(null);
      }, 4500);
    }
  };

  return (
    <section className="bg-surface border border-border rounded-xl p-6 sm:p-8 shadow-card relative overflow-hidden">

      {/* Background CAD grid accent */}
      <div className="absolute right-0 top-0 w-1/3 h-full bg-cad-grid opacity-30 pointer-events-none" />

      <div className="relative z-10 max-w-2xl space-y-4">

        <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-charcoal-900 font-sans">
          One complete audit trail.
        </h2>

        <p className="text-sm text-charcoal-500 font-sans leading-relaxed">
          Consolidate inspection information into a structured audit package
          for review, documentation and future operational workflows.
        </p>

        <div className="pt-2 flex flex-wrap items-center gap-3">

          <Button
            variant="primary"
            size="md"
            icon={<Download className="w-4 h-4" />}
            onClick={handleDownloadClick}
            disabled={!hasReports}
            title={
              !hasReports
                ? 'No report data available to export'
                : 'Download audit archive'
            }
          >
            Download audit package
          </Button>

          {!hasReports && (
            <span className="text-xs font-mono text-charcoal-400">
              [PACKAGE LOCKED: 0 RECORDS COMPILED]
            </span>
          )}

        </div>

        {/* Download feedback */}
        {downloadNotice && (
          <div className="mt-4 p-3 bg-amber-subtle border border-amber-border rounded-lg text-xs font-mono text-amber-text flex items-center gap-2 animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0 text-amber-text" />
            <span>{downloadNotice}</span>
          </div>
        )}

      </div>
    </section>
  );
};