export default function StatusBadge({ status }) {
  const map = {
    pending: 'badge-info',
    delivering: 'badge-warning',
    succeeded: 'badge-success',
    failed: 'badge-error',
    dead_letter: 'badge-muted',
    active: 'badge-success',
    disabled: 'badge-muted',
    paused: 'badge-warning',
    critical: 'badge-error',
    low: 'badge-warning',
    good: 'badge-success',
  };
  const label = (status || 'unknown').replace(/_/g, ' ');
  return (
    <span className={`badge ${map[status] || 'badge-muted'}`}>
      <span className="badge-dot" />
      {label}
    </span>
  );
}
