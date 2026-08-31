import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { demoVulnerabilities } from '../lib/demoData';

export function Vulnerabilities() {
  const vulnerabilities = demoVulnerabilities;

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
        <Table headers={tableHeaders} rows={tableRows} />
      </Card>
    </div>
  );
}
