import React, { useState } from 'react';
import { api } from '../utils/api';
import './FileUpload.css';

const FileUpload = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      if (selectedFile.type !== 'text/csv' && !selectedFile.name.endsWith('.csv')) {
        setError('Please upload a CSV file');
        return;
      }
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Don't set Content-Type header - let browser set it automatically with boundary
      const response = await api.post('/upload', formData);

      if (response.data.job_id) {
        // Automatically start processing
        await api.post(`/process/${response.data.job_id}`, {}, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (onUploadSuccess) {
          onUploadSuccess(response.data.job_id);
        }
        
        setFile(null);
        // Reset file input
        document.getElementById('file-input').value = '';
      }
    } catch (err) {
      console.error('Upload error:', err);
      const errorMessage = err.response?.data?.error || err.message || 'Failed to upload file';
      setError(errorMessage);
      console.error('Full error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="upload-area">
        <input
          id="file-input"
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={uploading}
          style={{ display: 'none' }}
        />
        <label htmlFor="file-input" className="upload-label">
          {file ? file.name : 'Choose CSV File'}
        </label>
        {file && (
          <button 
            className="upload-btn"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        )}
      </div>
      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default FileUpload;

