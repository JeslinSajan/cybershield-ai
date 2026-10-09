import React from 'react';

export type BadgeVariant =
  | 'Low'
  | 'Medium'
  | 'High'
  | 'Critical'
  | 'success'
  | 'warning'
  | 'danger'
  | 'offline'
  | 'info'
  | 'default';

interface BadgeProps {
  severity?: BadgeVariant | string;
  variant?: BadgeVariant | string;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ severity, variant, children, className = '' }: BadgeProps) {
  const key = (severity || variant || 'default').toString().toLowerCase();

  let colorClasses = 'bg-slate-700 text-slate-200 border-slate-600';

  if (['low', 'success', 'online', 'completed', 'healthy'].includes(key)) {
    colorClasses = 'bg-emerald-950/70 text-emerald-300 border-emerald-700/60';
  } else if (['medium', 'warning', 'pending', 'investigating', 'running'].includes(key)) {
    colorClasses = 'bg-amber-950/70 text-amber-300 border-amber-700/60';
  } else if (['high'].includes(key)) {
    colorClasses = 'bg-orange-950/70 text-orange-300 border-orange-700/60';
  } else if (['critical', 'danger', 'offline', 'failed', 'error', 'locked'].includes(key)) {
    colorClasses = 'bg-rose-950/70 text-rose-300 border-rose-700/60';
  } else if (['info', 'acknowledged', 'discovery', 'vulnerability'].includes(key)) {
    colorClasses = 'bg-cyan-950/70 text-cyan-300 border-cyan-700/60';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${colorClasses} ${className}`}
    >
      {children}
    </span>
  );
}
