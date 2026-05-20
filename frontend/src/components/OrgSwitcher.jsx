import { ChevronDown } from 'lucide-react';
import { useOrg } from '../hooks/useOrg';

export default function OrgSwitcher() {
  const { organizations, currentOrg, switchOrg } = useOrg();
  if (!organizations.length) return null;

  return (
    <div className="org-switcher">
      <select
        className="org-switcher-select"
        value={currentOrg?.id || ''}
        onChange={e => {
          const org = organizations.find(o => o.id === e.target.value);
          if (org) switchOrg(org);
        }}
      >
        {organizations.map(org => (
          <option key={org.id} value={org.id}>{org.name}</option>
        ))}
      </select>
      <ChevronDown size={16} className="org-switcher-icon" />
    </div>
  );
}
