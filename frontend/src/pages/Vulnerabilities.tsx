import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { vulnerabilities } from '../lib/demoData';

export function Vulnerabilities() {
  const tableHeaders = ['Severity', 'Score', 'Description', 'Recommendation', 'Status', 'Created'];
  const tableRows = vulnerabilities.map(vuln => [
    <Badge severity={vuln.severity}>{vuln.severity}</Badge>,
    <span className="text-gray-300">{vuln.score}</span>,
    <span className="text-gray-300">{vuln.description}</span>,
    <span className="text-gray-400 text-sm">{vuln.recommendation}</span>,
    <Badge severity="warning">{vuln.status}</Badge>,
    <span className="text-gray-400 text-sm">{new Date(vuln.created_at).toLocaleString()}</span>,
  ]);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Vulnerabilities</h2>
        <button className="bg-soc-accent hover:bg-soc-accentHover text-white px-4 py-2 rounded-md text-sm font-semibold transition-colors">
          + Run Vulnerability Scan
        </button>
      </div>

      <Card>
        {vulnerabilities.length > 0 ? (
          <Table headers={tableHeaders} rows={tableRows} />
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-gray-400 text-lg">No vulnerabilities found</p>
              <p className="text-gray-500 text-sm mt-2">Run a vulnerability scan to detect security issues</p>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
