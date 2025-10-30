import React from 'react';
import { WebSocketMessage } from '../types';

interface RecentRoutingsProps {
  routings: WebSocketMessage[];
  loading: boolean;
}

const RecentRoutings: React.FC<RecentRoutingsProps> = ({ routings, loading }) => {
  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-64 rounded-lg"></div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Routings</h3>
      <div className="space-y-3">
        {routings.length === 0 ? (
          <p className="text-gray-500">No recent routings</p>
        ) : (
          routings.slice(0, 10).map((routing, index) => (
            <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100">
              <div>
                <p className="text-sm font-medium text-gray-900">Routing #{index + 1}</p>
                <p className="text-xs text-gray-500">{routing.type}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">{routing.timestamp || 'Now'}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RecentRoutings;