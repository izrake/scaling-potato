import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    leadsUploaded: 0,
    leadsEnriched: 0
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [jobsRes, enrichedRes] = await Promise.all([
        api.get('/active-jobs'),
        api.get('/enriched-profiles?page=1&limit=1')
      ]);

      // Calculate total leads uploaded from all jobs
      const totalUploaded = jobsRes.data.jobs?.reduce((sum, job) => sum + (job.total || 0), 0) || 0;
      
      // Get total enriched profiles
      const totalEnriched = enrichedRes.data.total || 0;

      setStats({
        leadsUploaded: totalUploaded,
        leadsEnriched: totalEnriched
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Set defaults on error
      setStats({
        leadsUploaded: 0,
        leadsEnriched: 0
      });
    }
  };

  return (
    <div className="dashboard">
      <h1 className="page-title">Dashboard</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Leads Uploaded</div>
          <div className="stat-value">{stats.leadsUploaded}</div>
          <div className="stat-subtitle">Total Number</div>
        </div>
        
        <div className="stat-card">
          <div className="stat-label">Leads Enriched</div>
          <div className="stat-value">{stats.leadsEnriched}</div>
          <div className="stat-subtitle">Total Number</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

