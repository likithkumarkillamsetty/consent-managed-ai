import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Check, X, Ban, Eye, Search, Filter, RefreshCw } from 'lucide-react';

export default function ConsentList({ onSelectConsent, onRefreshSummary }) {
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [actionLoading, setActionLoading] = useState({});

  const fetchConsents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getConsents(userSearch || null, statusFilter || null);
      setConsents(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch consents');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsents();
  }, [statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchConsents();
  };

  const handleApprove = async (consentId) => {
    setActionLoading((prev) => ({ ...prev, [consentId]: true }));
    try {
      await api.approveConsent(consentId);
      await fetchConsents();
      if (onRefreshSummary) onRefreshSummary();
    } catch (err) {
      alert(`Approval error: ${err.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [consentId]: false }));
    }
  };

  const handleDeny = async (consentId) => {
    if (!window.confirm('Are you sure you want to deny this consent request?')) return;
    setActionLoading((prev) => ({ ...prev, [consentId]: true }));
    try {
      await api.denyConsent(consentId);
      await fetchConsents();
      if (onRefreshSummary) onRefreshSummary();
    } catch (err) {
      alert(`Denial error: ${err.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [consentId]: false }));
    }
  };

  const handleRevoke = async (consentId) => {
    if (!window.confirm('Are you sure you want to revoke this approved consent? Access will be immediately blocked.')) return;
    setActionLoading((prev) => ({ ...prev, [consentId]: true }));
    try {
      await api.revokeConsent(consentId);
      await fetchConsents();
      if (onRefreshSummary) onRefreshSummary();
    } catch (err) {
      alert(`Revocation error: ${err.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [consentId]: false }));
    }
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
    });
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
            Consent Registry
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Inspect, approve, deny, or revoke user data sharing consents.
          </p>
        </div>
        <button
          onClick={fetchConsents}
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filter & Search Controls */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '220px', display: 'flex', alignItems: 'center', position: 'relative' }}>
            <Search size={16} color="#64748b" style={{ position: 'absolute', left: '0.75rem' }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: '2.25rem' }}
              placeholder="Filter by User ID (e.g. user001)..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '180px' }}>
            <Filter size={16} color="#64748b" />
            <select
              className="form-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="APPROVED">APPROVED</option>
              <option value="DENIED">DENIED</option>
              <option value="REVOKED">REVOKED</option>
              <option value="EXPIRED">EXPIRED</option>
            </select>
          </div>

          <button type="submit" className="btn btn-secondary btn-sm">
            Apply Filters
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
          fontSize: '0.875rem',
        }}>
          {error}
        </div>
      )}

      {/* Consents Table */}
      <div className="card" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
            Loading consent registry...
          </div>
        ) : consents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
            No consents matching the criteria.
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Consent ID</th>
                  <th>User</th>
                  <th>Data Scope</th>
                  <th>Purpose</th>
                  <th>Status</th>
                  <th>Created At</th>
                  <th>Expires At</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {consents.map((c) => {
                  const isLoading = actionLoading[c.consent_id];
                  return (
                    <tr key={c.consent_id}>
                      <td>
                        <span
                          onClick={() => onSelectConsent(c.consent_id)}
                          style={{
                            color: '#38bdf8',
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                          }}
                        >
                          {c.consent_id.substring(0, 8)}...
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>{c.user_id}</td>
                      <td><span className="font-mono" style={{ fontSize: '0.8rem' }}>{c.data_scope}</span></td>
                      <td><span className="font-mono" style={{ fontSize: '0.8rem' }}>{c.purpose}</span></td>
                      <td>
                        <span className={`badge badge-${c.status.toLowerCase()}`}>
                          {c.status}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{formatDate(c.created_at)}</td>
                      <td style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{formatDate(c.expires_at)}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                          {/* Approve (Only PENDING) */}
                          {c.status === 'PENDING' && (
                            <>
                              <button
                                id={`btn-approve-${c.consent_id}`}
                                onClick={() => handleApprove(c.consent_id)}
                                disabled={isLoading}
                                className="btn btn-success btn-sm"
                                title="Approve Consent"
                              >
                                <Check size={14} /> Approve
                              </button>
                              <button
                                id={`btn-deny-${c.consent_id}`}
                                onClick={() => handleDeny(c.consent_id)}
                                disabled={isLoading}
                                className="btn btn-danger btn-sm"
                                title="Deny Consent"
                              >
                                <X size={14} /> Deny
                              </button>
                            </>
                          )}

                          {/* Revoke (Only APPROVED) */}
                          {c.status === 'APPROVED' && (
                            <button
                              id={`btn-revoke-${c.consent_id}`}
                              onClick={() => handleRevoke(c.consent_id)}
                              disabled={isLoading}
                              className="btn btn-danger btn-sm"
                              title="Revoke Consent"
                            >
                              <Ban size={14} /> Revoke
                            </button>
                          )}

                          {/* View details */}
                          <button
                            id={`btn-view-${c.consent_id}`}
                            onClick={() => onSelectConsent(c.consent_id)}
                            className="btn btn-secondary btn-sm"
                            title="View Full Details & Audit"
                          >
                            <Eye size={14} /> View
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
