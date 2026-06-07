import { useState, useEffect } from 'react';
import { Calendar, Webhook, CheckCircle, XCircle, TrendingUp, Activity } from 'lucide-react';
import { apiJson } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import { useOrg } from '../hooks/useOrg';
import { useToast } from '../components/ui/Toast';

export default function DashboardPage() {
  const { currentOrg } = useOrg();
  const toast = useToast();
  const [overview, setOverview] = useState(null);
  const [endpoints, setEndpoints] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentOrg) return;

    const load = async () => {
      try {
        const [ov, ep, del] = await Promise.all([
          apiJson('/analytics/overview'),
          apiJson('/analytics/endpoint-health'),
          apiJson('/deliveries?limit=8'),
        ]);
        setOverview(ov);
        setEndpoints(ep);
        setDeliveries(del.items || []);
      } catch (err) {
        toast.error('Failed to load dashboard data: ' + err.message);
      }
      setLoading(false);
    };

    load();

    const handleInterval = () => {
      if (document.visibilityState === 'visible') {
        load();
      }
    };
    const interval = setInterval(handleInterval, 15000);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        load();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [currentOrg]);

  if (loading) {
    return (
      <div className="metric-cards">
        {[1,2,3,4].map(i => <div key={i} className="metric-card skeleton-card"><div className="skeleton skeleton-lg" /><div className="skeleton skeleton-sm" /></div>)}
      </div>
    );
  }

  const ev = overview?.events?.total || 0;
  const wh = overview?.webhooks?.total || 0;
  const rate = overview?.deliveries?.success_rate || 0;
  const failed = overview?.deliveries?.failed || 0;

  return (
    <div className="page-animate">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p className="page-subtitle">Real-time overview of your webhook delivery pipeline</p>
      </div>

      {/* Metric cards */}
      <div className="metric-cards">
        <div className="metric-card">
          <div className="metric-card-top">
            <div className="metric-card-icon blue"><Calendar size={22} /></div>
            <div className="metric-card-trend up"><TrendingUp size={12} /> 24h</div>
          </div>
          <div className="metric-card-value">{ev.toLocaleString()}</div>
          <div className="metric-card-label">Total Events</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-top">
            <div className="metric-card-icon green"><Webhook size={22} /></div>
          </div>
          <div className="metric-card-value">{wh}</div>
          <div className="metric-card-label">Active Webhooks</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-top">
            <div className="metric-card-icon amber"><CheckCircle size={22} /></div>
          </div>
          <div className="metric-card-value">{rate}%</div>
          <div className="metric-card-label">Success Rate</div>
        </div>
        <div className="metric-card">
          <div className="metric-card-top">
            <div className="metric-card-icon rose"><XCircle size={22} /></div>
          </div>
          <div className="metric-card-value">{failed}</div>
          <div className="metric-card-label">Failed Deliveries</div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Recent deliveries */}
        <div className="card">
          <div className="card-header">
            <h4 className="card-title"><Activity size={18} /> Recent Deliveries</h4>
            <span className="live-indicator"><span className="live-dot" /> Live</span>
          </div>
          {deliveries.length === 0 ? (
            <p className="text-muted">No deliveries yet</p>
          ) : (
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Status</th>
                    <th>Attempts</th>
                    <th>Last Code</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map(d => (
                    <tr key={d.id}>
                      <td className="font-mono text-sm">{d.id?.slice(0, 8)}…</td>
                      <td><StatusBadge status={d.status} /></td>
                      <td>{d.attempt_count}</td>
                      <td>{d.last_status_code || '—'}</td>
                      <td className="text-muted text-sm">{new Date(d.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Endpoint health */}
        <div className="card">
          <div className="card-header">
            <h4 className="card-title"><Webhook size={18} /> Endpoint Health</h4>
          </div>
          {endpoints.length === 0 ? (
            <p className="text-muted">No endpoints configured</p>
          ) : (
            <div className="endpoint-health-list">
              {endpoints.map(ep => (
                <div key={ep.endpoint_id} className="endpoint-health-item">
                  <div className="endpoint-health-info">
                    <span className="endpoint-health-name">{ep.name}</span>
                    <span className="endpoint-health-url">{ep.url}</span>
                  </div>
                  <div className="endpoint-health-bar-container">
                    <div className="endpoint-health-bar">
                      <div
                        className="endpoint-health-fill"
                        style={{ width: `${ep.success_rate}%`, background: ep.success_rate > 90 ? 'var(--color-success)' : ep.success_rate > 50 ? 'var(--color-warning)' : 'var(--color-error)' }}
                      />
                    </div>
                    <span className="endpoint-health-pct">{ep.success_rate}%</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
