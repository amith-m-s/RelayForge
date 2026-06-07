import { useState, useEffect } from 'react';
import { Plus, Webhook, ExternalLink, Trash2, Loader2, Search } from 'lucide-react';
import { apiJson } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import EmptyState from '../components/EmptyState';
import Modal from '../components/ui/Modal';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { useToast } from '../components/ui/Toast';

export default function WebhooksPage() {
  const [endpoints, setEndpoints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [search, setSearch] = useState('');
  const [form, setForm] = useState({ name: '', url: '', secret: '', event_filter: '*' });
  const [confirmDelete, setConfirmDelete] = useState({ isOpen: false, id: null });
  const { addToast } = useToast();

  const load = async () => {
    try {
      const data = await apiJson('/webhooks/endpoints?limit=100');
      setEndpoints(data.items || []);
    } catch (err) {
      addToast('Failed to load webhook endpoints', 'error');
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await apiJson('/webhooks/endpoints', { method: 'POST', body: form });
      addToast('Webhook endpoint created', 'success');
      setShowCreate(false);
      setForm({ name: '', url: '', secret: '', event_filter: '*' });
      load();
    } catch (err) {
      addToast(err.message, 'error');
    }
    setCreating(false);
  };

  const handleDeleteClick = (id) => {
    setConfirmDelete({ isOpen: true, id });
  };

  const executeDelete = async () => {
    const id = confirmDelete.id;
    setConfirmDelete({ isOpen: false, id: null });
    try {
      await apiJson(`/webhooks/endpoints/${id}`, { method: 'DELETE' });
      addToast('Endpoint deleted', 'success');
      load();
    } catch (err) {
      addToast(err.message, 'error');
    }
  };

  const update = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  const filtered = endpoints.filter(ep => 
    ep.name?.toLowerCase().includes(search.toLowerCase()) || 
    ep.url?.toLowerCase().includes(search.toLowerCase()) ||
    ep.event_filter?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="page-loader"><div className="loader-spinner" /></div>;

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Webhook Endpoints</h2>
          <p className="page-subtitle">Manage your delivery destinations</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>
          <Plus size={18} /> Create Endpoint
        </button>
      </div>

      <div className="filter-bar" style={{ marginBottom: '1.5rem' }}>
        <div className="input-icon-wrapper search-input" style={{ width: '100%', maxWidth: '400px' }}>
          <Search size={18} className="input-icon" />
          <input 
            className="form-input" 
            placeholder="Search endpoints by name or URL..." 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
          />
        </div>
      </div>

      {endpoints.length === 0 ? (
        <EmptyState
          icon={Webhook}
          title="No endpoints yet"
          description="Create your first webhook endpoint to start receiving events."
          action={<button className="btn btn-primary" onClick={() => setShowCreate(true)}><Plus size={18} /> Create Endpoint</button>}
        />
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
          <Search size={32} style={{ opacity: 0.3, marginBottom: '0.5rem' }} />
          <h4>No matching endpoints found</h4>
          <p>Try refining your search terms.</p>
        </div>
      ) : (
        <div className="webhook-grid">
          {filtered.map((ep, i) => (
            <div key={ep.id} className="card webhook-card" style={{ animationDelay: `${i * 60}ms` }}>
              <div className="webhook-card-header">
                <div className="webhook-card-name">{ep.name}</div>
                <StatusBadge status={ep.status} />
              </div>
              <div className="webhook-card-url">
                <ExternalLink size={14} style={{ flexShrink: 0 }} />
                <span style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>{ep.url}</span>
              </div>
              <div className="webhook-card-meta">
                <span className="text-muted text-sm">Filter: <code>{ep.event_filter}</code></span>
                <span className="text-muted text-sm">{new Date(ep.created_at).toLocaleDateString()}</span>
              </div>
              <div className="webhook-card-actions">
                <button 
                  className="btn btn-ghost btn-sm" 
                  title="Delete" 
                  onClick={() => handleDeleteClick(ep.id)}
                  style={{ color: 'var(--color-error)' }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Webhook Endpoint">
        <form onSubmit={handleCreate} className="modal-form">
          <div className="form-group">
            <label className="form-label">Name</label>
            <input className="form-input" placeholder="My Webhook" value={form.name} onChange={update('name')} required />
          </div>
          <div className="form-group">
            <label className="form-label">URL</label>
            <input className="form-input" type="url" placeholder="https://api.example.com/webhooks" value={form.url} onChange={update('url')} required />
          </div>
          <div className="form-group">
            <label className="form-label">Secret (min 12 chars)</label>
            <input className="form-input" placeholder="whsec_..." value={form.secret} onChange={update('secret')} minLength={12} required />
          </div>
          <div className="form-group">
            <label className="form-label">Event Filter</label>
            <input className="form-input" placeholder="* or order.created,payment.completed" value={form.event_filter} onChange={update('event_filter')} />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? <Loader2 size={18} className="spinner" /> : 'Create Endpoint'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Custom Delete Confirmation */}
      <ConfirmDialog
        isOpen={confirmDelete.isOpen}
        title="Delete Webhook Endpoint"
        message="Are you sure you want to delete this endpoint? Delivery attempts to this URL will be stopped immediately."
        confirmText="Delete"
        type="danger"
        onConfirm={executeDelete}
        onCancel={() => setConfirmDelete({ isOpen: false, id: null })}
      />
    </div>
  );
}
