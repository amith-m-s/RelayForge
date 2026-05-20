import { useState, useEffect } from 'react';
import { Skull, RefreshCw, Trash2 } from 'lucide-react';
import { apiJson } from '../api/client';
import EmptyState from '../components/EmptyState';
import { useToast } from '../components/ui/Toast';

export default function DeadLetterPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  const load = async () => {
    try {
      const data = await apiJson('/dead-letter?limit=100');
      setItems(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const replay = async (id) => {
    try {
      await apiJson(`/dead-letter/${id}/replay`, { method: 'POST' });
      addToast('Replayed successfully', 'success');
      load();
    } catch (err) { addToast(err.message, 'error'); }
  };

  const purge = async (id) => {
    try {
      await apiJson(`/dead-letter/${id}`, { method: 'DELETE' });
      addToast('Purged', 'success');
      load();
    } catch (err) { addToast(err.message, 'error'); }
  };

  const purgeAll = async () => {
    if (!confirm('Purge ALL dead letter events?')) return;
    try {
      await apiJson('/dead-letter/purge', { method: 'POST' });
      addToast('All events purged', 'success');
      load();
    } catch (err) { addToast(err.message, 'error'); }
  };

  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Dead Letter Queue</h2>
          <p className="page-subtitle">Failed deliveries that exhausted all retry attempts</p>
        </div>
        {items.length > 0 && (
          <button className="btn btn-danger" onClick={purgeAll}><Trash2 size={18} /> Purge All</button>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState icon={Skull} title="Queue is empty" description="No dead letter events. Your webhooks are delivering successfully!" />
      ) : (
        <div className="card">
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Delivery ID</th>
                  <th>Reason</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.id}>
                    <td className="font-mono text-sm">{item.id?.slice(0, 8)}…</td>
                    <td className="font-mono text-sm">{item.delivery_id?.slice(0, 8)}…</td>
                    <td><span className="badge badge-error">{item.reason}</span></td>
                    <td className="text-muted text-sm">{new Date(item.created_at).toLocaleString()}</td>
                    <td>
                      <div className="btn-group">
                        <button className="btn btn-ghost btn-sm" onClick={() => replay(item.id)} title="Replay"><RefreshCw size={14} /></button>
                        <button className="btn btn-ghost btn-sm" onClick={() => purge(item.id)} title="Purge"><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
