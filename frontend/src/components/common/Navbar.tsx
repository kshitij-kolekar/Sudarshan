import React, { useState } from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { name: 'Overview', path: '/' },
    { name: 'Survey Map', path: '/map' },
    { name: 'Live Camera', path: '/live-camera' },
    { name: 'Reports', path: '/reports' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-surface/95 backdrop-blur-md border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Brand - Left */}
          <Link
            to="/"
            className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-terracotta/40 rounded px-1 -ml-1"
          >
            {/* Engineering Reticle Logo */}
            <div className="w-8 h-8 rounded bg-charcoal-900 border border-charcoal-700 flex items-center justify-center text-terracotta transition-transform group-hover:scale-105">
              <svg
                className="w-5 h-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <circle
                  cx="12"
                  cy="12"
                  r="8"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                  className="opacity-60"
                />

                <circle
                  cx="12"
                  cy="12"
                  r="3"
                  fill="currentColor"
                />

                <path
                  d="M12 2V6M12 18V22M2 12H6M18 12H22"
                  strokeWidth="1.5"
                />
              </svg>
            </div>

            <div className="flex flex-col leading-none">
              <span className="text-base font-bold tracking-tight text-white font-sans">
                DRONACHARYA
              </span>

              <span className="text-[9px] font-mono tracking-widest text-white uppercase mt-0.5">
                ROAD INTELLIGENCE
              </span>
            </div>
          </Link>

          {/* Desktop Navigation - Center */}
          <nav
            className="hidden md:flex items-center space-x-1"
            aria-label="Main Navigation"
          >
            {navLinks.map((link) => {
              const isActive =
                location.pathname === link.path;

              return (
                <NavLink
                  key={link.path}
                  to={link.path}
                  className={`px-3.5 py-1.5 rounded text-sm font-medium transition-colors ${
                    isActive
  ? 'text-white bg-surface-subtle border border-border/80 shadow-xs'
  : 'text-white hover:text-white hover:bg-surface-subtle/50'
                  }`}
                >
                  {link.name}
                </NavLink>
              );
            })}
          </nav>

          {/* Mobile menu trigger */}
          <div className="flex md:hidden items-center gap-2">

            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-forest-light border border-forest-border/60 text-forest text-[11px] font-mono">
              <span className="w-1.5 h-1.5 rounded-full bg-forest" />
              <span>Live</span>
            </div>

            <button
              type="button"
              onClick={() =>
                setMobileMenuOpen(!mobileMenuOpen)
              }
              className="p-2 rounded text-charcoal-600 hover:text-charcoal-900 hover:bg-surface-subtle focus:outline-none focus:ring-2 focus:ring-terracotta"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>

          </div>

        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-surface px-4 pt-2 pb-4 space-y-1 shadow-card">

          {navLinks.map((link) => {
            const isActive =
              location.pathname === link.path;

            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() =>
                  setMobileMenuOpen(false)
                }
                className={`block px-3 py-2 rounded text-sm font-medium transition-colors ${
                  isActive
  ? 'text-white bg-surface-subtle font-semibold'
  : 'text-white hover:text-white hover:bg-surface-subtle/60'
                }`}
              >
                {link.name}
              </Link>
            );
          })}

          <div className="pt-2 border-t border-border/60 mt-2 flex items-center justify-between text-xs font-mono text-charcoal-500 px-3">

            <span>
              TELEMETRY BUS
            </span>

            <span className="text-forest flex items-center gap-1.5 font-medium">

              <span className="w-1.5 h-1.5 rounded-full bg-forest" />

              Operational

            </span>

          </div>

        </div>
      )}
    </header>
  );
};