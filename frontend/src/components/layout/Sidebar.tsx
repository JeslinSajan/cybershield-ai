import { Link, useLocation } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/agents', label: 'Agents' },
  { path: '/devices', label: 'Devices' },
  { path: '/vulnerabilities', label: 'Vulnerabilities' },
  { path: '/alerts', label: 'Alerts' },
  { path: '/logs', label: 'Logs' },
  { path: '/threat-intelligence', label: 'Threat Intelligence' },
  { path: '/reports', label: 'Reports' },
  { path: '/ai-assistant', label: 'AI Assistant' },
  { path: '/settings', label: 'Settings' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-soc-panel border-r border-soc-panelLight flex flex-col">
      <div className="p-6 border-b border-soc-panelLight">
        <h1 className="text-xl font-bold text-soc-accent">CyberShield AI</h1>
        <p className="text-xs text-gray-400 mt-1">Security Operations Center</p>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`block px-4 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-soc-accent text-white font-semibold'
                      : 'text-gray-300 hover:bg-soc-panelLight hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="p-4 border-t border-soc-panelLight">
        <div className="text-xs text-gray-500">
          <p>Role: Administrator</p>
          <p>Organization: Demo Org</p>
        </div>
      </div>
    </aside>
  );
}
