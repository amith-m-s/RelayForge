import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Zap, Mail, Lock, User, Building2, ArrowRight, Loader2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ email: '', full_name: '', password: '', organization_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const update = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(form.email, form.full_name, form.password, form.organization_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-bg-orbs">
        <div className="auth-orb auth-orb-1" />
        <div className="auth-orb auth-orb-2" />
        <div className="auth-orb auth-orb-3" />
      </div>
      <div className="auth-card">
        <div className="auth-logo">
          <div className="sidebar-logo-icon"><Zap size={24} /></div>
          <span className="auth-logo-text">RelayForge</span>
        </div>
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Start delivering webhooks in minutes</p>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="reg-name" className="form-label">Full Name</label>
            <div className="input-icon-wrapper">
              <User size={18} className="input-icon" />
              <input id="reg-name" type="text" className="form-input" placeholder="Jane Smith" value={form.full_name} onChange={update('full_name')} required />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="reg-email" className="form-label">Email</label>
            <div className="input-icon-wrapper">
              <Mail size={18} className="input-icon" />
              <input id="reg-email" type="email" className="form-input" placeholder="you@company.com" value={form.email} onChange={update('email')} required />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="reg-password" className="form-label">Password</label>
            <div className="input-icon-wrapper">
              <Lock size={18} className="input-icon" />
              <input id="reg-password" type="password" className="form-input" placeholder="Min 12 characters" value={form.password} onChange={update('password')} minLength={12} required />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="reg-org" className="form-label">Organization Name</label>
            <div className="input-icon-wrapper">
              <Building2 size={18} className="input-icon" />
              <input id="reg-org" type="text" className="form-input" placeholder="Acme Inc" value={form.organization_name} onChange={update('organization_name')} required />
            </div>
          </div>
          <button id="reg-submit" type="submit" className="btn btn-primary btn-lg btn-full" disabled={loading}>
            {loading ? <Loader2 size={18} className="spinner" /> : <><span>Create Account</span><ArrowRight size={18} /></>}
          </button>
        </form>
        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
