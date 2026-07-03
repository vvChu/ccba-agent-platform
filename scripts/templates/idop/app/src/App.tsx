import React, { useState } from 'react';
import './App.css';

interface Lead {
  id: number;
  contactPerson: string;
  email: string;
  phone: string;
  status: 'lead' | 'contacted' | 'proposal' | 'contracted' | 'lost';
  estimatedValue: number;
  assignedTo: string;
}

const INITIAL_LEADS: Lead[] = [
  { id: 1, contactPerson: 'John Doe', email: 'john@example.com', phone: '+123456789', status: 'lead', estimatedValue: 15000, assignedTo: 'Alice Smith' },
  { id: 2, contactPerson: 'Jane Smith', email: 'jane@example.com', phone: '+987654321', status: 'proposal', estimatedValue: 45000, assignedTo: 'Bob Johnson' },
  { id: 3, contactPerson: 'David Miller', email: 'david@example.com', phone: '+112233445', status: 'contracted', estimatedValue: 75000, assignedTo: 'Charlie Brown' }
];

const PIPELINE_STEPS = [
  'Lead Intake',
  'Quotation',
  'Approvals',
  'CDE Provisioning',
  'Task Assignment',
  'Timesheet Log',
  'Expense Track',
  'Invoice Gen',
  'Cashflow Update',
  'KPI Dashboard',
  'Project Closure'
];

export default function App() {
  const [leads, setLeads] = useState<Lead[]>(INITIAL_LEADS);
  const [activeStep, setActiveStep] = useState<number>(3); // Default: CDE Provisioning (index 3)
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [contactPerson, setContactPerson] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [status, setStatus] = useState<Lead['status']>('lead');
  const [estimatedValue, setEstimatedValue] = useState('');
  const [assignedTo, setAssignedTo] = useState('');

  // Derived metrics
  const totalLeads = leads.length;
  const pipelineValue = leads.reduce((sum, l) => sum + l.estimatedValue, 0);
  const activeApprovals = leads.filter(l => l.status === 'proposal').length;
  const integrationStatus = 'Online';

  const handleCreateLead = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactPerson || !email) return;

    const newLead: Lead = {
      id: Date.now(),
      contactPerson,
      email,
      phone,
      status,
      estimatedValue: Number(estimatedValue) || 0,
      assignedTo: assignedTo || 'Unassigned'
    };

    setLeads([...leads, newLead]);
    setIsModalOpen(false);

    // Reset Form
    setContactPerson('');
    setEmail('');
    setPhone('');
    setStatus('lead');
    setEstimatedValue('');
    setAssignedTo('');
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="header">
        <div>
          <h1>CCBA IDOP Deployment Dashboard</h1>
          <p style={{ color: '#64748b', margin: '4px 0 0 0', fontSize: '0.9rem' }}>
            Premium SharePoint Integrated Deployment Operations Platform (IDOP)
          </p>
        </div>
        <div style={{ color: '#10b981', fontWeight: 600, fontSize: '0.9rem' }}>
          ● System Active
        </div>
      </header>

      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>CRM Leads</h3>
          <div className="metric-value">{totalLeads}</div>
        </div>
        <div className="metric-card">
          <h3>Pipeline Value</h3>
          <div className="metric-value">${pipelineValue.toLocaleString()}</div>
        </div>
        <div className="metric-card">
          <h3>Active Approvals</h3>
          <div className="metric-value">{activeApprovals}</div>
        </div>
        <div className="metric-card">
          <h3>Integration Status</h3>
          <div className="metric-value" style={{ color: '#10b981' }}>{integrationStatus}</div>
        </div>
      </div>

      {/* 11-Step Pipeline Tracker */}
      <div className="pipeline-tracker">
        <h2>11-Step Power Automate Pipeline Tracker</h2>
        <div className="steps-container">
          {PIPELINE_STEPS.map((step, index) => {
            let className = 'step-node';
            if (index < activeStep) className += ' completed';
            else if (index === activeStep) className += ' active';
            return (
              <div 
                key={step} 
                className={className}
                style={{ cursor: 'pointer' }}
                onClick={() => setActiveStep(index)}
                title={`Click to set active step to ${step}`}
              >
                <div className="step-circle">
                  {index < activeStep ? '✓' : index + 1}
                </div>
                <div className="step-label">{step}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Leads Table Section */}
      <div className="leads-section">
        <div className="section-header">
          <h2>Active CRM Leads</h2>
          <button className="btn-primary" onClick={() => setIsModalOpen(true)}>
            + Add New Lead
          </button>
        </div>

        <table className="leads-table">
          <thead>
            <tr>
              <th>Contact Person</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Status</th>
              <th>Estimated Value</th>
              <th>Assigned To</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>{lead.contactPerson}</td>
                <td>{lead.email}</td>
                <td>{lead.phone || 'N/A'}</td>
                <td>
                  <span className={`status-badge ${lead.status}`}>{lead.status}</span>
                </td>
                <td>${lead.estimatedValue.toLocaleString()}</td>
                <td>{lead.assignedTo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Interactive Modal */}
      {isModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <h3>Add New CRM Lead</h3>
            <form onSubmit={handleCreateLead}>
              <div className="form-group">
                <label>Contact Person *</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={contactPerson} 
                  onChange={(e) => setContactPerson(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input 
                  type="email" 
                  className="form-control" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={phone} 
                  onChange={(e) => setPhone(e.target.value)} 
                />
              </div>
              <div className="form-group">
                <label>Status</label>
                <select 
                  className="form-control" 
                  value={status} 
                  onChange={(e) => setStatus(e.target.value as Lead['status'])}
                >
                  <option value="lead">Lead</option>
                  <option value="contacted">Contacted</option>
                  <option value="proposal">Proposal</option>
                  <option value="contracted">Contracted</option>
                  <option value="lost">Lost</option>
                </select>
              </div>
              <div className="form-group">
                <label>Estimated Value ($)</label>
                <input 
                  type="number" 
                  className="form-control" 
                  value={estimatedValue} 
                  onChange={(e) => setEstimatedValue(e.target.value)} 
                />
              </div>
              <div className="form-group">
                <label>Assigned To</label>
                <input 
                  type="text" 
                  className="form-control" 
                  value={assignedTo} 
                  onChange={(e) => setAssignedTo(e.target.value)} 
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
