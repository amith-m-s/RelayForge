import { useState, useEffect } from 'react';
import { Skull, RefreshCw, Trash2 } from 'lucide-react';
import { apiJson } from '../api/client';
import EmptyState from '../components/EmptyState';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { useToast } from '../components/ui/Toast';
import { useOrg } from '../hooks/useOrg';

export default function DeadLetterPage() {
  const { currentOrg } = useOrg();
  const toast = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmPurgeAll, setConfirmPurgeAll] = useState(false);
  const [confirmPurgeSingle, setConfirmPurgeSingle] = useState({ isOpen: false, id: null });

  const load = async () => {
    try {
      const data = await apiJson('/dead-letter?limit=100');
      setItems(data.items || []);
    } catch (err) {
      toast.error('Failed to load dead letter queue events: ' + err.message);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (currentOrg) {
      load();
    }
  }, [currentOrg]);

  const replay = async (id) => {
    try {
      await apiJson(`/dead-letter/${id}/replay`, { method: 'POST' });
      toast.success('Replayed successfully');
      load();
    } catch (err) { toast.error(err.message); }
  };

  const purge = (id) => {
    setConfirmPurgeSingle({ isOpen: true, id });
  };

  const executeSinglePurge = async () => {
    const id = confirmPurgeSingle.id;
    setConfirmPurgeSingle({ isOpen: false, id: null });
    try {
      await apiJson(`/dead-letter/${id}`, { method: 'DELETE' });
      toast.success('Dead letter event purged');
      load();
    } catch (err) { toast.error(err.message); }
  };

  const executePurgeAll = async () => {
    setConfirmPurgeAll(false);
    try {
      await apiJson('/dead-letter/purge', { method: 'POST' });
      toast.success('All dead letter events purged');
      load();
    } catch (err) { toast.error(err.message); }
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
          <button className="btn btn-danger" onClick={() => setConfirmPurgeAll(true)}>
            <Trash2 size={18} /> Purge All
          </button>
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
                        <button className="btn btn-ghost btn-sm" onClick={() => purge(item.id)} title="Purge" style={{ color: 'var(--color-error)' }}><Trash2 size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Purge All Confirmation */}
      <ConfirmDialog
        isOpen={confirmPurgeAll}
        title="Purge All Dead Letter Events"
        message="Are you sure you want to purge all events in the dead letter queue? This action cannot be undone."
        confirmText="Purge All"
        type="danger"
        onConfirm={executePurgeAll}
        onCancel={() => setConfirmPurgeAll(false)}
      />

      {/* Purge Single Confirmation */}
      <ConfirmDialog
        isOpen={confirmPurgeSingle.isOpen}
        title="Purge Dead Letter Event"
        message="Are you sure you want to purge this event from the queue?"
        confirmText="Purge"
        type="danger"
        onConfirm={executeSinglePurge}
        onCancel={() => setConfirmPurgeSingle({ isOpen: false, id: null })}
      />
    </div>
  );
}
