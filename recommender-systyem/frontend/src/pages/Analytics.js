import React, { useState, useEffect } from 'react';
import './Analytics.css';

export default function Analytics() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Fetch analytics data
    fetch('/api/analytics/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error('Failed to fetch analytics:', err));
  }, []);

  if (!stats) return <div>Loading analytics...</div>;

  return (
    <div className="analytics">
      <h1>Analytics Dashboard</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Users</h3>
          <p>{stats.total_users}</p>
        </div>
        <div className="stat-card">
          <h3>Total Products</h3>
          <p>{stats.total_products}</p>
        </div>
        <div className="stat-card">
          <h3>Total Ratings</h3>
          <p>{stats.total_ratings}</p>
        </div>
        <div className="stat-card">
          <h3>Average Rating</h3>
          <p>{stats.avg_rating?.toFixed(2)}</p>
        </div>
      </div>
    </div>
  );
}