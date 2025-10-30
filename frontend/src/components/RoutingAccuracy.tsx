import React from 'react';

interface RoutingAccuracyProps {
  data: any[];
  loading: boolean;
}

const RoutingAccuracy: React.FC<RoutingAccuracyProps> = ({ data, loading }) => {
  if (loading) {
    return <div className="animate-pulse bg-gray-200 h-64 rounded-lg"></div>;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Routing Accuracy</h3>
      <div className="flex items-center justify-center h-32">
        <p className="text-gray-500">Chart placeholder</p>
      </div>
    </div>
  );
};

export default RoutingAccuracy;