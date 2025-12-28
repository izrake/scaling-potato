import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import './Leads.css';

const Leads = () => {
  const [activeTab, setActiveTab] = useState('raw_lead');
  const [leads, setLeads] = useState([]);
  const [currentLead, setCurrentLead] = useState(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [llmResponse, setLlmResponse] = useState(null);
  const [error, setError] = useState(null);
  const [pendingAnalysis, setPendingAnalysis] = useState({
    whatTheyDo: '',
    canWePitch: ''
  });
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchLeads();
  }, [activeTab]);

  // Load saved analysis when switching leads (no auto-analysis on load)
  useEffect(() => {
    if (activeTab === 'raw_lead' && currentLead) {
      // Load saved analysis from database if available
      if (currentLead.llm_analysis_what_they_do || currentLead.llm_analysis_can_we_pitch) {
        setPendingAnalysis({
          whatTheyDo: currentLead.llm_analysis_what_they_do || '',
          canWePitch: currentLead.llm_analysis_can_we_pitch || ''
        });
      } else {
        // Clear if no saved analysis
        setPendingAnalysis({ whatTheyDo: '', canWePitch: '' });
      }
      setError(null);
    } else {
      // Clear analysis when switching tabs
      setPendingAnalysis({ whatTheyDo: '', canWePitch: '' });
    }
  }, [currentLead?.id, activeTab]);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      // Map tab names to lead_status values
      const statusMap = {
        'raw_lead': 'raw_lead',
        'qualified': 'qualified',
        'contacted': 'contacted'
      };
      
      const leadStatus = statusMap[activeTab] || 'raw_lead';
      const response = await api.get(`/enriched-profiles?page=1&limit=100&lead_status=${leadStatus}`);
      const profiles = response.data.profiles || [];
      
      setLeads(profiles);
      if (profiles.length > 0) {
        // If current lead is not in the new list, go to first lead
        if (!currentLead || !profiles.find(p => p.id === currentLead.id)) {
          setCurrentLead(profiles[0]);
          setCurrentIndex(0);
        } else {
          // Update current lead if it exists in new data
          const updatedLead = profiles.find(p => p.id === currentLead.id);
          if (updatedLead) {
            setCurrentLead(updatedLead);
            // Update index to match new position
            const newIndex = profiles.findIndex(p => p.id === currentLead.id);
            if (newIndex !== -1) {
              setCurrentIndex(newIndex);
            }
          }
        }
      } else {
        setCurrentLead(null);
        setCurrentIndex(0);
      }
    } catch (error) {
      console.error('Error fetching leads:', error);
      setLeads([]);
      setCurrentLead(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSwipe = (direction) => {
    if (direction === 'left') {
      // Left swipe - keep in current tab (no action for now, or could remove)
      // For now, we'll just move to next lead
      handleNext();
    } else if (direction === 'right') {
      // Right swipe - move to qualified
      if (activeTab === 'raw_lead') {
        handleStatusChange('qualified');
      }
    }
  };

  const handleMarkAsContacted = async () => {
    if (!currentLead) return;
    
    try {
      await api.post(`/update-lead-status/${currentLead.id}`, { 
        lead_status: 'contacted' 
      });
      
      // Move to next lead in current list
      const nextIndex = currentIndex + 1;
      if (nextIndex < leads.length) {
        setCurrentIndex(nextIndex);
        setCurrentLead(leads[nextIndex]);
      } else {
        // No more leads in current tab, refresh list
        fetchLeads();
      }
    } catch (error) {
      console.error('Error marking as contacted:', error);
      alert('Failed to mark as contacted. Please try again.');
    }
  };

  const handleStatusChange = async (newStatus) => {
    if (!currentLead) return;
    
    try {
      // Update lead status on backend
      await api.post(`/update-lead-status/${currentLead.id}`, { 
        lead_status: newStatus 
      });
      
      // Move to next lead in current list (don't switch tabs)
      const nextIndex = currentIndex + 1;
      if (nextIndex < leads.length) {
        setCurrentIndex(nextIndex);
        setCurrentLead(leads[nextIndex]);
        setPendingAnalysis({ whatTheyDo: '', canWePitch: '' }); // Clear analysis for new lead
      } else {
        // No more leads in current tab, refresh list to get updated data
        fetchLeads();
      }
    } catch (error) {
      console.error('Error updating lead status:', error);
      alert('Failed to update lead status. Please try again.');
    }
  };

  const handleNext = () => {
    if (currentIndex < leads.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      setCurrentLead(leads[nextIndex]);
      setPendingAnalysis({ whatTheyDo: '', canWePitch: '' }); // Clear analysis
    }
  };

  const analyzePendingLead = async () => {
    if (!currentLead || activeTab !== 'raw_lead') return;
    
    setAnalyzing(true);
    setError(null);
    setPendingAnalysis({ whatTheyDo: '', canWePitch: '' });
    
    try {
      console.log('Analyzing lead:', currentLead.id);
      const response = await api.post(`/generate-lead-response/${currentLead.id}`, {
        section: 'pending'
      });
      
      console.log('LLM Response received:', response.data);
      
      if (response.data.success && response.data.response) {
        // Parse the JSON response
        let parsedResponse;
        try {
          // Try to parse as JSON if it's a string
          if (typeof response.data.response === 'string') {
            // Try to extract JSON from markdown code blocks if present
            let jsonString = response.data.response.trim();
            if (jsonString.startsWith('```')) {
              // Remove markdown code block markers
              jsonString = jsonString.replace(/^```json\s*/, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
            }
            parsedResponse = JSON.parse(jsonString);
          } else {
            parsedResponse = response.data.response;
          }
          console.log('Parsed response:', parsedResponse);
        } catch (e) {
          console.error('Failed to parse JSON response:', e);
          console.log('Raw response:', response.data.response);
          // If parsing fails, try to extract from text
          parsedResponse = response.data.response;
        }
        
        // Extract "What they do" value (try multiple key variations)
        const whatTheyDo = parsedResponse['What they do'] || 
                          parsedResponse['what_they_do'] || 
                          parsedResponse['What They Do'] ||
                          parsedResponse['whatTheyDo'] ||
                          parsedResponse['What They Do:'] ||
                          '';
        
        console.log('Extracted whatTheyDo:', whatTheyDo);
        
        // Extract "Can we pitch Spheron?" value (try multiple key variations)
        let canWePitch = '';
        const pitchData = parsedResponse['Can we pitch Spheron?'] || 
                         parsedResponse['can_we_pitch_spheron'] ||
                         parsedResponse['Can We Pitch Spheron?'] ||
                         parsedResponse['canWePitchSpheron'] ||
                         parsedResponse['Can we pitch Spheron?:'];
        
        console.log('Extracted pitchData:', pitchData);
        console.log('Type of pitchData:', typeof pitchData);
        
        if (pitchData) {
          if (typeof pitchData === 'object' && pitchData !== null && !Array.isArray(pitchData)) {
            // Format: { "Verdict": "YES/NO", "Reasoning": "...", "The Hook": "..." }
            const verdict = pitchData.Verdict || pitchData.verdict || pitchData.VERDICT || '';
            const reasoning = pitchData.Reasoning || pitchData.reasoning || pitchData.REASONING || '';
            const hook = pitchData['The Hook'] || pitchData.the_hook || pitchData.theHook || '';
            
            // Build the formatted string
            let formattedText = '';
            if (verdict) {
              formattedText += `Verdict: ${verdict}`;
            }
            if (reasoning) {
              if (formattedText) formattedText += '\n\n';
              formattedText += `Reasoning: ${reasoning}`;
            }
            if (hook) {
              if (formattedText) formattedText += '\n\n';
              formattedText += `The Hook: ${hook}`;
            }
            
            canWePitch = formattedText || JSON.stringify(pitchData, null, 2);
          } else {
            canWePitch = String(pitchData);
          }
        }
        
        console.log('Final canWePitch:', canWePitch);
        
        console.log('Final analysis:', { whatTheyDo, canWePitch });
        
        setPendingAnalysis({
          whatTheyDo: whatTheyDo,
          canWePitch: canWePitch
        });
      } else {
        console.warn('No response data or success flag:', response.data);
      }
    } catch (error) {
      console.error('Error analyzing pending lead:', error);
      console.error('Error details:', error.response?.data);
      // Show error to user for debugging
      setError(error.response?.data?.error || 'Failed to analyze lead. Check console for details.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      setCurrentIndex(prevIndex);
      setCurrentLead(leads[prevIndex]);
      setLlmResponse(null); // Clear LLM response when switching leads
      setError(null);
      setPendingAnalysis({ whatTheyDo: '', canWePitch: '' }); // Clear analysis
    }
  };

  const handleGenerateResponse = async () => {
    if (!currentLead) return;
    
    setGenerating(true);
    setError(null);
    setLlmResponse(null);
    
    try {
      const response = await api.post(`/generate-lead-response/${currentLead.id}`, {
        section: activeTab === 'raw_lead' ? 'pending' : (activeTab === 'qualified' ? 'reached' : 'reached')
      });
      
      if (activeTab === 'raw_lead') {
        // Parse and update the text boxes, not just show JSON
        if (response.data.success && response.data.response) {
          // Parse the JSON response
          let parsedResponse;
          try {
            if (typeof response.data.response === 'string') {
              let jsonString = response.data.response.trim();
              if (jsonString.startsWith('```')) {
                jsonString = jsonString.replace(/^```json\s*/, '').replace(/^```\s*/, '').replace(/\s*```$/, '');
              }
              parsedResponse = JSON.parse(jsonString);
            } else {
              parsedResponse = response.data.response;
            }
          } catch (e) {
            console.error('Failed to parse JSON response:', e);
            parsedResponse = response.data.response;
          }
          
          // Extract "What they do" value
          const whatTheyDo = parsedResponse['What they do'] || 
                            parsedResponse['what_they_do'] || 
                            parsedResponse['What They Do'] ||
                            parsedResponse['whatTheyDo'] ||
                            parsedResponse['What They Do:'] ||
                            '';
          
          // Extract "Can we pitch Spheron?" value
          let canWePitch = '';
          const pitchData = parsedResponse['Can we pitch Spheron?'] || 
                           parsedResponse['can_we_pitch_spheron'] ||
                           parsedResponse['Can We Pitch Spheron?'] ||
                           parsedResponse['canWePitchSpheron'] ||
                           parsedResponse['Can we pitch Spheron?:'];
          
          if (pitchData) {
            if (typeof pitchData === 'object' && pitchData !== null && !Array.isArray(pitchData)) {
              const verdict = pitchData.Verdict || pitchData.verdict || pitchData.VERDICT || '';
              const reasoning = pitchData.Reasoning || pitchData.reasoning || pitchData.REASONING || '';
              const hook = pitchData['The Hook'] || pitchData.the_hook || pitchData.theHook || '';
              const pitchAngle = pitchData['The Pitch Angle'] || pitchData.the_pitch_angle || pitchData.thePitchAngle || '';
              
              let formattedText = '';
              if (verdict) {
                formattedText += `Verdict: ${verdict}`;
              }
              if (reasoning) {
                if (formattedText) formattedText += '\n\n';
                formattedText += `Reasoning: ${reasoning}`;
              }
              if (pitchAngle) {
                if (formattedText) formattedText += '\n\n';
                formattedText += `The Pitch Angle: ${pitchAngle}`;
              }
              if (hook) {
                if (formattedText) formattedText += '\n\n';
                formattedText += `The Hook: ${hook}`;
              }
              
              canWePitch = formattedText || JSON.stringify(pitchData, null, 2);
            } else {
              canWePitch = String(pitchData);
            }
          }
          
          // Update the text boxes
          setPendingAnalysis({
            whatTheyDo: whatTheyDo,
            canWePitch: canWePitch
          });
        }
        
        // Don't show JSON output for raw_lead - text boxes are updated directly
        setLlmResponse(null);
      } else if (activeTab === 'qualified' || activeTab === 'contacted') {
        // Messages are already saved to DB by backend, just refresh to get them
        // Also set in state for immediate display
        setLlmResponse({
          type: 'reached',
          email: response.data.email,
          linkedin_message: response.data.linkedin_message
        });
        // Refresh lead to get updated messages from DB
        fetchLeads();
      }
    } catch (err) {
      console.error('Error generating response:', err);
      setError(err.response?.data?.error || 'Failed to generate response. Please check your LLM settings.');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    }).catch(err => {
      console.error('Failed to copy:', err);
      alert('Failed to copy to clipboard');
    });
  };

  // Parse name into first and last name (if currentLead exists)
  const fullName = currentLead?.name || '';
  const nameParts = fullName.trim().split(/\s+/);
  const firstName = currentLead?.csv_firstname || nameParts[0] || '';
  const lastName = currentLead?.csv_lastname || nameParts.slice(1).join(' ') || '';

  return (
    <div className="leads-page">
      <h1 className="page-title">Leads</h1>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'raw_lead' ? 'active' : ''}`}
          onClick={() => setActiveTab('raw_lead')}
        >
          Raw Lead
        </button>
        <button 
          className={`tab ${activeTab === 'qualified' ? 'active' : ''}`}
          onClick={() => setActiveTab('qualified')}
        >
          Qualified
        </button>
        <button 
          className={`tab ${activeTab === 'contacted' ? 'active' : ''}`}
          onClick={() => setActiveTab('contacted')}
        >
          Contacted
        </button>
      </div>

      {loading ? (
        <div className="empty-state">Loading leads...</div>
      ) : !currentLead ? (
        <div className="empty-state">
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📭</div>
          <div style={{ fontSize: '18px', fontWeight: '500', marginBottom: '8px', color: '#333' }}>
            No leads available
          </div>
          <div style={{ fontSize: '14px', color: '#666' }}>
            {activeTab === 'raw_lead' && 'No raw leads. Upload a CSV file to get started.'}
            {activeTab === 'qualified' && 'No qualified leads yet. Swipe right on raw leads to move them here.'}
            {activeTab === 'contacted' && 'No contacted leads yet. Mark qualified leads as contacted to move them here.'}
          </div>
        </div>
      ) : (

      <div className="lead-detail-card">
        <div className="lead-navigation">
          <button 
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            className="nav-btn"
          >
            ← Previous
          </button>
          <span className="lead-counter">
            {currentIndex + 1} of {leads.length}
          </span>
          <button 
            onClick={handleNext}
            disabled={currentIndex === leads.length - 1}
            className="nav-btn"
          >
            Next →
          </button>
        </div>

        <div className="lead-field">
          <label>Full Name:</label>
          <input type="text" value={fullName || ''} readOnly />
        </div>

        <div className="lead-field">
          <label>LinkedIn:</label>
          <input 
            type="text" 
            value={currentLead.linkedin_url || ''} 
            readOnly 
          />
        </div>

        <div className="lead-field">
          <label>Website:</label>
          <input 
            type="text" 
            value={currentLead.website || ''} 
            readOnly 
          />
        </div>

        <div className="lead-field">
          <label>Email:</label>
          <input 
            type="text" 
            value={currentLead.email || 'if available'} 
            readOnly 
          />
        </div>

        <div className="lead-field">
          <label>About:</label>
          <textarea 
            readOnly
            value={currentLead.company_description || 'AI powered description generated from the company scraped content'}
            rows={4}
          />
        </div>

        {activeTab === 'raw_lead' && (
          <>
            <div className="lead-field">
              <label>
                What they do:
                {(analyzing || generating) && <span className="analyzing-indicator"> (Analyzing...)</span>}
              </label>
              <textarea 
                readOnly 
                value={pendingAnalysis.whatTheyDo || currentLead.company_name || ''} 
                rows={3}
                placeholder={(analyzing || generating) ? 'Analyzing lead...' : (pendingAnalysis.whatTheyDo ? '' : 'Click "Generate Analysis" to get results')}
              />
              {error && <div className="error-message" style={{ marginTop: '8px', fontSize: '12px', color: '#dc2626' }}>{error}</div>}
              {!generating && !analyzing && !pendingAnalysis.whatTheyDo && !error && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
                  Click "Generate Analysis" to analyze this lead
                </div>
              )}
            </div>

            <div className="lead-field">
              <label>
                Can we pitch Spheron?:
                {(analyzing || generating) && <span className="analyzing-indicator"> (Analyzing...)</span>}
              </label>
              <textarea 
                readOnly 
                rows={4}
                value={pendingAnalysis.canWePitch || ''}
                placeholder={(analyzing || generating) ? 'Analyzing lead...' : (pendingAnalysis.canWePitch ? '' : 'Click "Generate Analysis" to get results')}
              />
            </div>

            <div className="llm-section">
              <div className="llm-header">
                <h3>LLM Analysis</h3>
                <button 
                  className="generate-btn"
                  onClick={handleGenerateResponse}
                  disabled={generating || analyzing}
                >
                  {generating || analyzing ? 'Generating...' : 'Generate Analysis'}
                </button>
              </div>
              
              {error && (
                <div className="error-message">{error}</div>
              )}
              
              {/* JSON output removed - results are shown in the text boxes above */}
            </div>
          </>
        )}

        {(activeTab === 'qualified' || activeTab === 'contacted') && (
          <>
            <div className="lead-field">
              <label>
                Generated Email:
                {generating && <span className="analyzing-indicator"> (Generating...)</span>}
              </label>
              <textarea 
                readOnly 
                value={currentLead.generated_email || (llmResponse?.type === 'reached' ? llmResponse.email : '') || ''} 
                rows={6}
                placeholder={generating ? 'Generating email...' : (currentLead.generated_email ? '' : 'Click "Generate Messages" to create email')}
              />
              {currentLead.generated_email && (
                <button 
                  className="copy-btn"
                  onClick={() => copyToClipboard(currentLead.generated_email)}
                  style={{ marginTop: '8px' }}
                >
                  Copy Email
                </button>
              )}
            </div>

            <div className="lead-field">
              <label>
                Generated LinkedIn Message:
                {generating && <span className="analyzing-indicator"> (Generating...)</span>}
              </label>
              <textarea 
                readOnly 
                rows={6}
                value={currentLead.generated_linkedin_connection || (llmResponse?.type === 'reached' ? llmResponse.linkedin_message : '') || ''}
                placeholder={generating ? 'Generating LinkedIn message...' : (currentLead.generated_linkedin_connection ? '' : 'Click "Generate Messages" to create LinkedIn message')}
              />
              {currentLead.generated_linkedin_connection && (
                <button 
                  className="copy-btn"
                  onClick={() => copyToClipboard(currentLead.generated_linkedin_connection)}
                  style={{ marginTop: '8px' }}
                >
                  Copy LinkedIn Message
                </button>
              )}
            </div>

            {activeTab === 'qualified' && (
              <div className="llm-section">
                <div className="llm-header">
                  <h3>Outreach Messages</h3>
                  <button 
                    className="generate-btn"
                    onClick={handleGenerateResponse}
                    disabled={generating}
                  >
                    {generating ? 'Generating...' : 'Generate Messages'}
                  </button>
                </div>
                
                {error && (
                  <div className="error-message">{error}</div>
                )}
              </div>
            )}

            {activeTab === 'contacted' && currentLead.contacted_date && (
              <div className="lead-field">
                <label>Contacted Date:</label>
                <input 
                  type="text" 
                  value={new Date(currentLead.contacted_date).toLocaleString()} 
                  readOnly 
                />
              </div>
            )}
          </>
        )}

        {activeTab === 'raw_lead' && (
          <div className="swipe-actions">
            <div className="swipe-action left" onClick={() => handleSwipe('left')}>
              <span>←</span>
              <div>Skip</div>
            </div>
            <div className="swipe-action right" onClick={() => handleSwipe('right')}>
              <div>Right SWIPE (Move to Qualified)</div>
              <span>→</span>
            </div>
          </div>
        )}

        {activeTab === 'qualified' && (
          <div className="swipe-actions">
            <div className="swipe-action left" onClick={() => handleSwipe('left')}>
              <span>←</span>
              <div>Skip</div>
            </div>
            <div className="swipe-action right" onClick={handleMarkAsContacted} style={{ background: '#10b981', color: 'white' }}>
              <div>Mark as Contacted</div>
              <span>✓</span>
            </div>
          </div>
        )}

        {activeTab === 'contacted' && (
          <div className="swipe-actions" style={{ justifyContent: 'center' }}>
            <div style={{ padding: '12px 24px', color: '#666', fontSize: '14px' }}>
              This lead has been contacted
            </div>
          </div>
        )}
      </div>
      )}
    </div>
  );
};

export default Leads;
