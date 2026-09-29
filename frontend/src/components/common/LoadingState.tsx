import React from 'react';

interface LoadingStateProps {
  label?: string;
  rows?: number;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  label = 'Loading telemetry...',
  rows = 4,
  className = '',
}) => {
  return (
    <div className={`p-6 bg-surface border border-border rounded-lg space-y-3 ${className}`}>
      <div className="flex items-center gap-2 text-xs font-mono text-charcoal-400">
        <span className="w-2 h-2 rounded-full bg-terracotta animate-pulse" />
        <span>{label}</span>
      </div>
      <div className="space-y-2 pt-2">
        {Array.from({ length: rows }).map((_, i) => (
          <div
            key={i}
            className="h-9 bg-surface-subtle border border-border/60 rounded animate-pulse"
            style={{ opacity: 1 - i * 0.15 }}
          />
        ))}
      </div>
    </div>
  );
};
