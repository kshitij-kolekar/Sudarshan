import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface text-charcoal-600 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">

        {/* Bottom row */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-charcoal-400 font-mono">
          <div>
            &copy; {new Date().getFullYear()} DRONACHARYA Civil Infrastructure Platform. All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <span>Precision Survey Operations</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
