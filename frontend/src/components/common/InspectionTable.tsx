import React from 'react';
import { Inspection, InspectionReport } from '../../types';
import { StatusBadge } from './StatusBadge';
import { EmptyState } from './EmptyState';
import { ClipboardList, ExternalLink } from 'lucide-react';

export type TableVariant = 'recent' | 'reports';

interface InspectionTableProps {
  variant?: TableVariant;
  inspections?: Inspection[];
  reports?: InspectionReport[];
  emptyTitle?: string;
  emptyDescription?: string;
  onViewRecord?: (id: string) => void;
  className?: string;
}

export const InspectionTable: React.FC<InspectionTableProps> = ({
  variant = 'recent',
  inspections = [],
  reports = [],
  emptyTitle,
  emptyDescription,
  onViewRecord,
  className = '',
}) => {
  const isReports = variant === 'reports';
  const hasData = isReports ? reports.length > 0 : inspections.length > 0;

  const defaultEmptyTitle = isReports
    ? 'No inspection reports available'
    : 'No inspections available';

  const defaultEmptyDesc = isReports
    ? 'Inspection reports will appear here once survey data is connected.'
    : 'Inspection records will appear here once survey data is connected to Sudarshan.';

  return (
    <div className={`bg-surface border border-border rounded-lg overflow-hidden shadow-subtle ${className}`}>
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs" role="table">
          <thead>
            <tr className="bg-surface-subtle border-b border-border text-[11px] font-mono text-charcoal-500 uppercase tracking-wider">
              <th scope="col" className="py-3 px-4 font-semibold">Inspection</th>
              <th scope="col" className="py-3 px-4 font-semibold">Road section</th>
              <th scope="col" className="py-3 px-4 font-semibold">Date</th>
              <th scope="col" className="py-3 px-4 font-semibold">Defects</th>
              {isReports && <th scope="col" className="py-3 px-4 font-semibold">Critical</th>}
              {isReports && <th scope="col" className="py-3 px-4 font-semibold">GPS</th>}
              <th scope="col" className="py-3 px-4 font-semibold">Status</th>
              <th scope="col" className="py-3 px-4 font-semibold text-right">Action</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-border/60">
            {hasData ? (
              // Ready for real API rows when connected in future
              isReports ? (
                reports.map((report) => (
                  <tr key={report.id} className="hover:bg-surface-subtle/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-charcoal-900">
                      {report.reportCode}
                    </td>
                    <td className="py-3 px-4 font-medium text-charcoal-800">
                      {report.roadSection}
                    </td>
                    <td className="py-3 px-4 font-mono text-charcoal-500">
                      {report.date}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-charcoal-700">
                      {report.defectsCount}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-red-600">
                      {report.criticalCount}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-charcoal-500">
                      {report.gpsCoordinates
                        ? `${report.gpsCoordinates.latitude.toFixed(4)}, ${report.gpsCoordinates.longitude.toFixed(4)}`
                        : '—'}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={report.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onViewRecord && onViewRecord(report.id)}
                        className="text-terracotta hover:text-terracotta-hover font-medium inline-flex items-center gap-1 font-mono"
                      >
                        View <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                inspections.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-subtle/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-charcoal-900">
                      {item.inspectionNumber}
                    </td>
                    <td className="py-3 px-4 font-medium text-charcoal-800">
                      {item.roadSection}
                    </td>
                    <td className="py-3 px-4 font-mono text-charcoal-500">
                      {item.date}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-charcoal-700">
                      {item.defectsCount}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onViewRecord && onViewRecord(item.id)}
                        className="text-terracotta hover:text-terracotta-hover font-medium inline-flex items-center gap-1 font-mono"
                      >
                        Review <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )
            ) : null}
          </tbody>
        </table>
      </div>

      {/* When data is empty, render the intentional empty state container inside table frame */}
      {!hasData && (
        <div className="py-12 px-4 bg-canvas/30">
          <EmptyState
            title={emptyTitle || defaultEmptyTitle}
            description={emptyDescription || defaultEmptyDesc}
            icon={ClipboardList}
            compact
          />
        </div>
      )}
      
    </div>
  );
};
