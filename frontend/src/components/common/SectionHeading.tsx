import React from 'react';

interface SectionHeadingProps {
  label?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  align?: 'left' | 'center';
  className?: string;
}

export const SectionHeading: React.FC<SectionHeadingProps> = ({
  label,
  title,
  description,
  action,
  align = 'left',
  className = '',
}) => {
  return (
    <div
      className={`flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 ${
        align === 'center' ? 'text-center sm:text-left' : ''
      } ${className}`}
    >
      <div className="space-y-1 max-w-2xl">
        {label && (
          <div className="text-[11px] font-mono font-medium text-terracotta tracking-wider uppercase">
            {label}
          </div>
        )}
        <h2 className="text-xl sm:text-2xl font-semibold tracking-tight text-charcoal-900 font-sans">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-charcoal-500 font-sans leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
};
