import { useEffect, useRef } from 'react';
import { AlertTriangle, X, Check, HelpCircle } from 'lucide-react';

export default function ConfirmDialog({
  isOpen,
  title = 'Are you sure?',
  message = 'This action cannot be undone.',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning', // 'info' | 'success' | 'warning' | 'danger'
  onConfirm,
  onCancel,
}) {
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    // Body scroll lock
    const originalStyle = window.getComputedStyle(document.body).overflow;
    document.body.style.overflow = 'hidden';

    // Focus trap & escape handler
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = originalStyle;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const typeConfig = {
    info: {
      icon: HelpCircle,
      colorClass: 'text-primary',
      btnClass: 'btn-primary',
    },
    success: {
      icon: Check,
      colorClass: 'text-success',
      btnClass: 'btn-success',
    },
    warning: {
      icon: AlertTriangle,
      colorClass: 'text-warning',
      btnClass: 'btn-warning',
    },
    danger: {
      icon: AlertTriangle,
      colorClass: 'text-error',
      btnClass: 'btn-error',
    },
  };

  const config = typeConfig[type] || typeConfig.warning;
  const Icon = config.icon;

  return (
    <div className="modal-overlay modal-open" onClick={onCancel}>
      <div 
        ref={dialogRef}
        className="modal-content card" 
        style={{ maxWidth: '420px', padding: '1.5rem', animation: 'scaleUp 0.2s ease-out' }}
        onClick={(e) => e.stopPropagation()}
      >
        <button 
          className="modal-close-btn" 
          onClick={onCancel}
          aria-label="Close dialog"
          style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }}
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', alignItems: 'flex-start' }}>
          <div className={`${config.colorClass}`} style={{ flexShrink: 0, padding: '0.5rem', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.03)' }}>
            <Icon size={24} />
          </div>
          
          <div style={{ flexGrow: 1 }}>
            <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, color: 'var(--color-text)' }}>{title}</h4>
            <p style={{ margin: '0.5rem 0 0', fontSize: '0.875rem', color: 'var(--color-text-muted)', lineHeight: '1.5' }}>{message}</p>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem' }}>
          <button className="btn btn-ghost" onClick={onCancel}>
            {cancelText}
          </button>
          <button className={`btn ${config.btnClass}`} onClick={onConfirm} autoFocus>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
