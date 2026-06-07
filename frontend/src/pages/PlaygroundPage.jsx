import { useState, useEffect } from 'react';
import { Play, Code, Terminal as TermIcon, AlertTriangle, CheckCircle, RefreshCw, Send, HelpCircle } from 'lucide-react';
import { apiJson, api } from '../api/client';
import { useToast } from '../components/ui/Toast';

const TEMPLATES = {
  'user.created': {
    event: 'user.created',
    data: {
      id: 'usr_9J2xK8s1a',
      email: 'alex.jones@example.com',
      full_name: 'Alex Jones',
      plan: 'enterprise',
      created_at: new Date().toISOString()
    }
  },
  'order.paid': {
    event: 'order.paid',
    data: {
      id: 'ord_1M8xL9p2b',
      amount: 14900,
      currency: 'USD',
      status: 'paid',
      customer_id: 'cust_3A7bN4m9x',
      items: [
        { sku: 'rf-api-premium', quantity: 1, name: 'RelayForge API Premium' }
      ],
      paid_at: new Date().toISOString()
    }
  },
  'invoice.payment_failed': {
    event: 'invoice.payment_failed',
    data: {
      id: 'inv_8k2s1d9f',
      customer_email: 'finance@startup.io',
      amount_due: 4900,
      attempt_count: 3,
      next_retry_at: new Date(Date.now() + 86400000).toISOString(),
      reason: 'insufficient_funds'
    }
  }
};

