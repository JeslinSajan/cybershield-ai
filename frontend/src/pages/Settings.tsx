import { Card } from '../components/ui/Card';

export function Settings() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Settings</h2>
      <Card>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-gray-400 text-lg">Coming Soon</p>
            <p className="text-gray-500 text-sm mt-2">System settings configuration will be available in Phase 7 implementation</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
