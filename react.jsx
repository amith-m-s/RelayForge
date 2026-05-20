import React, { useState, useEffect } from 'react';
import { AlertTriangle, Package, Bell, Settings, Search, Mail, Clock, Users, Database } from 'lucide-react';

const WarehouseInventorySystem = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [inventoryData, setInventoryData] = useState([
    { id: 'WH-001', name: 'Steel Bolts M8', current: 15, threshold: 50, critical: 20, status: 'critical', updated: '2 mins ago' },
    { id: 'WH-002', name: 'Safety Helmets', current: 25, threshold: 30, critical: 10, status: 'low', updated: '15 mins ago' },
    { id: 'WH-003', name: 'Rubber Gloves', current: 150, threshold: 100, critical: 30, status: 'good', updated: '1 hour ago' },
    { id: 'WH-004', name: 'Cable Ties', current: 8, threshold: 25, critical: 15, status: 'critical', updated: '5 mins ago' },
    { id: 'WH-005', name: 'Work Boots', current: 45, threshold: 40, critical: 20, status: 'good', updated: '30 mins ago' }
  ]);
  
  const [alertSettings, setAlertSettings] = useState({
    selectedItem: 'WH-001',
    lowThreshold: 50,
    criticalThreshold: 20,
    maxStock: 500,
    frequency: 'immediate',
    recipients: 'manager@warehouse.com'
  });

  const [emailConfig, setEmailConfig] = useState({
    smtpServer: 'smtp.gmail.com',
    smtpPort: 587,
    senderEmail: 'alerts@warehouse.com',
    appPassword: ''
  });

  // Simulate real-time Firebase updates
  useEffect(() => {
    const interval = setInterval(() => {
      setInventoryData(prev => prev.map(item => ({
        ...item,
        updated: Math.random() > 0.7 ? 'Just now' : item.updated
      })));
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch(status) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-300';
      case 'low': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'good': return 'bg-green-100 text-green-700 border-green-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const filteredInventory = inventoryData.filter(item => 
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const alertItems = inventoryData.filter(item => item.status === 'critical' || item.status === 'low');

  const stats = {
    totalItems: inventoryData.length,
    lowStock: inventoryData.filter(item => item.status === 'low').length,
    criticalAlerts: inventoryData.filter(item => item.status === 'critical').length,
    systemHealth: 98
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-lg">
          <div className="text-3xl font-bold">{stats.totalItems}</div>
          <div className="text-blue-100">Total Items</div>
        </div>
        <div className="bg-gradient-to-r from-orange-500 to-red-600 text-white p-6 rounded-lg">
          <div className="text-3xl font-bold">{stats.lowStock}</div>
          <div className="text-orange-100">Low Stock</div>
        </div>
        <div className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white p-6 rounded-lg">
          <div className="text-3xl font-bold">{stats.criticalAlerts}</div>
          <div className="text-cyan-100">Critical Alerts</div>
        </div>
        <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-6 rounded-lg">
          <div className="text-3xl font-bold">{stats.systemHealth}%</div>
          <div className="text-green-100">System Health</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Inventory Table */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Package className="h-5 w-5" />
              Inventory Status
            </h2>
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search items..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Item Code</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Product</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Stock</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Threshold</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredInventory.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm">{item.id}</td>
                    <td className="px-4 py-3 font-medium">{item.name}</td>
                    <td className="px-4 py-3">{item.current}</td>
                    <td className="px-4 py-3">{item.threshold}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(item.status)}`}>
                        {item.status === 'critical' ? '🔴 Critical' : 
                         item.status === 'low' ? '🟡 Low Stock' : '🟢 Good'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{item.updated}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Active Alerts Panel */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h3 className="text-lg font-bold text-red-800">Active Alerts</h3>
          </div>
          
          <div className="space-y-3">
            {alertItems.map((item) => (
              <div key={item.id} className="bg-white border-l-4 border-red-500 p-3 rounded">
                <div className="font-semibold text-gray-800">{item.name}</div>
                <div className="text-sm text-gray-600">Stock: {item.current} (Threshold: {item.threshold})</div>
                <div className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                  <Mail className="h-3 w-3" />
                  Email sent {item.updated}
                </div>
              </div>
            ))}
          </div>
          
          <button className="w-full mt-4 bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition-colors">
            View All Alerts
          </button>
        </div>
      </div>
    </div>
  );

  const renderAlertSetup = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          Configure Alert Thresholds
        </h2>
        <p className="text-gray-600 mb-6">Set minimum stock levels to trigger automatic Firebase Cloud Function alerts</p>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Item</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.selectedItem}
                onChange={(e) => setAlertSettings(prev => ({...prev, selectedItem: e.target.value}))}
              >
                {inventoryData.map(item => (
                  <option key={item.id} value={item.id}>
                    {item.name} (Current: {item.current})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Low Stock Threshold</label>
              <input
                type="number"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.lowThreshold}
                onChange={(e) => setAlertSettings(prev => ({...prev, lowThreshold: parseInt(e.target.value)}))}
              />
              <p className="text-sm text-gray-500 mt-1">Firebase function triggers when stock falls below this level</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Critical Stock Threshold</label>
              <input
                type="number"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.criticalThreshold}
                onChange={(e) => setAlertSettings(prev => ({...prev, criticalThreshold: parseInt(e.target.value)}))}
              />
              <p className="text-sm text-gray-500 mt-1">Send urgent alert when stock is critically low</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Alert Frequency</label>
              <select 
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.frequency}
                onChange={(e) => setAlertSettings(prev => ({...prev, frequency: e.target.value}))}
              >
                <option value="immediate">Immediate</option>
                <option value="30min">Every 30 minutes</option>
                <option value="1hour">Every hour</option>
                <option value="daily">Daily summary</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Maximum Stock Level</label>
              <input
                type="number"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.maxStock}
                onChange={(e) => setAlertSettings(prev => ({...prev, maxStock: parseInt(e.target.value)}))}
                placeholder="e.g., 500"
              />
              <p className="text-sm text-gray-500 mt-1">Optional: Alert when overstocked</p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Alert Recipients</label>
              <input
                type="email"
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={alertSettings.recipients}
                onChange={(e) => setAlertSettings(prev => ({...prev, recipients: e.target.value}))}
                placeholder="manager@warehouse.com"
              />
              <p className="text-sm text-gray-500 mt-1">Additional emails (comma-separated)</p>
            </div>
          </div>
        </div>
        
        <div className="flex gap-4 mt-6">
          <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2">
            <Database className="h-4 w-4" />
            Save to Firebase
          </button>
          <button className="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors">
            🧪 Test Alert
          </button>
        </div>
      </div>

      {/* Current Thresholds Overview */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">📋 Current Thresholds Overview</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-white">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Item</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Low Stock</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Critical</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Max Stock</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {inventoryData.slice(0, 3).map((item) => (
                <tr key={item.id}>
                  <td className="px-4 py-3">{item.name}</td>
                  <td className="px-4 py-3">{item.threshold}</td>
                  <td className="px-4 py-3">{item.critical}</td>
                  <td className="px-4 py-3">500</td>
                  <td className="px-4 py-3">
                    {item.status === 'critical' ? '🔴 Critical' : 
                     item.status === 'low' ? '🟡 Low' : '🟢 Good'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Notification Settings
        </h2>
        <p className="text-gray-600 mb-6">Configure your Node.js + Firebase email integration</p>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Email Configuration */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">SMTP Server</label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={emailConfig.smtpServer}
                  onChange={(e) => setEmailConfig(prev => ({...prev, smtpServer: e.target.value}))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">SMTP Port</label>
                <input
                  type="number"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={emailConfig.smtpPort}
                  onChange={(e) => setEmailConfig(prev => ({...prev, smtpPort: parseInt(e.target.value)}))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sender Email</label>
                <input
                  type="email"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={emailConfig.senderEmail}
                  onChange={(e) => setEmailConfig(prev => ({...prev, senderEmail: e.target.value}))}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">App Password</label>
                <input
                  type="password"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={emailConfig.appPassword}
                  onChange={(e) => setEmailConfig(prev => ({...prev, appPassword: e.target.value}))}
                  placeholder="••••••••••••••••"
                />
              </div>
              <button className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition-colors">
                Test Email Setup
              </button>
            </div>
          </div>

          {/* Alert Types */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Alert Types
            </h3>
            <div className="space-y-3">
              {[
                { id: 'lowStock', label: 'Low stock warnings', checked: true },
                { id: 'critical', label: 'Critical stock alerts', checked: true },
                { id: 'overstock', label: 'Overstock notifications', checked: false },
                { id: 'daily', label: 'Daily inventory summary', checked: true },
                { id: 'weekly', label: 'Weekly reports', checked: false },
                { id: 'maintenance', label: 'System maintenance alerts', checked: true }
              ].map((alert) => (
                <div key={alert.id} className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id={alert.id}
                    defaultChecked={alert.checked}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor={alert.id} className="text-sm font-medium text-gray-700">
                    {alert.label}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Timing Settings */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Timing Settings
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Business Hours Start</label>
                <input
                  type="time"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  defaultValue="08:00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Business Hours End</label>
                <input
                  type="time"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  defaultValue="18:00"
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="businessHours"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="businessHours" className="text-sm font-medium text-gray-700">
                    Send alerts only during business hours
                  </label>
                </div>
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="weekends"
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="weekends" className="text-sm font-medium text-gray-700">
                    Weekend alerts
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* Recipients */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Users className="h-5 w-5" />
              Recipients
            </h3>
            <div className="space-y-4">
              <div className="p-3 bg-white rounded border">
                <div className="font-medium text-gray-800">Warehouse Manager</div>
                <div className="text-sm text-gray-600">john.manager@warehouse.com</div>
              </div>
              <div className="p-3 bg-white rounded border">
                <div className="font-medium text-gray-800">Procurement Team</div>
                <div className="text-sm text-gray-600">procurement@warehouse.com</div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Add New Recipient</label>
                <div className="flex gap-2">
                  <input
                    type="email"
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="email@warehouse.com"
                  />
                  <button className="bg-blue-600 text-white px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors">
                    Add
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Firebase Status */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-bold text-green-800 mb-2 flex items-center gap-2">
          <Database className="h-5 w-5" />
          Firebase Cloud Functions Status
        </h3>
        <p className="text-green-700 mb-4">Your alert system is powered by Firebase Cloud Functions monitoring Firestore in real-time.</p>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center gap-2 text-green-700">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Database triggers active
          </div>
          <div className="flex items-center gap-2 text-green-700">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Email service connected
          </div>
          <div className="flex items-center gap-2 text-green-700">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Threshold monitoring running
          </div>
          <div className="flex items-center gap-2 text-green-700">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            Last check: 2 minutes ago
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-800 text-white p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Package className="h-8 w-8" />
            <h1 className="text-2xl font-bold">WarehouseHub</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <span>{alertItems.length} Alerts</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                👤
              </div>
              <span>John Manager</span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto">
          <div className="flex space-x-1">
            {[
              { id: 'dashboard', label: '📊 Dashboard', icon: Package },
              { id: 'alerts', label: '⚠️ Alert Setup', icon: AlertTriangle },
              { id: 'settings', label: '⚙️ Settings', icon: Settings }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'alerts' && renderAlertSetup()}
        {activeTab === 'settings' && renderSettings()}
      </main>
    </div>
  );
};

export default WarehouseInventorySystem;