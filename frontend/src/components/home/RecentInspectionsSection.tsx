import React from 'react';
import { InspectionTable } from '../common/InspectionTable';
import { useInspections } from '../../hooks/useInspections';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';

export const RecentInspectionsSection: React.FC = () => {
  const { data: inspections } = useInspections(5);

  return (
    <section className="py-12 border-t border-border">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6">
        <div className="space-y-1">
          <h2 className="text-2xl font-bold tracking-tight text-charcoal-900 font-sans">
            Recent inspections
          </h2>
          <p className="text-sm text-charcoal-500 max-w-xl font-sans">
            Continuous log of verified pavement surveys, road corridor recordings, and automated defect passes.
          </p>
        </div>

        <Link
          to="/reports"
          className="inline-flex items-center gap-1.5 text-xs font-mono font-semibold text-charcoal-700 hover:text-terracotta transition-colors group self-start sm:self-auto"
        >
          <span>ALL REPORTS</span>
          <ArrowUpRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </Link>
      </div>

      <InspectionTable
        variant="recent"
        inspections={inspections}
        emptyTitle="No inspections available"
        emptyDescription="Inspection records will appear here once survey data is connected to Sudarshan."
      />
    </section>
  );
};
