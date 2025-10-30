import axios from 'axios';
import { AnalyticsOverview, AgentPerformance } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  async getAnalyticsOverview(timeRange: string): Promise<AnalyticsOverview> {
    const response = await api.get(`/api/v1/analytics/overview?time_range=${timeRange}`);
    return response.data;
  },

  async getAgentPerformance(timeRange: string): Promise<{ agents: AgentPerformance[] }> {
    const response = await api.get(`/api/v1/analytics/agent-performance?time_range=${timeRange}`);
    return response.data;
  },
};