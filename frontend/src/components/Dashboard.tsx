import React, { useEffect, useState, useCallback } from 'react';
import { apiService } from '../services/api';
import { wsService } from '../services/websocket';
import MetricsOverview from './MetricsOverview';
import AgentPerformanceChart from './AgentPerformance';
import RoutingAccuracy from './RoutingAccuracy';
import RecentRoutings from './RecentRoutings';
import { AnalyticsOverview, AgentPerformance, WebSocketMessage } from '../types';

const Dashboard: React.FC = () => {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [agentPerformance, setAgentPerformance] = useState<AgentPerformance[]>([]);
  const [recentRoutings, setRecentRoutings] = useState<WebSocketMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [overviewData, performanceData] = await Promise.all([
        apiService.getAnalyticsOverview(timeRange),
        apiService.getAgentPerformance(timeRange),
      ]);
      
      setOverview(overviewData);
      setAgentPerformance(performanceData.agents);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'routing_event') {
      setRecentRoutings((prev: WebSocketMessage[]) => [message, ...prev.slice(0, 49)]);
    } else if (message.type === 'performance_update') {
      loadDashboardData();
    }
  }, [loadDashboardData]);

  useEffect(() => {
    loadDashboardData();
    
    wsService.connect();
    const unsubscribe = wsService.subscribe(handleWebSocketMessage);
    
    const interval = setInterval(loadDashboardData, 30000);
    
    return () => {
      unsubscribe();
      clearInterval(interval);
    };
  }, [timeRange, handleWebSocketMessage, loadDashboardData]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">InsightFlow Dashboard</h1>
            <div className="flex space-x-2">
              {['1h', '24h', '7d', '30d'].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    timeRange === range
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <MetricsOverview data={overview} loading={loading} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <AgentPerformanceChart agents={agentPerformance} loading={loading} />
            <RoutingAccuracy data={[]} loading={loading} />
          </div>

          <RecentRoutings routings={recentRoutings} loading={loading} />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;