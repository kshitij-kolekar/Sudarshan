import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { Compass, Home } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto my-16">
      <div className="w-12 h-12 rounded-lg bg-surface-subtle border border-border flex items-center justify-center mb-4 text-terracotta">
        <Compass className="w-6 h-6" />
      </div>
      <span className="text-xs font-mono text-charcoal-400 uppercase tracking-widest mb-1">
        ERROR 404 — UNMAPPED COORDINATES
      </span>
      <h1 className="text-2xl font-bold tracking-tight text-charcoal-900 mb-2 font-sans">
        Road Section Not Found
      </h1>
      <p className="text-xs text-charcoal-500 mb-6 font-sans leading-relaxed">
        The requested GIS route or platform path does not exist in the municipal road network index.
      </p>
      <Link to="/">
        <Button variant="primary" size="md" icon={<Home className="w-4 h-4" />}>
          Return to Overview
        </Button>
      </Link>
    </div>
  );
};
