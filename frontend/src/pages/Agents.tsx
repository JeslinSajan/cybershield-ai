import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { demoAgents } from '../lib/demoData';

export function Agents() {
  const agents = demoAgents;

  const tableHeaders = ['Name', 'Hostname', 'Status', 'Version', 'Last Heartbeat', 'Created'];
  const tableRows = agents.map(agent => [
    <span className="font-semibold text-white">{agent.name}</span>,
    <span className="text-gray-300">{agent.hostname}</span>,
    <Badge severity={agent.status === 'ONLINE' ? 'success' : agent.status === 'OFFLINE' ? 'offline' : 'warning'}>
      {agent.status}
    </Badge>,
    <span className="text-gray-300">{agent.version}</span>,
    <span className="text-gray-400 text-sm">{new Date(agent.last_heartbeat_at).toLocaleString()}</span>,
    <span className="text-gray-400 text-sm">{new Date(agent.created_at).toLocaleString()}</span>,
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Agents</h2>
        <button className="bg-soc-accent hover:bg-soc-accentHover text-white px-4 py-2 rounded-md text-sm font-semibold transition-colors">
          + Register Agent
        </button>
      </div>

      <Card>
        <Table headers={tableHeaders} rows={tableRows} />
      </Card>
    </div>
  );
}
