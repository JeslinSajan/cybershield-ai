import { Card } from '../components/ui/Card';
import {
  dashboardSummary,
  alertTrend,
  vulnerabilityDistribution,
  riskTrend,
  activities
} from '../lib/demoData';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function Dashboard() {
  const summary = dashboardSummary;
  const vulnDistribution = vulnerabilityDistribution;

  const vulnChartData = [
    { name: 'Low', value: vulnDistribution.Low, color: '#10b981' },
    { name: 'Medium', value: vulnDistribution.Medium, color: '#f59e0b' },
    { name: 'High', value: vulnDistribution.High, color: '#f97316' },
    { name: 'Critical', value: vulnDistribution.Critical, color: '#dc2626' },
  ];

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Dashboard</h2>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Online Agents</p>
              <p className="text-3xl font-bold text-white">{summary.online_agents}</p>
            </div>
            <div className="w-12 h-12 bg-soc-success/20 rounded-full flex items-center justify-center">
              <span className="text-soc-success text-xl">📡</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Online Devices</p>
              <p className="text-3xl font-bold text-white">{summary.online_devices}</p>
            </div>
            <div className="w-12 h-12 bg-soc-accent/20 rounded-full flex items-center justify-center">
              <span className="text-soc-accent text-xl">🖥️</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Critical Vulns</p>
              <p className="text-3xl font-bold text-soc-critical">{summary.critical_vulnerabilities}</p>
            </div>
            <div className="w-12 h-12 bg-soc-critical/20 rounded-full flex items-center justify-center">
              <span className="text-soc-critical text-xl">🔴</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Open Alerts</p>
              <p className="text-3xl font-bold text-soc-warning">{summary.open_alerts}</p>
            </div>
            <div className="w-12 h-12 bg-soc-warning/20 rounded-full flex items-center justify-center">
              <span className="text-soc-warning text-xl">⚠️</span>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Avg Risk Score</p>
              <p className="text-3xl font-bold text-white">{summary.average_risk_score}</p>
            </div>
            <div className="w-12 h-12 bg-orange-500/20 rounded-full flex items-center justify-center">
              <span className="text-orange-500 text-xl">📊</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Alert Trend (7 Days)</h3>
          {alertTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={alertTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Line type="monotone" dataKey="count" stroke="#06b6d4" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-500">No data available</p>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Vulnerability Severity Distribution</h3>
          {vulnChartData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={vulnChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="name" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Bar dataKey="value" fill="#06b6d4" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-500">No data available</p>
            </div>
          )}
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Risk Trend (7 Days)</h3>
          {riskTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={riskTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                  itemStyle={{ color: '#e2e8f0' }}
                />
                <Legend />
                <Line type="monotone" dataKey="score" stroke="#f97316" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-500">No data available</p>
            </div>
          )}
        </Card>

        <Card>
          <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
          {activities.length > 0 ? (
            <div className="space-y-3">
              {activities.map((activity, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-soc-panelLight rounded">
                  <div className="w-2 h-2 mt-2 bg-soc-accent rounded-full"></div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-300">{activity.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-500">No activity data available</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
