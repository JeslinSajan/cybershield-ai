import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { demoAlerts } from '../lib/demoData';

export function Alerts() {
  const alerts = demoAlerts;

  const tableHeaders = ['Type', 'Severity', 'Status', 'Description', 'Risk Score', 'Triggered', 'Device'];
  const tableRows = alerts.map(alert => [
    <span className="text-gray-300 capitalize">{alert.alert_type.replace('_', ' ')}</span>,
    <Badge severity={alert.severity}>{alert.severity}</Badge>,
    <Badge severity={alert.status === 'Open' ? 'danger' : alert.status === 'Acknowledged' ? 'warning' : 'success'}>
      {alert.status}
    </Badge>,
    <span className="text-gray-300">{alert.description}</span>,
    <span className="text-gray-300">{alert.risk_score}</span>,
    <span className="text-gray-400 text-sm">{new Date(alert.triggered_at).toLocaleString()}</span>,
    <span className="text-gray-400 text-sm">{alert.device_id}</span>,
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Alerts</h2>
        <div className="flex space-x-2">
          <select className="bg-soc-panelLight border border-soc-panelLight rounded-md px-3 py-2 text-sm text-gray-300">
            <option>All Severities</option>
            <option>Critical</option>
            <option>High</option>
            <option>Medium</option>
            <option>Low</option>
          </select>
          <select className="bg-soc-panelLight border border-soc-panelLight rounded-md px-3 py-2 text-sm text-gray-300">
            <option>All Statuses</option>
            <option>Open</option>
            <option>Acknowledged</option>
            <option>Investigating</option>
            <option>Resolved</option>
            <option>False Positive</option>
          </select>
        </div>
      </div>

      <Card>
        <Table headers={tableHeaders} rows={tableRows} />
      </Card>
    </div>
  );
}
