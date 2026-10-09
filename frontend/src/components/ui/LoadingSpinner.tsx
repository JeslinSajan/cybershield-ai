export function LoadingSpinner({
  size = 'md',
  message,
}: {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }[size];

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-3">
      <div
        className={`${sizeClasses} border-cyan-500/20 border-t-cyan-400 rounded-full animate-spin`}
      />
      {message && <p className="text-sm text-slate-400 animate-pulse">{message}</p>}
    </div>
  );
}
