import React, { useEffect, useState } from 'react';
import { api } from '../utils/api';
import FileUpload from '../components/FileUpload';
import './Jobs.css';

const Jobs = () => {
  const [jobs, setJobs] = useState([]);
  const [currentJob, setCurrentJob] = useState(null);

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 2000); // Poll every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await api.get('/active-jobs');
      const jobsList = response.data.jobs || [];
      setJobs(jobsList);
      
      // Find current running job and calculate progress
      const running = jobsList.find(job => job.status === 'processing');
      if (running) {
        const progress = running.total > 0 
          ? Math.round((running.processed / running.total) * 100) 
          : 0;
        setCurrentJob({ ...running, progress });
      } else {
        setCurrentJob(null);
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const handleStopJob = async (jobId) => {
    try {
      await api.post(`/stop-job/${jobId}`);
      fetchJobs();
    } catch (error) {
      console.error('Error stopping job:', error);
      alert('Failed to stop job');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10b981';
      case 'processing': return '#667eea';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const handleUploadSuccess = (jobId) => {
    // Refresh jobs list after upload
    fetchJobs();
  };

  return (
    <div className="jobs-page">
      <h1 className="page-title">Jobs</h1>

      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {currentJob && (
        <div className="current-job-section">
          <div className="current-job-header">
            <span>Current Running Job</span>
            <span className="job-arrow">→</span>
          </div>
          
          <div className="progress-section">
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                style={{ 
                  width: `${currentJob.progress || 0}%`,
                  backgroundColor: getStatusColor(currentJob.status)
                }}
              />
            </div>
            <div className="progress-text">
              {currentJob.progress || 0}% Complete
            </div>
          </div>
        </div>
      )}

      <div className="jobs-list">
        <h2 className="section-title">All Jobs</h2>
        {jobs.map((job) => (
          <div key={job.id} className="job-card">
            <div className="job-info">
              <div className="job-name">{job.filename || `Job ${job.id}`}</div>
              <div 
                className="job-status"
                style={{ color: getStatusColor(job.status) }}
              >
                {job.status}
              </div>
            </div>
            {job.status === 'processing' && (
              <button 
                className="stop-btn"
                onClick={() => handleStopJob(job.id)}
              >
                Stop
              </button>
            )}
          </div>
        ))}
        
        {jobs.length === 0 && (
          <div className="empty-state">No jobs found</div>
        )}
      </div>
    </div>
  );
};

export default Jobs;

