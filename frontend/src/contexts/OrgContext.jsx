import { createContext, useState, useEffect, useCallback } from 'react';
import { apiJson, setOrgId, getOrgId } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export const OrgContext = createContext(null);

export function OrgProvider({ children }) {
  const { user } = useAuth();
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchOrgs = useCallback(async () => {
    if (!user) return;
    try {
      const data = await apiJson('/organizations');
      setOrganizations(data);
      const savedId = getOrgId();
      const match = data.find(o => o.id === savedId);
      const org = match || data[0] || null;
      setCurrentOrg(org);
      if (org) setOrgId(org.id);
    } catch {
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => { fetchOrgs(); }, [fetchOrgs]);

  const switchOrg = (org) => {
    setCurrentOrg(org);
    setOrgId(org.id);
  };

  return (
    <OrgContext.Provider value={{ organizations, currentOrg, switchOrg, loading, refetch: fetchOrgs }}>
      {children}
    </OrgContext.Provider>
  );
}
