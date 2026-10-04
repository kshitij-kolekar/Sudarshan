import React from 'react';
import { Link } from 'react-router-dom';
import { HeroVisual } from '../components/home/HeroVisual';
import { WorkflowSection } from '../components/home/WorkflowSection';
import { Button } from '../components/common/Button';
import { Map, FileSpreadsheet } from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="pt-12 sm:pt-40 pb-40 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* Hero Text / Copy */}
          <div className="lg:col-span-6 space-y-6">

            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl lg:text-[5.00rem] font-bold tracking-tight text-charcoal-900 font-sans leading-[1.12]">
                See every road. <br />
                <span className="text-terracotta">Fix what matters.</span>
              </h1>

              <p className="text-base sm:text-lg text-charcoal-600 font-sans leading-relaxed max-w-xl">
                A field-ready platform for organising road surveys, locating infrastructure defects and turning inspection data into actionable reports.
              </p>
            </div>

            {/* CTAs */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link to="/map">
                <Button
                  variant="primary"
                  size="lg"
                  icon={<Map className="w-4 h-4" />}
                >
                  Open Survey Map
                </Button>
              </Link>

              <Link to="/reports">
                <Button
                  variant="secondary"
                  size="lg"
                  icon={<FileSpreadsheet className="w-4 h-4 text-charcoal-500" />}
                >
                  View Inspection Reports
                </Button>
              </Link>
            </div>

            
          </div>

          {/* Hero Geospatial Visualization */}
          <div className="lg:col-span-6">
            <HeroVisual />
          </div>

        </div>
      </section>

      {/* Main Content Body */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full space-y-12 pb-16">
        

        {/* Workflow Lifecycle (Requirement 10) */}
        <WorkflowSection />
      </div>
    </div>
  );
};
