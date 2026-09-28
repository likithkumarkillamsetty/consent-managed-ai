import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ShieldCheck, ShieldAlert, Clock, Ban, CheckCircle2, XCircle, ArrowRight, RefreshCw, Key, Plus } from 'lucide-react';

export default function Dashboard({ setActiveTab, onSelectConsent }) {
  const [summary, setSummary] = useState(null);
  const [recentConsents, setRecentConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumData, consentsData] = await Promise.all([
        api.getSummary(),
        api.getConsents(),
      ]);
      setSummary(sumData);
      setRecentConsents(consentsData.slice(0, 5));
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const stats = [
    {
      title: 'Total Consents',
      value: summary ? summary.total_consents : '-',
      icon: ShieldCheck,
      color: '#38bdf8',
      bg: 'rgba(56, 189, 248, 0.1)',
      border: 'rgba(56, 189, 248, 0.25)',
    },
    {
      title: 'Approved',
      value: summary ? summary.approved_consents : '-',
      icon: CheckCircle2,
      color: '#34d399',
      bg: 'rgba(16, 185, 129, 0.1)',
      border: 'rgba(16, 185, 129, 0.25)',
    },
    {
      title: 'Pending',
      value: summary ? summary.pending_consents : '-',
      icon: Clock,
      color: '#fbbf24',
      bg: 'rgba(245, 158, 11, 0.1)',
      border: 'rgba(245, 158, 11, 0.25)',
    },
    {
      title: 'Revoked',
      value: summary ? summary.revoked_consents : '-',
      icon: Ban,
      color: '#c084fc',
      bg: 'rgba(168, 85, 247, 0.1)',
      border: 'rgba(168, 85, 247, 0.25)',
    },
    {
      title: 'Blocked Access',
      value: summary ? summary.total_access_blocked : '-',
      icon: ShieldAlert,
      color: '#f87171',
      bg: 'rgba(239, 68, 68, 0.1)',
      border: 'rgba(239, 68, 68, 0.25)',
    },
  ];

  return (
    <div>
      {/* Header Banner */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
      }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
            Consent Governance Dashboard
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Live enterprise consent status, gate access enforcement metrics, and audit summary.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={loadData}
            className="btn btn-secondary btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            id="btn-quick-create"
            onClick={() => setActiveTab('create')}
            className="btn btn-primary btn-sm"
          >
            <Plus size={14} />
            New Consent Request
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          fontSize: '0.875rem',
        }}>
          {error}
        </div>
      )}

      {/* Metrics Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem',
      }}>
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              className="card"
              style={{
                backgroundColor: stat.bg,
                borderColor: stat.border,
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {stat.title}
                </span>
                <Icon size={20} color={stat.color} />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: stat.color, lineHeight: 1 }}>
                {loading ? '...' : stat.value}
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Action Highlights */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1.5fr 1fr',
        gap: '1.5rem',
        marginBottom: '2rem',
      }}>
        {/* Recent Consents Card */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc' }}>
              Recent Consent Requests
            </h2>
            <button
              onClick={() => setActiveTab('consents')}
              style={{ background: 'none', border: 'none', color: '#38bdf8', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
            >
              View All <ArrowRight size={14} />
            </button>
          </div>

          {recentConsents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.875rem' }}>
              No consent requests found. Create one to get started.
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Scope</th>
                    <th>Purpose</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {recentConsents.map((c) => (
                    <tr key={c.consent_id}>
                      <td style={{ fontWeight: 600, color: '#38bdf8' }}>{c.user_id}</td>
                      <td><span className="font-mono" style={{ fontSize: '0.75rem' }}>{c.data_scope}</span></td>
                      <td><span className="font-mono" style={{ fontSize: '0.75rem' }}>{c.purpose}</span></td>
                      <td>
                        <span className={`badge badge-${c.status.toLowerCase()}`}>
                          {c.status}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => onSelectConsent(c.consent_id)}
                          className="btn btn-secondary btn-sm"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Consent Gate Quick Tester Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <Key size={20} color="#38bdf8" />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc' }}>
                Consent Gate Engine
              </h2>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', lineHeight: '1.5', marginBottom: '1rem' }}>
              The Consent Gate operates as the central policy enforcement point. It validates user authorization, active scopes, specific purpose bindings, and time-validity in real time before data access is allowed.
            </p>
            <div style={{
              backgroundColor: '#0b1120',
              border: '1px solid #1e293b',
              borderRadius: '8px',
              padding: '0.85rem',
              fontSize: '0.8rem',
              color: '#cbd5e1',
              marginBottom: '1rem',
            }}>
              <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: '0.25rem' }}>Core Enforcement Guarantees:</div>
              <ul style={{ paddingLeft: '1.2rem', margin: 0 }}>
                <li>Purpose mismatch block (<code className="font-mono">PURPOSE_NOT_ALLOWED</code>)</li>
                <li>Scope violation block (<code className="font-mono">DATA_SCOPE_NOT_ALLOWED</code>)</li>
                <li>Revocation & expiry real-time checks</li>
              </ul>
            </div>
          </div>

          <button
            id="btn-goto-gate"
            onClick={() => setActiveTab('gate')}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            Launch Consent Gate Tester
          </button>
        </div>
      </div>
    </div>
  );
}
