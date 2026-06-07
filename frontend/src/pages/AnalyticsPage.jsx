import { useState, useEffect, useMemo, useCallback } from 'react';
import { BarChart3 } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { apiJson } from '../api/client';
import { useOrg } from '../hooks/useOrg';
import { useToast } from '../components/ui/Toast';

const chartTheme = {
  bg: 'rgba(30, 41, 59, 0.6)',
  grid: 'rgba(71, 85, 105, 0.3)',
  text: '#94a3b8',
  blue: '#3b82f6',
  green: '#10b981',
  red: '#f43f5e',
  amber: '#f59e0b',
};

export default function AnalyticsPage() {
  const { currentOrg } = useOrg();
  const toast = useToast();
  const [metrics, setMetrics] = useState([]);
  const [volume, setVolume] = useState([]);
  const [endpointHealth, setEndpointHealth] = useState([]);
  const [timeWindow, setTimeWindow] = useState(24);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentOrg) return;
    const load = async () => {
      try {
        const [m, v, eh] = await Promise.all([
          apiJson(`/analytics/delivery-metrics?window=${timeWindow}`),
          apiJson(`/analytics/event-volume?window=${timeWindow}`),
          apiJson('/analytics/endpoint-health'),
        ]);
        setMetrics(m);
        setVolume(v);
        setEndpointHealth(eh);
      } catch (err) {
        toast.error('Failed to load analytics: ' + err.message);
      }
      setLoading(false);
    };
    load();
  }, [currentOrg, timeWindow]);

  const fmtTime = useCallback((ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    return timeWindow <= 24 ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }, [timeWindow]);

  const CustomTooltip = useCallback(({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <div className="chart-tooltip-label">{fmtTime(label)}</div>
        {payload.map((p, i) => (
          <div key={i} className="chart-tooltip-row">
            <span className="chart-tooltip-dot" style={{ background: p.color }} />
            <span>{p.name}: {p.value}</span>
          </div>
        ))}
      </div>
    );
  }, [fmtTime]);

  const performanceChart = useMemo(() => (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={metrics}>
        <defs>
          <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartTheme.green} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartTheme.green} stopOpacity={0} />
          </linearGradient>
          <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={chartTheme.red} stopOpacity={0.3} />
            <stop offset="95%" stopColor={chartTheme.red} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" tickFormatter={fmtTime} stroke={chartTheme.text} fontSize={12} />
        <YAxis stroke={chartTheme.text} fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="succeeded" stroke={chartTheme.green} fill="url(#greenGrad)" name="Succeeded" strokeWidth={2} />
        <Area type="monotone" dataKey="failed" stroke={chartTheme.red} fill="url(#redGrad)" name="Failed" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  ), [metrics, fmtTime, CustomTooltip]);

  const volumeChart = useMemo(() => (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={volume}>
        <CartesianGrid stroke={chartTheme.grid} strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" tickFormatter={fmtTime} stroke={chartTheme.text} fontSize={12} />
        <YAxis stroke={chartTheme.text} fontSize={12} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="count" fill={chartTheme.blue} name="Events" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  ), [volume, fmtTime, CustomTooltip]);

  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Analytics</h2>
          <p className="page-subtitle">Delivery performance and event metrics</p>
        </div>
        <div className="filter-group">
          <select className="form-select" value={timeWindow} onChange={e => setTimeWindow(Number(e.target.value))}>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last 7 Days</option>
            <option value={720}>Last 30 Days</option>
          </select>
        </div>
      </div>

      {/* Delivery metrics chart */}
      <div className="card chart-card">
        <div className="card-header">
          <h4 className="card-title">Delivery Performance</h4>
        </div>
        <div className="chart-container">
          {performanceChart}
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Event volume */}
        <div className="card chart-card">
          <div className="card-header">
            <h4 className="card-title">Event Volume</h4>
          </div>
          <div className="chart-container">
            {volumeChart}
          </div>
        </div>

        {/* Endpoint health */}
        <div className="card">
          <div className="card-header">
            <h4 className="card-title">Endpoint Health</h4>
          </div>
          <div className="endpoint-health-list">
            {endpointHealth.length === 0 ? (
              <p className="text-muted">No endpoints</p>
            ) : endpointHealth.map(ep => (
              <div key={ep.endpoint_id} className="endpoint-health-item">
                <div className="endpoint-health-info">
                  <span className="endpoint-health-name">{ep.name}</span>
                  <span className="text-muted text-sm">{ep.total_deliveries} deliveries</span>
                </div>
                <div className="endpoint-health-bar-container">
                  <div className="endpoint-health-bar">
                    <div className="endpoint-health-fill" style={{ width: `${ep.success_rate}%`, background: ep.success_rate > 90 ? chartTheme.green : ep.success_rate > 50 ? chartTheme.amber : chartTheme.red }} />
                  </div>
                  <span className="endpoint-health-pct">{ep.success_rate}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
