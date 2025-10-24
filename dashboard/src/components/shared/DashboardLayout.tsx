/**
 * Shared Dashboard Layout Component
 *
 * Provides consistent layout structure and styling for all dashboard pages.
 * Ensures uniform header, navigation, and container styling.
 */

import React from "react";
import { cn } from "../../lib/utils";
import { SwarmAILogo } from "./SwarmAILogo";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  icon?: string;
  className?: string;
  headerActions?: React.ReactNode;
  showLogo?: boolean;
  logoVariant?: "logo-only" | "logo-with-name";
}

export function DashboardLayout({
  children,
  title,
  subtitle,
  icon,
  className,
  headerActions,
  showLogo = true,
  logoVariant = "logo-with-name",
}: DashboardLayoutProps) {
  return (
    <div className={cn("dashboard-container", className)}>
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {showLogo && (
              <div className="flex items-center">
                <SwarmAILogo
                  variant={logoVariant}
                  size={logoVariant === "logo-only" ? "md" : "xl"}
                  priority
                />
              </div>
            )}
            <div>
              <h1 className="dashboard-title">
                {icon && <span className="mr-2">{icon}</span>}
                {title}
              </h1>
              {subtitle && <p className="dashboard-subtitle">{subtitle}</p>}
            </div>
          </div>
          {headerActions && (
            <div className="flex items-center gap-3">{headerActions}</div>
          )}
        </div>
      </div>

      {/* Dashboard Content */}
      <div className="dashboard-content">{children}</div>
    </div>
  );
}

/**
 * Dashboard Section Component
 *
 * Provides consistent section styling with optional header and actions.
 */
interface DashboardSectionProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  className?: string;
  variant?: "default" | "glass" | "bordered";
}

export function DashboardSection({
  children,
  title,
  subtitle,
  actions,
  className,
  variant = "default",
}: DashboardSectionProps) {
  const sectionClasses = cn(
    "rounded-lg p-4",
    {
      "bg-slate-800/50 border border-slate-700": variant === "default",
      "card-glass": variant === "glass",
      "border-2 border-slate-600": variant === "bordered",
    },
    className
  );

  return (
    <section className={sectionClasses}>
      {(title || actions) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-white mb-1">{title}</h2>
            )}
            {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  );
}

/**
 * Dashboard Grid Component
 *
 * Provides consistent grid layouts with responsive behavior.
 */
interface DashboardGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4;
  className?: string;
}

export function DashboardGrid({
  children,
  columns = 3,
  className,
}: DashboardGridProps) {
  const gridClasses = cn(
    "dashboard-grid",
    {
      "dashboard-grid-2": columns === 2,
      "dashboard-grid-3": columns === 3,
      "dashboard-grid-4": columns === 4,
    },
    className
  );

  return <div className={gridClasses}>{children}</div>;
}
