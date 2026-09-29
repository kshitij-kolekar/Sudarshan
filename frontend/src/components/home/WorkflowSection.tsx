import React from 'react';
import { ScanEye, MapPin, AlertTriangle, FileSpreadsheet } from 'lucide-react';

export const WorkflowSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Detect',
      description: 'Identify road defects from survey imagery.',
      icon: ScanEye,
      tag: 'OPTICAL & LIDAR',
    },
    {
      num: '02',
      title: 'Locate',
      description: 'Associate each defect with its geographic position.',
      icon: MapPin,
      tag: 'GNSS & CHAINAGE',
    },
    {
      num: '03',
      title: 'Prioritise',
      description: 'Organise defects according to severity and operational importance.',
      icon: AlertTriangle,
      tag: 'PCI SCORING',
    },
    {
      num: '04',
      title: 'Report',
      description: 'Convert inspection information into structured reports.',
      icon: FileSpreadsheet,
      tag: 'WORK ORDERS',
    },
  ];

  return (
    <section className="py-12 border-t border-border">
      <div className="space-y-1 mb-8">
        <h2 className="text-2xl font-bold tracking-tight text-charcoal-900 font-sans">
          From survey to work order.
        </h2>
        <p className="text-sm text-charcoal-500 max-w-xl">
          A systematic civil engineering workflow connecting raw field capture to municipal pavement remediation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {steps.map((step) => {
          const Icon = step.icon;
          return (
            <div
              key={step.num}
              className="bg-surface border border-border rounded-lg p-5 flex flex-col justify-between shadow-subtle hover:border-charcoal-300 transition-colors relative group"
            >
              <div>

                <div className="w-8 h-8 rounded bg-surface-subtle border border-border flex items-center justify-center text-charcoal-700 mb-3 group-hover:text-charcoal-900 transition-colors">
                  <Icon className="w-4 h-4" />
                </div>

                <h3 className="text-base font-semibold text-charcoal-900 tracking-tight mb-1.5 font-sans">
                  {step.title}
                </h3>

                <p className="text-xs text-charcoal-500 leading-relaxed font-sans">
                  {step.description}
                </p>
              </div>

              <div className="mt-6 pt-3 border-t border-border/50 text-[10px] font-mono text-charcoal-400">
                STAGE {step.num} PIPELINE SPEC
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
