import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  disabledReason?: string;
  icon?: React.ReactNode;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabledReason,
  icon,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses =
    'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 rounded-lg select-none';

  const sizeClasses = {
    sm: 'px-2.5 py-1.5 text-xs gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-5 py-2.5 text-base gap-2.5',
  }[size];

  const variantClasses = {
    primary:
      'bg-cyan-600 hover:bg-cyan-500 text-white focus:ring-cyan-500 shadow-md shadow-cyan-900/20 disabled:bg-cyan-950 disabled:text-cyan-600',
    secondary:
      'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 focus:ring-slate-500 disabled:bg-slate-900 disabled:text-slate-600',
    danger:
      'bg-rose-600 hover:bg-rose-500 text-white focus:ring-rose-500 shadow-md shadow-rose-950/20 disabled:bg-rose-950 disabled:text-rose-600',
    outline:
      'bg-transparent hover:bg-slate-800 text-slate-300 border border-slate-700 hover:border-slate-600 focus:ring-slate-500 disabled:border-slate-800 disabled:text-slate-600',
    ghost:
      'bg-transparent hover:bg-slate-800 text-slate-300 hover:text-white focus:ring-slate-500 disabled:text-slate-600',
  }[variant];

  const isDisabled = disabled || isLoading || !!disabledReason;

  const buttonElement = (
    <button
      className={`${baseClasses} ${sizeClasses} ${variantClasses} ${
        isDisabled ? 'opacity-60 cursor-not-allowed' : ''
      } ${className}`}
      disabled={isDisabled}
      title={disabledReason || props.title}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-0.5 h-4 w-4 text-current"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {!isLoading && icon && <span>{icon}</span>}
      <span>{children}</span>
    </button>
  );

  return buttonElement;
}
