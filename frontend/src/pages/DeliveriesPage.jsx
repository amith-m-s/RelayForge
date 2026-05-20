import { useState, useEffect } from 'react';
import { Truck, RefreshCw, ChevronDown, ChevronRight, Search, Filter } from 'lucide-react';
import { apiJson } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/ui/Toast';

export default function DeliveriesPage() {
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [attempts, setAttempts] = useState({});
  const { addToast } = useToast();

  const load = async () => {
    try {
      const params = new URLSearchParams({ limit: '50' });
      if (statusFilter) params.set('status', statusFilter);
      const data = await apiJson(`/deliveries?${params}`);
      setDeliveries(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, [statusFilter]);

  const loadAttempts = async (deliveryId) => {
    if (attempts[deliveryId]) return;
    try {
      const data = await apiJson(`/deliveries/${deliveryId}/attempts`);
      setAttempts(prev => ({ ...prev, [deliveryId]: data.items || [] }));
    } catch { /* ignore */ }
  };

  const toggleExpand = (id) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    loadAttempts(id);
  };

  const replay = async (id) => {
    try {
      await apiJson(`/deliveries/${id}/replay`, { method: 'POST' });
      addToast('Delivery replay queued', 'success');
      load();
    } catch (err) {
      addToast(err.message, 'error');
    }
  };

  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Deliveries</h2>
          <p className="page-subtitle">Track and manage webhook delivery attempts</p>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <Filter size={16} />
          <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="succeeded">Succeeded</option>
            <option value="failed">Failed</option>
            <option value="dead_letter">Dead Letter</option>
          </select>
        </div>
      </div>

      {deliveries.length === 0 ? (
        <EmptyState icon={Truck} title="No deliveries" description="Deliveries will appear here when events are dispatched." />
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th></th>
                  <th>Delivery ID</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Last Code</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map(d => (
                  <>
                    <tr key={d.id} className="table-row-clickable" onClick={() => toggleExpand(d.id)}>
                      <td style={{width:30}}>{expanded === d.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</td>
                      <td className="font-mono text-sm">{d.id?.slice(0, 12)}…</td>
                      <td><StatusBadge status={d.status} /></td>
                      <td>{d.attempt_count}</td>
                      <td>{d.last_status_code || '—'}</td>
                      <td className="text-muted text-sm">{new Date(d.created_at).toLocaleString()}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm" onClick={(e) => { e.stopPropagation(); replay(d.id); }} title="Replay">
                          <RefreshCw size={14} />
                        </button>
                      </td>
                    </tr>
                    {expanded === d.id && (
                      <tr key={`${d.id}-attempts`} className="detail-row">
                        <td colSpan={7}>
                          <div className="attempt-timeline">
                            <h5 className="attempt-timeline-title">Delivery Attempts</h5>
                            {!attempts[d.id] ? (
                              <div className="loader-spinner" style={{margin:'1rem auto'}} />
                            ) : attempts[d.id].length === 0 ? (
                              <p className="text-muted">No attempts yet</p>
                            ) : (
                              <div className="timeline">
                                {attempts[d.id].map((a, i) => (
                                  <div key={i} className={`timeline-item ${a.http_status && a.http_status < 300 ? 'success' : 'error'}`}>
                                    <div className="timeline-dot" />
                                    <div className="timeline-content">
                                      <div className="timeline-header">
                                        <span className="timeline-attempt">Attempt #{a.attempt_number}</span>
                                        <span className={`timeline-status ${a.http_status && a.http_status < 300 ? 'text-success' : 'text-error'}`}>
                                          {a.http_status || 'Error'}
                                        </span>
                                        {a.duration_ms && <span className="text-muted text-sm">{a.duration_ms}ms</span>}
                                      </div>
                                      {a.error_message && <p className="timeline-error">{a.error_message}</p>}
                                      <span className="text-muted text-xs">{a.created_at ? new Date(a.created_at).toLocaleString() : ''}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
