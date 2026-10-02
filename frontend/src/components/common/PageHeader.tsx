import React from 'react';

interface PageHeaderProps {
  badge?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  badge,
  title,
  description,
  actions,
  className = '',
}) => {
  return (
    <div className={`border-b border-border bg-surface/50 backdrop-blur-xs py-8 px-4 sm:px-6 lg:px-8 ${className}`}>
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1.5 max-w-3xl">
          {badge && (
            <div className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-terracotta tracking-wide uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-terracotta" />
              <span>{badge}</span>
            </div>
          )}
          <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-charcoal-900 font-sans">
            {title}
          </h1>
          {description && (
            <p className="text-sm text-charcoal-500 font-sans leading-relaxed">
              {description}
            </p>
          )}
        </div>

        {actions && <div className="shrink-0 flex items-center gap-3">{actions}</div>}
      </div>
    </div>
  );
};
