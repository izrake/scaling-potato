import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import './Settings.css';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('pending');
  const [pendingSettings, setPendingSettings] = useState({
    provider: 'openai',
    apiKey: '',
    model: '',
    systemPrompt: '',
    temperature: '0.7',
    maxTokens: 1000,
    questions: ['What they do:', 'Can we pitch Spheron?:']
  });
  const [reachedSettings, setReachedSettings] = useState({
    provider: 'openai',
    apiKey: '',
    model: '',
    systemPrompt: '',
    temperature: '0.7',
    maxTokens: 1000,
    variables: {}
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    setMessage({ type: '', text: '' });
    try {
      // Load pending settings
      const pendingRes = await api.get('/llm-settings/pending');
      if (pendingRes.data && !pendingRes.data.error) {
        const data = pendingRes.data;
        setPendingSettings({
          provider: data.provider || 'openai',
          apiKey: data.api_key || '',
          model: data.model || '',
          systemPrompt: data.system_prompt || '',
          temperature: data.temperature || '0.7',
          maxTokens: data.max_tokens || 1000,
          questions: data.variables?.questions || ['What they do:', 'Can we pitch Spheron?:']
        });
      } else if (pendingRes.data?.error) {
        throw new Error(pendingRes.data.error);
      }

      // Load reached settings
      const reachedRes = await api.get('/llm-settings/reached');
      if (reachedRes.data && !reachedRes.data.error) {
        const data = reachedRes.data;
        setReachedSettings({
          provider: data.provider || 'openai',
          apiKey: data.api_key || '',
          model: data.model || '',
          systemPrompt: data.system_prompt || '',
          temperature: data.temperature || '0.7',
          maxTokens: data.max_tokens || 1000,
          variables: data.variables || {}
        });
      } else if (reachedRes.data?.error) {
        throw new Error(reachedRes.data.error);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to load settings';
      setMessage({ type: 'error', text: `Error: ${errorMsg}. Please check your backend server is running.` });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (section) => {
    setSaving(true);
    setMessage({ type: '', text: '' });
    
    try {
      const settings = section === 'pending' ? pendingSettings : reachedSettings;
      
      const payload = {
        provider: settings.provider,
        api_key: settings.apiKey,
        model: settings.model,
        system_prompt: settings.systemPrompt,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
        variables: section === 'pending' 
          ? { questions: settings.questions }
          : settings.variables
      };

      await api.post(`/llm-settings/${section}`, payload);
      
      setMessage({ type: 'success', text: `${section === 'pending' ? 'Pending' : 'Reached'} settings saved successfully!` });
      
      // Clear message after 3 seconds
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage({ type: '', text: '' });
    setTestResult(null);
    
    try {
      const settings = activeTab === 'pending' ? pendingSettings : reachedSettings;
      
      // Validate required fields
      if (!settings.provider) {
        setMessage({ type: 'error', text: 'Please select a provider' });
        setTesting(false);
        return;
      }
      
      if (!settings.apiKey) {
        setMessage({ type: 'error', text: 'Please enter an API key' });
        setTesting(false);
        return;
      }
      
      const payload = {
        provider: settings.provider,
        api_key: settings.apiKey,
        model: settings.model,
        system_prompt: settings.systemPrompt,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
        variables: activeTab === 'pending' 
          ? { questions: settings.questions }
          : settings.variables
      };

      const response = await api.post(`/test-llm-settings/${activeTab}`, payload);
      
      if (response.data.success) {
        setTestResult(response.data);
        setMessage({ type: 'success', text: 'Test completed successfully! Check the result below.' });
      }
    } catch (error) {
      console.error('Error testing settings:', error);
      setMessage({ type: 'error', text: error.response?.data?.error || 'Failed to test settings. Please check your API key and configuration.' });
      setTestResult(null);
    } finally {
      setTesting(false);
    }
  };

  const handlePendingChange = (field, value) => {
    setPendingSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleReachedChange = (field, value) => {
    setReachedSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const addQuestion = () => {
    setPendingSettings(prev => ({
      ...prev,
      questions: [...prev.questions, '']
    }));
  };

  const updateQuestion = (index, value) => {
    setPendingSettings(prev => ({
      ...prev,
      questions: prev.questions.map((q, i) => i === index ? value : q)
    }));
  };

  const removeQuestion = (index) => {
    setPendingSettings(prev => ({
      ...prev,
      questions: prev.questions.filter((_, i) => i !== index)
    }));
  };

  const getModelOptions = (provider) => {
    if (provider === 'openai') {
      return [
        { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
        { value: 'gpt-4o', label: 'GPT-4o' },
        { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
        { value: 'gpt-4', label: 'GPT-4' },
        { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
      ];
    } else if (provider === 'gemini') {
      return [
        { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
        { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
        { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' }
      ];
    }
    return [];
  };

  if (loading) {
    return (
      <div className="settings-page">
        <div className="loading">Loading settings...</div>
      </div>
    );
  }

  const currentSettings = activeTab === 'pending' ? pendingSettings : reachedSettings;

  return (
    <div className="settings-page">
      <h1 className="page-title">LLM Settings</h1>

      <div className="settings-tabs">
        <button
          className={`tab-button ${activeTab === 'pending' ? 'active' : ''}`}
          onClick={() => setActiveTab('pending')}
        >
          Pending Leads
        </button>
        <button
          className={`tab-button ${activeTab === 'reached' ? 'active' : ''}`}
          onClick={() => setActiveTab('reached')}
        >
          Reached Leads
        </button>
      </div>

      {message.text && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="settings-container">
        <div className="settings-section">
          <label className="settings-label">LLM Provider</label>
          <select
            className="settings-input"
            value={currentSettings.provider}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('provider', e.target.value);
              } else {
                handleReachedChange('provider', e.target.value);
              }
            }}
          >
            <option value="openai">OpenAI</option>
            <option value="gemini">Google Gemini</option>
          </select>
        </div>

        <div className="settings-section">
          <label className="settings-label">API Key</label>
          <input
            type="password"
            className="settings-input"
            value={currentSettings.apiKey}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('apiKey', e.target.value);
              } else {
                handleReachedChange('apiKey', e.target.value);
              }
            }}
            placeholder={`Enter your ${currentSettings.provider === 'openai' ? 'OpenAI' : 'Gemini'} API key`}
          />
        </div>

        <div className="settings-section">
          <label className="settings-label">Model</label>
          <select
            className="settings-input"
            value={currentSettings.model}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('model', e.target.value);
              } else {
                handleReachedChange('model', e.target.value);
              }
            }}
          >
            <option value="">Select a model</option>
            {getModelOptions(currentSettings.provider).map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="settings-section">
          <label className="settings-label">Temperature</label>
          <input
            type="number"
            className="settings-input"
            value={currentSettings.temperature}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('temperature', e.target.value);
              } else {
                handleReachedChange('temperature', e.target.value);
              }
            }}
            min="0"
            max="2"
            step="0.1"
            placeholder="0.7"
          />
          <small className="settings-hint">Controls randomness (0.0 = deterministic, 2.0 = very creative)</small>
        </div>

        <div className="settings-section">
          <label className="settings-label">Max Tokens</label>
          <input
            type="number"
            className="settings-input"
            value={currentSettings.maxTokens}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('maxTokens', parseInt(e.target.value) || 1000);
              } else {
                handleReachedChange('maxTokens', parseInt(e.target.value) || 1000);
              }
            }}
            min="100"
            max="4000"
            placeholder="1000"
          />
        </div>

        <div className="settings-section">
          <label className="settings-label">System Prompt</label>
          <textarea
            className="system-prompt-textarea"
            value={currentSettings.systemPrompt}
            onChange={(e) => {
              if (activeTab === 'pending') {
                handlePendingChange('systemPrompt', e.target.value);
              } else {
                handleReachedChange('systemPrompt', e.target.value);
              }
            }}
            placeholder={
              activeTab === 'pending'
                ? "Enter system prompt for analyzing pending leads. Use {full_name}, {company_name}, {about_section} as variables."
                : "Enter system prompt for generating outreach messages. Use {full_name}, {company_name}, {about_section}, {company_description} as variables."
            }
            rows={8}
          />
        </div>

        {activeTab === 'pending' && (
          <div className="settings-section">
            <div className="settings-label-row">
              <label className="settings-label">Questions to Answer</label>
              <button className="add-question-btn" onClick={addQuestion}>
                + Add Question
              </button>
            </div>
            {pendingSettings.questions.map((question, index) => (
              <div key={index} className="question-input-group">
                <input
                  type="text"
                  className="settings-input question-input"
                  value={question}
                  onChange={(e) => updateQuestion(index, e.target.value)}
                  placeholder={`Question ${index + 1}`}
                />
                <button
                  className="remove-question-btn"
                  onClick={() => removeQuestion(index)}
                  disabled={pendingSettings.questions.length === 1}
                >
                  ×
                </button>
              </div>
            ))}
            <small className="settings-hint">
              These questions will be answered by the LLM based on the lead's profile information.
            </small>
          </div>
        )}

        <div className="settings-actions">
          <button
            className="test-btn"
            onClick={handleTest}
            disabled={testing || saving}
          >
            {testing ? 'Testing...' : 'Test Settings'}
          </button>
          <button
            className="save-btn"
            onClick={() => handleSave(activeTab)}
            disabled={saving || testing}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>

        {testResult && (
          <div className="test-result">
            <h3 className="test-result-title">Test Result</h3>
            
            <div className="test-data-section">
              <h4>Test Data Used:</h4>
              <div className="test-data">
                {testResult.test_data && Object.entries(testResult.test_data).map(([key, value]) => (
                  <div key={key} className="test-data-item">
                    <strong>{key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                    <span>{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {activeTab === 'pending' && testResult.response && (
              <div className="test-response-section">
                <h4>Generated Response:</h4>
                <div className="test-response-content">
                  {testResult.response}
                </div>
                <button
                  className="copy-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(testResult.response);
                    alert('Copied to clipboard!');
                  }}
                >
                  Copy Response
                </button>
              </div>
            )}

            {activeTab === 'reached' && (
              <>
                {testResult.email && (
                  <div className="test-response-section">
                    <h4>Generated Email:</h4>
                    <div className="test-response-content">
                      {testResult.email}
                    </div>
                    <button
                      className="copy-btn"
                      onClick={() => {
                        navigator.clipboard.writeText(testResult.email);
                        alert('Copied to clipboard!');
                      }}
                    >
                      Copy Email
                    </button>
                  </div>
                )}
                
                {testResult.linkedin_message && (
                  <div className="test-response-section">
                    <h4>Generated LinkedIn Message:</h4>
                    <div className="test-response-content">
                      {testResult.linkedin_message}
                    </div>
                    <button
                      className="copy-btn"
                      onClick={() => {
                        navigator.clipboard.writeText(testResult.linkedin_message);
                        alert('Copied to clipboard!');
                      }}
                    >
                      Copy LinkedIn Message
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;
