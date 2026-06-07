import { useState, useEffect, Fragment } from 'react';
import { Calendar, Search, ChevronDown, ChevronRight } from 'lucide-react';
import { apiJson } from '../api/client';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/ui/Toast';
import { useOrg } from '../hooks/useOrg';

export default function EventsPage() {
  const { currentOrg } = useOrg();
  const toast = useToast();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    if (!currentOrg) return;
    const load = async () => {
      try {
        const data = await apiJson('/events?limit=50');
        setEvents(data.items || []);
      } catch (err) {
        toast.error('Failed to load events: ' + err.message);
      }
      setLoading(false);
    };
    load();
  }, [currentOrg]);

  const filtered = events.filter(ev =>
    ev.source?.toLowerCase().includes(search.toLowerCase()) ||
    ev.event_key?.toLowerCase().includes(search.toLowerCase()) ||
    ev.id?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Events</h2>
          <p className="page-subtitle">Incoming event log</p>
        </div>
      </div>

      <div className="filter-bar">
        <div className="input-icon-wrapper search-input">
          <Search size={18} className="input-icon" />
          <input className="form-input" placeholder="Search events..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Calendar} title="No events" description="Events will appear here when your application sends them." />
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th></th>
                  <th>Event ID</th>
                  <th>Source</th>
                  <th>Event Key</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(ev => (
                  <Fragment key={ev.id}>
                    <tr className="table-row-clickable" onClick={() => setExpanded(expanded === ev.id ? null : ev.id)}>
                      <td style={{width:30}}>{expanded === ev.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</td>
                      <td className="font-mono text-sm">{ev.id?.slice(0, 12)}…</td>
                      <td>{ev.source}</td>
                      <td><code>{ev.event_key || '—'}</code></td>
                      <td className="text-muted text-sm">{new Date(ev.created_at).toLocaleString()}</td>
                    </tr>
                    {expanded === ev.id && (
                      <tr className="detail-row">
                        <td colSpan={5}>
                          <div className="json-viewer">
                            <div className="json-header">Event Details</div>
                            <pre className="json-content">{JSON.stringify(ev, null, 2)}</pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
