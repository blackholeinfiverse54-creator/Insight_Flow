import React from 'react';
import { AnalyticsOverview } from '../types';

interface MetricsOverviewProps {
  data: AnalyticsOverview | null;
  loading: boolean;
}

const MetricsOverview: React.FC<MetricsOverviewProps> = ({ data, loading }) => {
  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-32 rounded-lg"></div>;
  }

  if (!data) {
    return <div className="text-gray-500">No data available</div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-500">Total Routings</h3>
        <p className="text-2xl font-bold text-gray-900">{data.total_routings}</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-500">Success Rate</h3>
        <p className="text-2xl font-bold text-green-600">{data.success_rate}%</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-500">Avg Latency</h3>
        <p className="text-2xl font-bold text-blue-600">{data.average_latency_ms}ms</p>
      </div>
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-sm font-medium text-gray-500">Active Agents</h3>
        <p className="text-2xl font-bold text-purple-600">{data.active_agents}</p>
      </div>
    </div>
  );
};

export default MetricsOverview;