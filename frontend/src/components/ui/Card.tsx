import React from 'react';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function Card({
  children,
  title,
  description,
  action,
  className = '',
}: CardProps) {
  return (
    <div
      className={`bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg shadow-black/20 text-slate-200 ${className}`}
    >
      {(title || action) && (
        <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800/80">
          <div>
            {title && <h3 className="text-base font-bold text-slate-100">{title}</h3>}
            {description && (
              <p className="text-xs text-slate-400 mt-0.5">{description}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
