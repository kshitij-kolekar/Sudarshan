import React from 'react';
import { ScanEye, MapPin, AlertTriangle, FileSpreadsheet,Building,List } from 'lucide-react';

export const WorkflowSection: React.FC = () => {
 const steps = [
    {
      num: '01',
      title: 'Real-Time Detection',
      description: 'Receive up-to-date pothole depth measurements and road condition data.',
      icon: ScanEye,
    },
    {
      num: '02',
      title: 'Interactive Road Map',
      description: 'Visualize detected potholes on an interactive map with severity indicators.',
      icon: MapPin,
    },
    {
      num: '03',
      title: 'Detailed damage analysis',
      description: 'Access pothole depth, width, area, and severity ratings with AI-powered assessment.',
      icon: AlertTriangle,
    },
    {
      num: '04',
      title: 'Repair cost estimates',
      description: 'Get instant cost estimates for pothole repairs based on size and depth.',
      icon: FileSpreadsheet,
    },
    {
      num: '05',
      title: 'City-wide dashboard',
      description: 'Monitor all road conditions across your municipality in one view.',
      icon: Building,
    },
    {
    num: '06',
    title: 'Repair prioritization',
    description: 'Auto-rank potholes by severity and generate work orders in real-time.',
    icon: List,
  },
    
  ];

  return (
    <section className="py-12 border-t border-border">
      <div className="space-y-1 mb-8 text-center">
        <h1 className="text-6xl font-bold tracking-tight text-charcoal-900 font-sans">
          One Dashboard. <br />Multiple Capabilities.
        </h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
            </div>
          );
        })}
      </div>
    </section>
  );
};
