import React from 'react';

interface MetricProps {
  label: string;
  value: number | string | null;
  unit?: string;
  subtext?: string;
  badge?: string;
  badgeVariant?: 'default' | 'critical' | 'high' | 'medium' | 'low';
  emptyNote?: string;
  className?: string;
}

export const Metric: React.FC<MetricProps> = ({
  label,
  value,
  unit,
  subtext,
  badge,
  badgeVariant = 'default',
  emptyNote,
  className = '',
}) => {
  const isValuePresent = value !== null && value !== undefined && value !== '';
  const displayValue = isValuePresent ? value : '—';

  const badgeStyles = {
  default: 'bg-surface-subtle text-charcoal-500 border-border',
  critical: 'bg-surface-subtle text-charcoal-500 border-border',
  high: 'bg-surface-subtle text-charcoal-500 border-border',
  medium: 'bg-surface-subtle text-charcoal-500 border-border',
  low: 'bg-surface-subtle text-charcoal-500 border-border',
};

  return (
    <div
      className={`bg-surface border border-border rounded-lg p-5 flex flex-col justify-between shadow-subtle hover:border-charcoal-300 transition-colors ${className}`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className="text-xs font-mono uppercase tracking-wider text-charcoal-500 font-medium">
          {label}
        </span>
        {badge && (
          <span
            className={`text-[10px] font-mono px-1.5 py-0.5 rounded border uppercase ${badgeStyles[badgeVariant]}`}
          >
            {badge}
          </span>
        )}
      </div>

      <div className="my-1">
        <div className="flex items-baseline gap-1.5">
          <span
            className={`text-2xl sm:text-3xl font-semibold tracking-tight font-mono ${
              isValuePresent ? 'text-charcoal-900' : 'text-charcoal-400'
            }`}
          >
            {displayValue}
          </span>
          {unit && isValuePresent && (
            <span className="text-xs font-mono text-charcoal-500">{unit}</span>
          )}
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-border/60">
        <p className="text-[11px] text-charcoal-400 font-sans leading-relaxed">
          {emptyNote ? emptyNote : subtext || 'Awaiting live survey telemetry'}
        </p>
      </div>
    </div>
  );
};