export default function PlaygroundPage() {
  const toast = useToast();
  const [endpoints, setEndpoints] = useState([]);
  const [selectedEndpointId, setSelectedEndpointId] = useState('');
  const [eventType, setEventType] = useState('user.created');
  const [payloadText, setPayloadText] = useState(JSON.stringify(TEMPLATES['user.created'].data, null, 2));
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  
  // Terminal execution state
  const [logs, setLogs] = useState([]);
  const [deliveryResult, setDeliveryResult] = useState(null);
  const [activeTab, setActiveTab] = useState('request'); // 'request' | 'response'

  useEffect(() => {
    const loadEndpoints = async () => {
      try {
        const data = await apiJson('/webhooks/endpoints?limit=100');
        const active = (data.items || []).filter(e => e.status === 'active');
        setEndpoints(active);
        if (active.length > 0) {
          setSelectedEndpointId(active[0].id);
        }
      } catch (err) {
        toast.error('Failed to load webhook endpoints: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    loadEndpoints();
  }, []);

  const handleTemplateChange = (type) => {
    setEventType(type);
    if (TEMPLATES[type]) {
      setPayloadText(JSON.stringify(TEMPLATES[type].data, null, 2));
    } else {
      setPayloadText(JSON.stringify({ custom: true, timestamp: new Date().toISOString() }, null, 2));
    }
  };

  const runSimulation = async () => {
    if (!selectedEndpointId) {
      toast.error('Please create or select an active webhook endpoint first.');
      return;
    }
    
    let parsedPayload;
    try {
      parsedPayload = JSON.parse(payloadText);
    } catch (e) {
      toast.error('Invalid JSON payload');
      return;
    }

    setTriggering(true);
    setDeliveryResult(null);
    
    const timestamp = new Date().toLocaleTimeString();
    setLogs([
      { type: 'info', text: 'Initializing simulation environment...', timestamp },
      { type: 'info', text: `Preparing event: "${eventType}"`, timestamp },
    ]);

    const log = (type, text) => {
      setLogs(prev => [...prev, { type, text, timestamp: new Date().toLocaleTimeString() }]);
    };

    try {
      // 1. Trigger the event through the API
      const res = await api('/events', {
        method: 'POST',
        body: {
          source: 'playground-sandbox',
          event_type: eventType,
          payload: parsedPayload,
          event_key: `play_${Math.random().toString(36).substring(7)}`
        }
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error?.message || 'Ingestion failed');
      }

      const eventData = await res.json();
      log('success', `Event created successfully (ID: ${eventData.id})`);
      log('info', 'Queuing webhook delivery task...');

      // 2. Poll for the delivery object mapping to this event
      let deliveryObj = null;
      let attempts = 0;
      const maxAttempts = 15;

      while (attempts < maxAttempts) {
        attempts++;
        await new Promise(r => setTimeout(r, 1000));
        
        log('poll', `Polling delivery state... (attempt ${attempts}/${maxAttempts})`);

        const delRes = await apiJson(`/deliveries?limit=10`);
        const matchingDelivery = (delRes.items || []).find(d => d.event_id === eventData.id);

        if (matchingDelivery) {
          deliveryObj = matchingDelivery;
          if (matchingDelivery.status !== 'pending' && matchingDelivery.status !== 'queued') {
            break;
          }
        }
      }

      if (!deliveryObj) {
        throw new Error('Delivery timeout: Delivery task did not execute in time.');
      }

      log('success', `Delivery execution captured! Status: ${deliveryObj.status.toUpperCase()}`);

      // 3. Load full details including delivery attempts
      const detailRes = await apiJson(`/deliveries/${deliveryObj.id}`);
      const attemptsRes = await apiJson(`/deliveries/${deliveryObj.id}/attempts`);
      
      setDeliveryResult({
        ...detailRes,
        attempts: attemptsRes.items || []
      });

      if (attemptsRes.items && attemptsRes.items.length > 0) {
        const lastAttempt = attemptsRes.items[attemptsRes.items.length - 1];
        log('info', `[HTTP Status] ${lastAttempt.http_status || 'Connection Refused/Error'}`);
        log('info', `[Latency] ${lastAttempt.duration_ms || 0}ms`);
        if (lastAttempt.http_status >= 200 && lastAttempt.http_status < 300) {
          log('success', 'Webhook successfully delivered!');
        } else {
          log('error', `Webhook failed: HTTP ${lastAttempt.http_status}`);
        }
      } else {
        log('error', 'Delivery attempted but no network logs returned.');
      }

    } catch (err) {
      log('error', `Simulation error: ${err.message}`);
      toast.error(err.message || 'Simulation failed');
    } finally {
      setTriggering(false);
    }
  };

  if (loading) {
    return <div className="page-loader"><div className="loader-spinner" /></div>;
  }

  const selectedEndpoint = endpoints.find(e => e.id === selectedEndpointId);

  return (
    <div className="page-animate">
      <div className="page-header">
        <h2>Developer Sandbox</h2>
        <p className="page-subtitle">Test and debug webhook integrations by triggering live simulations</p>
      </div>

      {endpoints.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-state-icon"><AlertTriangle size={32} /></div>
          <h4>No Active Endpoints</h4>
          <p>You need at least one active webhook endpoint configuration to run a simulation.</p>
          <a href="/webhooks" className="btn btn-primary" style={{ marginTop: '1rem' }}>Create Endpoint</a>
        </div>
      ) : (
        <div className="dashboard-grid" style={{ gridTemplateColumns: '1.1fr 0.9fr', alignItems: 'stretch' }}>
          
          {/* Config Panel */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="card-header" style={{ marginBottom: '1.25rem' }}>
              <h4 className="card-title"><Code size={18} /> Trigger Event Simulation</h4>
            </div>

            <div className="form-group">
              <label className="form-label">Target Webhook Endpoint</label>
              <select 
                className="form-input" 
                value={selectedEndpointId} 
                onChange={e => setSelectedEndpointId(e.target.value)}
              >
                {endpoints.map(ep => (
                  <option key={ep.id} value={ep.id}>{ep.name} ({ep.url})</option>
                ))}
              </select>
              {selectedEndpoint && (
                <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: '0.4rem' }}>
                  Filter: <code>{selectedEndpoint.event_filter}</code>
                </div>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Event Type Template</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {Object.keys(TEMPLATES).map(type => (
                  <button 
                    key={type} 
                    className={`btn btn-sm ${eventType === type ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => handleTemplateChange(type)}
                  >
                    {type}
                  </button>
                ))}
                <button 
                  className={`btn btn-sm ${!TEMPLATES[eventType] ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => handleTemplateChange('custom.event')}
                >
                  Custom...
                </button>
              </div>
            </div>

            {!TEMPLATES[eventType] && (
              <div className="form-group">
                <label className="form-label">Event Type Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={eventType} 
                  onChange={e => setEventType(e.target.value)}
                  placeholder="e.g. user.updated"
                />
              </div>
            )}

            <div className="form-group" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
              <label className="form-label">JSON Payload</label>
              <textarea 
                className="form-input font-mono" 
                style={{ flexGrow: 1, minHeight: '260px', resize: 'vertical', fontSize: '0.85rem', lineHeight: '1.4' }}
                value={payloadText}
                onChange={e => setPayloadText(e.target.value)}
              />
            </div>

            <button 
              className="btn btn-primary btn-lg btn-full" 
              onClick={runSimulation} 
              disabled={triggering}
              style={{ marginTop: '1rem' }}
            >
              {triggering ? (
                <>
                  <RefreshCw size={18} className="spinner" />
                  <span>Simulating...</span>
                </>
              ) : (
                <>
                  <Send size={18} />
                  <span>Fire Webhook Event</span>
                </>
              )}
            </button>
          </div>

          {/* Console Output */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', backgroundColor: 'rgba(15,23,42,0.95)' }}>
            <div className="card-header" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '0.75rem' }}>
              <h4 className="card-title" style={{ color: 'var(--color-primary-light)' }}>
                <TermIcon size={18} /> Live Trace Terminal
              </h4>
              <span className="live-indicator"><span className="live-dot" /> Polling</span>
            </div>

            {/* Terminal Body */}
            <div 
              className="font-mono" 
              style={{ 
                flexGrow: 1, 
                padding: '1.25rem', 
                overflowY: 'auto', 
                fontSize: '0.8rem', 
                color: '#e2e8f0',
                maxHeight: '400px',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.4rem',
                borderBottom: '1px solid rgba(255,255,255,0.06)'
              }}
            >
              {logs.length === 0 ? (
                <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '3rem 0' }}>
                  <HelpCircle size={28} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
                  <div>Sandbox ready. Configure details and click "Fire Webhook Event" to view delivery traces.</div>
                </div>
              ) : (
                logs.map((log, index) => {
                  let color = '#94a3b8';
                  if (log.type === 'success') color = '#4ade80';
                  if (log.type === 'error') color = '#f87171';
                  if (log.type === 'poll') color = 'var(--color-warning)';
                  return (
                    <div key={index} style={{ color }}>
                      <span style={{ opacity: 0.5 }}>[{log.timestamp || new Date().toLocaleTimeString()}]</span> {log.text}
                    </div>
                  );
                })
              )}
            </div>

            {/* Response/Request Payload Inspection */}
            {deliveryResult && deliveryResult.attempts && deliveryResult.attempts.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
                <div className="tabs" style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  <button 
                    className={`tab ${activeTab === 'request' ? 'active' : ''}`}
                    onClick={() => setActiveTab('request')}
                    style={{ flex: 1, padding: '0.75rem', background: 'none', border: 'none', borderBottom: activeTab === 'request' ? '2px solid var(--color-primary)' : 'none', color: '#e2e8f0', cursor: 'pointer' }}
                  >
                    Sent Request
                  </button>
                  <button 
                    className={`tab ${activeTab === 'response' ? 'active' : ''}`}
                    onClick={() => setActiveTab('response')}
                    style={{ flex: 1, padding: '0.75rem', background: 'none', border: 'none', borderBottom: activeTab === 'response' ? '2px solid var(--color-primary)' : 'none', color: '#e2e8f0', cursor: 'pointer' }}
                  >
                    Received Response
                  </button>
                </div>

                <div 
                  className="font-mono" 
                  style={{ 
                    padding: '1.25rem', 
                    fontSize: '0.75rem', 
                    color: '#e2e8f0', 
                    overflowX: 'auto',
                    backgroundColor: 'rgba(0,0,0,0.2)',
                    flexGrow: 1,
                    minHeight: '180px'
                  }}
                >
                  {activeTab === 'request' ? (
                    <div>
                      <div style={{ color: 'var(--color-primary-light)', marginBottom: '0.5rem' }}>Headers:</div>
                      <pre style={{ margin: 0, opacity: 0.85 }}>
{`POST ${selectedEndpoint?.url} HTTP/1.1
Content-Type: application/json
User-Agent: RelayForge/0.1.0
X-RelayForge-Signature: t=1700000000,v1=${deliveryResult.id.slice(0, 16)}...
X-RelayForge-Delivery-ID: ${deliveryResult.id}`}
                      </pre>
                      <div style={{ color: 'var(--color-primary-light)', marginTop: '1rem', marginBottom: '0.5rem' }}>Payload Body:</div>
                      <pre style={{ margin: 0 }}>
                        {(() => {
                          try {
                            return JSON.stringify(JSON.parse(payloadText), null, 2);
                          } catch (e) {
                            return payloadText;
                          }
                        })()}
                      </pre>
                    </div>
                  ) : (
                    <div>
                      <div style={{ color: 'var(--color-primary-light)', marginBottom: '0.5rem' }}>Metadata:</div>
                      <div>HTTP status code: <span style={{ color: deliveryResult.last_status_code >= 200 && deliveryResult.last_status_code < 300 ? '#4ade80' : '#f87171' }}>{deliveryResult.last_status_code || 'ERROR'}</span></div>
                      <div>Latency: {deliveryResult.attempts[0]?.duration_ms || 0}ms</div>
                      <div style={{ color: 'var(--color-primary-light)', marginTop: '1rem', marginBottom: '0.5rem' }}>Response Body:</div>
                      <pre style={{ margin: 0, opacity: 0.85 }}>
                        {deliveryResult.last_response_body || deliveryResult.last_error || 'No body returned'}
                      </pre>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
}
