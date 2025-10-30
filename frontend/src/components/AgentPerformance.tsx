import React from 'react';
import { AgentPerformance } from '../types';

interface AgentPerformanceChartProps {
  agents: AgentPerformance[];
  loading: boolean;
}

const AgentPerformanceChart: React.FC<AgentPerformanceChartProps> = ({ agents, loading }) => {
  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-64 rounded-lg"></div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Agent Performance</h3>
      <div className="space-y-4">
        {agents.map((agent) => (
          <div key={agent.agent_id} className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">{agent.agent_name}</p>
              <p className="text-sm text-gray-500">{agent.agent_type}</p>
            </div>
            <div className="text-right">
              <p className="font-medium text-gray-900">{(agent.performance_score * 100).toFixed(1)}%</p>
              <p className="text-sm text-gray-500">{agent.total_requests} requests</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentPerformanceChart;