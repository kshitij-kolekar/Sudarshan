import React from 'react';
import { Severity, InspectionStatus } from '../../types';

interface StatusBadgeProps {
  status?: InspectionStatus;
  severity?: Severity;
  label?: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  severity,
  label,
  className = '',
}) => {
  if (severity) {
    const severityStyles: Record<Severity, string> = {
      critical: 'bg-red-50 text-red-700 border-red-200',
      high: 'bg-orange-50 text-orange-800 border-orange-200',
      medium: 'bg-amber-50 text-amber-800 border-amber-200',
      low: 'bg-slate-100 text-slate-700 border-slate-200',
    };

    const displayText = label || severity.toUpperCase();

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium tracking-wide uppercase border ${severityStyles[severity]} ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full mr-1.5 shrink-0 bg-current opacity-70" />
        {displayText}
      </span>
    );
  }

  if (status) {
    const statusStyles: Record<InspectionStatus, string> = {
  pending: 'bg-surface-subtle text-charcoal-500 border-border',
  in_progress: 'bg-surface-subtle text-charcoal-500 border-border',
  completed: 'bg-forest-light text-forest border-forest-border',
  under_review: 'bg-amber-subtle text-amber-text border-amber-border',
  approved: 'bg-forest-light text-forest border-forest-border',
};

    const formatStatus = (s: InspectionStatus) => {
      switch (s) {
        case 'in_progress': return 'In Progress';
        case 'under_review': return 'Under Review';
        default: return s.charAt(0).toUpperCase() + s.slice(1);
      }
    };

    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium tracking-tight border ${statusStyles[status]} ${className}`}
      >
        <span className="w-1.5 h-1.5 rounded-full mr-1.5 shrink-0 bg-current opacity-70" />
        {label || formatStatus(status)}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono text-charcoal-500 bg-surface-subtle border border-border ${className}`}
    >
      {label || '—'}
    </span>
  );
};
