import { useState, useEffect } from 'react';
import { Key, Shield, Copy, Plus, Trash2, Loader2, Check } from 'lucide-react';
import { apiJson } from '../api/client';
import { useOrg } from '../hooks/useOrg';
import Modal from '../components/ui/Modal';
import { useToast } from '../components/ui/Toast';
import EmptyState from '../components/EmptyState';

export default function SettingsPage() {
  const [tab, setTab] = useState('api-keys');

  return (
    <div className="page-animate">
      <div className="page-header">
        <div>
          <h2>Settings</h2>
          <p className="page-subtitle">Manage API keys, retry policies, and organization</p>
        </div>
      </div>

      <div className="settings-tabs">
        {[
          { id: 'api-keys', label: 'API Keys', icon: Key },
          { id: 'retry-policies', label: 'Retry Policies', icon: Shield },
        ].map(t => (
          <button
            key={t.id}
            className={`settings-tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      <div className="settings-content">
        {tab === 'api-keys' && <ApiKeysTab />}
        {tab === 'retry-policies' && <RetryPoliciesTab />}
      </div>
    </div>
  );
}

function ApiKeysTab() {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [copied, setCopied] = useState(false);
  const { addToast } = useToast();

  const load = async () => {
    try {
      const data = await apiJson('/api-keys?limit=100');
      setKeys(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const data = await apiJson('/api-keys', { method: 'POST', body: { name } });
      setNewKey(data.full_key);
      addToast('API key created', 'success');
      setName('');
      load();
    } catch (err) { addToast(err.message, 'error'); }
    setCreating(false);
  };

  const revoke = async (id) => {
    if (!confirm('Revoke this API key?')) return;
    try {
      await apiJson(`/api-keys/${id}`, { method: 'DELETE' });
      addToast('Key revoked', 'success');
      load();
    } catch (err) { addToast(err.message, 'error'); }
  };

  const copyKey = () => {
    navigator.clipboard.writeText(newKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <div className="loader-spinner" style={{margin:'2rem auto'}} />;

  return (
    <div>
      <div className="settings-section-header">
        <h4>API Keys</h4>
        <button className="btn btn-primary btn-sm" onClick={() => { setShowCreate(true); setNewKey(null); }}>
          <Plus size={16} /> Create Key
        </button>
      </div>

      {newKey && (
        <div className="alert alert-warning">
          <p><strong>Copy your key now — it won't be shown again:</strong></p>
          <div className="key-display">
            <code className="key-value">{newKey}</code>
            <button className="btn btn-ghost btn-sm" onClick={copyKey}>
              {copied ? <Check size={14} /> : <Copy size={14} />}
            </button>
          </div>
        </div>
      )}

      {keys.length === 0 ? (
        <EmptyState icon={Key} title="No API keys" description="Create an API key to authenticate programmatic access." />
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Prefix</th>
                <th>Status</th>
                <th>Last Used</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {keys.map(k => (
                <tr key={k.id}>
                  <td className="font-medium">{k.name}</td>
                  <td><code>{k.key_prefix}…</code></td>
                  <td><span className={`badge ${k.is_active ? 'badge-success' : 'badge-muted'}`}>{k.is_active ? 'Active' : 'Revoked'}</span></td>
                  <td className="text-muted text-sm">{k.last_used_at ? new Date(k.last_used_at).toLocaleString() : 'Never'}</td>
                  <td className="text-muted text-sm">{new Date(k.created_at).toLocaleDateString()}</td>
                  <td>
                    {k.is_active && (
                      <button className="btn btn-ghost btn-sm" onClick={() => revoke(k.id)}><Trash2 size={14} /></button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create API Key">
        <form onSubmit={create} className="modal-form">
          <div className="form-group">
            <label className="form-label">Key Name</label>
            <input className="form-input" placeholder="Production API Key" value={name} onChange={e => setName(e.target.value)} required />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? <Loader2 size={16} className="spinner" /> : 'Create Key'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

function RetryPoliciesTab() {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: '', max_attempts: 8, base_delay_seconds: 30, max_delay_seconds: 3600 });
  const { addToast } = useToast();

  const load = async () => {
    try {
      const data = await apiJson('/retry-policies?limit=100');
      setPolicies(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await apiJson('/retry-policies', { method: 'POST', body: form });
      addToast('Retry policy created', 'success');
      setShowCreate(false);
      setForm({ name: '', max_attempts: 8, base_delay_seconds: 30, max_delay_seconds: 3600 });
      load();
    } catch (err) { addToast(err.message, 'error'); }
    setCreating(false);
  };

  const remove = async (id) => {
    if (!confirm('Delete this retry policy?')) return;
    try {
      await apiJson(`/retry-policies/${id}`, { method: 'DELETE' });
      addToast('Policy deleted', 'success');
      load();
    } catch (err) { addToast(err.message, 'error'); }
  };

  const update = (field) => (e) => setForm(f => ({ ...f, [field]: field === 'name' ? e.target.value : Number(e.target.value) }));

  if (loading) return <div className="loader-spinner" style={{margin:'2rem auto'}} />;

  return (
    <div>
      <div className="settings-section-header">
        <h4>Retry Policies</h4>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)}>
          <Plus size={16} /> Create Policy
        </button>
      </div>

      {policies.length === 0 ? (
        <EmptyState icon={Shield} title="No retry policies" description="Create a retry policy to customize delivery retry behavior." />
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Max Attempts</th>
                <th>Base Delay</th>
                <th>Max Delay</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {policies.map(p => (
                <tr key={p.id}>
                  <td className="font-medium">{p.name}</td>
                  <td>{p.max_attempts}</td>
                  <td>{p.base_delay_seconds}s</td>
                  <td>{p.max_delay_seconds}s</td>
                  <td className="text-muted text-sm">{new Date(p.created_at).toLocaleDateString()}</td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => remove(p.id)}><Trash2 size={14} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="Create Retry Policy">
        <form onSubmit={create} className="modal-form">
          <div className="form-group">
            <label className="form-label">Policy Name</label>
            <input className="form-input" placeholder="Default Retry" value={form.name} onChange={update('name')} required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Attempts</label>
              <input className="form-input" type="number" min={1} max={50} value={form.max_attempts} onChange={update('max_attempts')} />
            </div>
            <div className="form-group">
              <label className="form-label">Base Delay (s)</label>
              <input className="form-input" type="number" min={1} max={3600} value={form.base_delay_seconds} onChange={update('base_delay_seconds')} />
            </div>
            <div className="form-group">
              <label className="form-label">Max Delay (s)</label>
              <input className="form-input" type="number" min={1} max={86400} value={form.max_delay_seconds} onChange={update('max_delay_seconds')} />
            </div>
          </div>
          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? <Loader2 size={16} className="spinner" /> : 'Create Policy'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
