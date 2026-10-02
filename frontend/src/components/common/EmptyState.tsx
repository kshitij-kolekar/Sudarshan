import React from 'react';
import { Database, LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  compact?: boolean;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Database,
  actionLabel,
  onAction,
  className = '',
  compact = false,
}) => {
  return (
    <div
      className={`border border-dashed border-border rounded-lg bg-surface/60 text-center flex flex-col items-center justify-center ${
        compact ? 'p-6' : 'py-12 px-6'
      } ${className}`}
    >
      <div className="w-10 h-10 rounded-full bg-surface-subtle border border-border flex items-center justify-center text-charcoal-400 mb-3 shadow-subtle">
        <Icon className="w-5 h-5 stroke-[1.5]" />
      </div>
      <h4 className="text-sm font-semibold text-charcoal-700 tracking-tight mb-1">
        {title}
      </h4>
      <p className="text-xs text-charcoal-500 max-w-md leading-relaxed">
        {description}
      </p>

      {actionLabel && (
        <div className="mt-4">
          <button
            onClick={onAction}
            className="text-xs font-mono font-medium text-terracotta hover:text-terracotta-hover transition-colors inline-flex items-center gap-1.5 focus:outline-none"
          >
            <span>{actionLabel}</span>
            <span aria-hidden="true">&rarr;</span>
          </button>
        </div>
      )}
    </div>
  );
};
