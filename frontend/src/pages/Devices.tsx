import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { devices } from '../lib/demoData';

export function Devices() {
  const tableHeaders = ['Hostname', 'IP Address', 'MAC Address', 'Vendor', 'Type', 'Status', 'Last Seen'];
  const tableRows = devices.map(device => [
    <span className="font-semibold text-white">{device.hostname}</span>,
    <span className="text-gray-300">{device.ip_address}</span>,
    <span className="text-gray-400 text-sm">{device.mac_address}</span>,
    <span className="text-gray-300">{device.vendor}</span>,
    <span className="text-gray-300">{device.device_type}</span>,
    <Badge severity={device.status === 'online' ? 'success' : 'offline'}>
      {device.status}
    </Badge>,
    <span className="text-gray-400 text-sm">{new Date(device.last_seen_at).toLocaleString()}</span>,
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Devices</h2>
        <button className="bg-soc-accent hover:bg-soc-accentHover text-white px-4 py-2 rounded-md text-sm font-semibold transition-colors">
          + Run Discovery Scan
        </button>
      </div>

      <Card>
        {devices.length > 0 ? (
          <Table headers={tableHeaders} rows={tableRows} />
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-400 text-lg">No devices discovered</p>
              <p className="text-gray-500 text-sm mt-2">Run a discovery scan to find devices on your network</p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
