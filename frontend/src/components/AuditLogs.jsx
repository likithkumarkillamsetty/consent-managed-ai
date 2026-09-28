import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { History, Search, RefreshCw, ShieldAlert, ShieldCheck } from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userFilter, setUserFilter] = useState('');
  const [consentFilter, setConsentFilter] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLogs(userFilter || null, consentFilter || null);
      setLogs(data);
    } catch (err) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    fetchLogs();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const d = new Date(dateStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getResultBadgeClass = (result) => {
    switch (result) {
      case 'ALLOWED':
      case 'SUCCESS':
        return 'badge-approved';
      case 'BLOCKED':
      case 'DENIED':
        return 'badge-denied';
      case 'REVOKED':
        return 'badge-revoked';
      case 'EXPIRED':
        return 'badge-expired';
      default:
        return 'badge-pending';
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
            System Audit Trail
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Immutable chronological record of all consent creations, state mutations, and gate access decisions.
          </p>
        </div>
        <button
          onClick={fetchLogs}
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh Logs
        </button>
      </div>

      {/* Filter bar */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <form onSubmit={handleFilterSubmit} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Filter by User ID (e.g. user001)..."
              value={userFilter}
              onChange={(e) => setUserFilter(e.target.value)}
            />
          </div>
          <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Filter by Consent ID UUID..."
              value={consentFilter}
              onChange={(e) => setConsentFilter(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-secondary btn-sm">
            <Search size={14} /> Filter Logs
          </button>
        </form>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '0.85rem 1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
        }}>
          {error}
        </div>
      )}

      {/* Logs Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
            Loading audit records...
          </div>
        ) : logs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
            No audit records found matching the filter.
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event</th>
                  <th>Result</th>
                  <th>User ID</th>
                  <th>Data Scope</th>
                  <th>Purpose</th>
                  <th>Consent ID</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr key={l.audit_id}>
                    <td style={{ fontSize: '0.8rem', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                      {formatDate(l.timestamp)}
                    </td>
                    <td>
                      <span className="font-mono" style={{ fontSize: '0.8rem', fontWeight: 600, color: '#f8fafc' }}>
                        {l.event_type}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getResultBadgeClass(l.result)}`}>
                        {l.result}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, color: '#38bdf8' }}>
                      {l.user_id || '—'}
                    </td>
                    <td>
                      <span className="font-mono" style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                        {l.data_scope || '—'}
                      </span>
                    </td>
                    <td>
                      <span className="font-mono" style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
                        {l.purpose || '—'}
                      </span>
                    </td>
                    <td>
                      {l.consent_id ? (
                        <span className="font-mono" style={{ fontSize: '0.75rem', color: '#64748b' }} title={l.consent_id}>
                          {l.consent_id.substring(0, 8)}...
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                      {l.details || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
