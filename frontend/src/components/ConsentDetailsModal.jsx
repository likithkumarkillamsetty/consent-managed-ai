import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { X, Check, Ban, Clock, History, AlertCircle, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function ConsentDetailsModal({ consentId, onClose, onRefresh }) {
  const [consent, setConsent] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [consentData, auditData] = await Promise.all([
        api.getConsentById(consentId),
        api.getConsentAudit(consentId),
      ]);
      setConsent(consentData);
      setAuditLogs(auditData);
    } catch (err) {
      setError(err.message || 'Failed to load consent details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (consentId) {
      loadData();
    }
  }, [consentId]);

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      await api.approveConsent(consentId);
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeny = async () => {
    if (!window.confirm('Deny this consent request?')) return;
    setActionLoading(true);
    try {
      await api.denyConsent(consentId);
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Denial failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!window.confirm('Revoke this consent? Access will immediately be blocked.')) return;
    setActionLoading(true);
    try {
      await api.revokeConsent(consentId);
      await loadData();
      if (onRefresh) onRefresh();
    } catch (err) {
      alert(`Revocation failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
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

  if (!consentId) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '780px' }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #1e293b',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <ShieldCheck size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f8fafc' }}>
              Consent Details & Audit Trail
            </h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: '0.25rem' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '1.5rem' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: '#94a3b8' }}>Loading consent...</div>
          ) : error ? (
            <div style={{ color: '#f87171', padding: '1rem', backgroundColor: 'rgba(239,68,68,0.1)', borderRadius: '8px' }}>
              {error}
            </div>
          ) : consent ? (
            <>
              {/* Primary Card */}
              <div style={{
                backgroundColor: '#0b1120',
                border: '1px solid #1e293b',
                borderRadius: '10px',
                padding: '1.25rem',
                marginBottom: '1.5rem',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Consent Identifier
                    </div>
                    <div className="font-mono" style={{ fontSize: '0.9rem', color: '#38bdf8', fontWeight: 600 }}>
                      {consent.consent_id}
                    </div>
                  </div>
                  <span className={`badge badge-${consent.status.toLowerCase()}`} style={{ fontSize: '0.85rem', padding: '0.35rem 0.8rem' }}>
                    {consent.status}
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', fontSize: '0.875rem' }}>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>User ID</span>
                    <strong style={{ color: '#f8fafc' }}>{consent.user_id}</strong>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Data Scope</span>
                    <span className="font-mono" style={{ color: '#cbd5e1' }}>{consent.data_scope}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Purpose</span>
                    <span className="font-mono" style={{ color: '#cbd5e1' }}>{consent.purpose}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Data Provider</span>
                    <span style={{ color: '#cbd5e1' }}>{consent.data_provider}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Data Consumer</span>
                    <span style={{ color: '#cbd5e1' }}>{consent.data_consumer}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Expires At</span>
                    <span style={{ color: '#cbd5e1' }}>{formatDate(consent.expires_at)}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Created At</span>
                    <span style={{ color: '#cbd5e1' }}>{formatDate(consent.created_at)}</span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Approved At</span>
                    <span style={{ color: '#cbd5e1' }}>{formatDate(consent.approved_at)}</span>
                  </div>
                  {consent.revoked_at && (
                    <div>
                      <span style={{ color: '#64748b', display: 'block', fontSize: '0.75rem' }}>Revoked At</span>
                      <span style={{ color: '#f87171' }}>{formatDate(consent.revoked_at)}</span>
                    </div>
                  )}
                </div>

                {/* State Actions */}
                <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid #1e293b', display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                  {consent.status === 'PENDING' && (
                    <>
                      <button
                        onClick={handleApprove}
                        disabled={actionLoading}
                        className="btn btn-success btn-sm"
                      >
                        <Check size={14} /> Approve Consent
                      </button>
                      <button
                        onClick={handleDeny}
                        disabled={actionLoading}
                        className="btn btn-danger btn-sm"
                      >
                        <X size={14} /> Deny Consent
                      </button>
                    </>
                  )}
                  {consent.status === 'APPROVED' && (
                    <button
                      onClick={handleRevoke}
                      disabled={actionLoading}
                      className="btn btn-danger btn-sm"
                    >
                      <Ban size={14} /> Revoke Consent
                    </button>
                  )}
                </div>
              </div>

              {/* Audit History Timeline */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <History size={16} color="#38bdf8" />
                  <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc' }}>
                    Audit History for this Consent
                  </h4>
                </div>

                {auditLogs.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '1rem', color: '#64748b', fontSize: '0.85rem' }}>
                    No audit records found.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {auditLogs.map((log) => (
                      <div
                        key={log.audit_id}
                        style={{
                          backgroundColor: '#0b1120',
                          border: '1px solid #1e293b',
                          borderRadius: '6px',
                          padding: '0.75rem 1rem',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.85rem',
                        }}
                      >
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                            <span className="font-mono" style={{ fontWeight: 600, color: '#38bdf8' }}>
                              {log.event_type}
                            </span>
                            <span className={`badge badge-${log.result === 'ALLOWED' || log.result === 'SUCCESS' ? 'approved' : 'denied'}`} style={{ fontSize: '0.65rem' }}>
                              {log.result}
                            </span>
                          </div>
                          <div style={{ color: '#94a3b8', fontSize: '0.78rem' }}>{log.details || '—'}</div>
                        </div>
                        <div style={{ color: '#64748b', fontSize: '0.75rem', textAlign: 'right' }}>
                          {formatDate(log.timestamp)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
