import React from 'react';
import { Metric } from '../common/Metric';
import { useSurveys } from '../../hooks/useSurveys';

export const HeroVisual: React.FC = () => {
  const { metrics } = useSurveys();

  return (
    <div className="relative w-full">

  {/* Photo */}
  <div className="relative aspect-[16/10] sm:aspect-[16/9] w-full bg-black overflow-hidden">
    <img
      src="/drone-hero.png"
      alt="Road inspection drone"
      className="absolute inset-0 w-full h-full object-cover"
    />
  </div>

  {/* Metrics OVER the photo */}
  <div className="absolute inset-0 z-10 pointer-events-none">

    {/* Potholes */}
    <div className="absolute right-[8%] top-[62%]">
      <Metric
        label="Potholes repaired"
        value={metrics.potholesDetected}
        unit="+"
        className="bg-transparent border-0 shadow-none p-0"
      />
    </div>

    {/* Roads */}
    <div className="absolute right-[8%] top-[92%]">
      <Metric
        label="Roads surveyed"
        value={metrics.roadsSurveyedKm}
        unit="miles"
        className="bg-transparent border-0 shadow-none p-0"
      />
    </div>

  </div>

</div>
  );
};