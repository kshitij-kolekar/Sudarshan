import React from 'react';
import { Layers, Compass, FileCheck } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-border bg-surface text-charcoal-600 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-8 border-b border-border/60">
          
          {/* Brand Info */}
          <div className="space-y-3 md:col-span-2">
            <div className="flex items-center gap-2.5">
              <div className="w-5 h-5 rounded bg-charcoal-900 flex items-center justify-center text-terracotta">
                <span className="w-1.5 h-1.5 rounded-full bg-terracotta" />
              </div>
              <span className="font-bold tracking-tight text-charcoal-900 text-sm">
                SUDARSHAN
              </span>
              <span className="text-[10px] font-mono uppercase tracking-widest text-charcoal-400">
                / ROAD INTELLIGENCE
              </span>
            </div>
            <p className="text-xs text-charcoal-500 max-w-md leading-relaxed">
              Municipal road asset management, defect identification, and survey analytics platform for civil engineering authorities and operations teams.
            </p>
            <div className="flex items-center gap-4 text-[11px] font-mono text-charcoal-400">
              <span>WGS 84 DATUM</span>
              <span>•</span>
              <span>ASTM D6433 (PCI) COMPLIANT SPEC</span>
              <span>•</span>
              <span>CRS: EPSG:4326</span>
            </div>
          </div>

          {/* Platform Spec */}
          <div className="space-y-2">
            <div className="text-xs font-mono uppercase tracking-wider text-charcoal-900 font-semibold">
              Survey Modules
            </div>
            <ul className="text-xs space-y-1.5 text-charcoal-500">
              <li className="flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-charcoal-400" />
                <span>Geographic Chainage Engine</span>
              </li>
              <li className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-charcoal-400" />
                <span>Pavement Condition Index (PCI)</span>
              </li>
              <li className="flex items-center gap-1.5">
                <FileCheck className="w-3.5 h-3.5 text-charcoal-400" />
                <span>Municipal Work Order Export</span>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom row */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-charcoal-400 font-mono">
          <div>
            &copy; {new Date().getFullYear()} SUDARSHAN Civil Infrastructure Platform. All rights reserved.
          </div>
          <div className="flex items-center gap-4">
            <span>Precision Survey Operations</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
