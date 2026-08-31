interface BadgeProps {
  severity: 'Low' | 'Medium' | 'High' | 'Critical' | 'success' | 'warning' | 'danger' | 'offline';
  children: React.ReactNode;
}

export function Badge({ severity, children }: BadgeProps) {
  const colors = {
    Low: 'bg-soc-success text-white',
    Medium: 'bg-soc-warning text-white',
    High: 'bg-orange-500 text-white',
    Critical: 'bg-soc-critical text-white',
    success: 'bg-soc-success text-white',
    warning: 'bg-soc-warning text-white',
    danger: 'bg-soc-danger text-white',
    offline: 'bg-soc-offline text-white'
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-semibold ${colors[severity]}`}>
      {children}
    </span>
  );
}
