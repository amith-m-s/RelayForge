import { useState, useEffect } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Webhook, Calendar, Truck, SkullIcon, BarChart3,
  Settings, ChevronsLeft, ChevronsRight, Zap, LogOut, Bell, Terminal, Menu,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import OrgSwitcher from '../components/OrgSwitcher';

const navItems = [
  { section: 'Overview', items: [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  ]},
  { section: 'Webhooks', items: [
    { to: '/webhooks', icon: Webhook, label: 'Endpoints' },
    { to: '/playground', icon: Terminal, label: 'Sandbox' },
    { to: '/events', icon: Calendar, label: 'Events' },
    { to: '/deliveries', icon: Truck, label: 'Deliveries' },
    { to: '/dead-letter', icon: SkullIcon, label: 'Dead Letter' },
  ]},
  { section: 'System', items: [
    { to: '/settings', icon: Settings, label: 'Settings' },
  ]},
];

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const location = useLocation();

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const getPageTitle = () => {
    const flat = navItems.flatMap(s => s.items);
    const match = flat.find(i => i.end ? location.pathname === i.to : location.pathname.startsWith(i.to) && i.to !== '/');
    return match?.label || 'Dashboard';
  };

  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '??';

  return (
    <div className={`dashboard-layout ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Mobile Overlay */}
      <div 
        className={`mobile-overlay ${mobileOpen ? 'visible' : ''}`} 
        onClick={() => setMobileOpen(false)} 
      />

      {/* Sidebar */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-header">
          <a href="/" className="sidebar-logo">
            <div className="sidebar-logo-icon"><Zap size={20} /></div>
            <span className="sidebar-logo-text">RelayForge</span>
          </a>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(section => (
            <div key={section.section} className="sidebar-section">
              <div className="sidebar-section-title">{section.section}</div>
              {section.items.map(item => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                >
                  <item.icon size={20} className="sidebar-link-icon" />
                  <span className="sidebar-link-text">{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="sidebar-toggle" onClick={() => setCollapsed(c => !c)}>
            {collapsed ? <ChevronsRight size={20} /> : <ChevronsLeft size={20} />}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="dashboard-main">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button 
              className="mobile-menu-btn" 
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
              style={{ background: 'none', border: 'none', cursor: 'pointer', outline: 'none' }}
            >
              <Menu size={20} />
            </button>
            <div className="topbar-breadcrumb">
              <span>RelayForge</span>
              <span className="topbar-breadcrumb-separator">/</span>
              <span className="topbar-breadcrumb-current">{getPageTitle()}</span>
            </div>
          </div>
          <div className="topbar-right">
            <OrgSwitcher />
            <button className="btn btn-ghost" onClick={logout} title="Logout">
              <LogOut size={18} />
            </button>
            <div className="topbar-user">
              <div className="topbar-avatar">{initials}</div>
              <div className="topbar-user-info">
                <span className="topbar-user-name">{user?.full_name || 'User'}</span>
                <span className="topbar-user-email">{user?.email || ''}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="dashboard-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
