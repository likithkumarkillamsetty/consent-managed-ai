import React, { useState } from 'react';
import { api } from '../services/api';
import { ShieldPlus, CheckCircle2, ArrowRight, AlertCircle } from 'lucide-react';

export default function CreateConsent({ setActiveTab, onConsentCreated }) {
  const defaultFutureDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().slice(0, 16);
  };

  const [formData, setFormData] = useState({
    user_id: 'user001',
    data_provider: 'Bank',
    data_consumer: 'AI Platform',
    data_scope: 'TRANSACTION_DATA',
    purpose: 'AI_TRAINING',
    expires_at: defaultFutureDate(),
  });

  const [loading, setLoading] = useState(false);
  const [createdConsent, setCreatedConsent] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setCreatedConsent(null);

    try {
      // Ensure ISO string for expires_at
      const payload = {
        ...formData,
        expires_at: new Date(formData.expires_at).toISOString(),
      };
      const result = await api.createConsent(payload);
      setCreatedConsent(result);
      if (onConsentCreated) onConsentCreated(result);
    } catch (err) {
      setError(err.message || 'Failed to create consent request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '750px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
          Create Consent Request
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Initiate a new granular data access consent with purpose, scope, and time boundaries.
        </p>
      </div>

      {createdConsent ? (
        <div className="card" style={{ border: '1px solid rgba(16, 185, 129, 0.4)', background: 'rgba(16, 185, 129, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
            <CheckCircle2 size={28} color="#34d399" />
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>
                Consent Request Created Successfully
              </h2>
              <p style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                The request has been recorded with status <strong className="badge badge-pending">PENDING</strong> and logged to the Audit system.
              </p>
            </div>
          </div>

          <div style={{
            background: '#0b1120',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            border: '1px solid #1e293b',
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.875rem' }}>
              <div><span style={{ color: '#64748b' }}>Consent ID:</span> <span className="font-mono" style={{ color: '#38bdf8' }}>{createdConsent.consent_id}</span></div>
              <div><span style={{ color: '#64748b' }}>User ID:</span> <strong>{createdConsent.user_id}</strong></div>
              <div><span style={{ color: '#64748b' }}>Data Scope:</span> <span className="font-mono">{createdConsent.data_scope}</span></div>
              <div><span style={{ color: '#64748b' }}>Purpose:</span> <span className="font-mono">{createdConsent.purpose}</span></div>
              <div><span style={{ color: '#64748b' }}>Data Provider:</span> {createdConsent.data_provider}</div>
              <div><span style={{ color: '#64748b' }}>Data Consumer:</span> {createdConsent.data_consumer}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={() => setActiveTab('consents')}
              className="btn btn-primary"
            >
              Go to Consent Registry <ArrowRight size={16} />
            </button>
            <button
              onClick={() => {
                setCreatedConsent(null);
              }}
              className="btn btn-secondary"
            >
              Create Another Consent
            </button>
          </div>
        </div>
      ) : (
        <div className="card">
          {error && (
            <div style={{
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#f87171',
              padding: '0.85rem 1rem',
              borderRadius: '8px',
              marginBottom: '1.5rem',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">User ID (Data Principal)</label>
                <input
                  type="text"
                  name="user_id"
                  className="form-input"
                  required
                  placeholder="e.g. user001"
                  value={formData.user_id}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Expiry Date & Time</label>
                <input
                  type="datetime-local"
                  name="expires_at"
                  className="form-input"
                  required
                  value={formData.expires_at}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Data Provider (Custodian)</label>
                <input
                  type="text"
                  name="data_provider"
                  className="form-input"
                  required
                  placeholder="e.g. Bank, Hospital, Telecom"
                  value={formData.data_provider}
                  onChange={handleChange}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Data Consumer (AI / Requester)</label>
                <input
                  type="text"
                  name="data_consumer"
                  className="form-input"
                  required
                  placeholder="e.g. AI Platform, Analytics Engine"
                  value={formData.data_consumer}
                  onChange={handleChange}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Data Scope</label>
                <select
                  name="data_scope"
                  className="form-select"
                  value={formData.data_scope}
                  onChange={handleChange}
                >
                  <option value="CUSTOMER_PROFILE">CUSTOMER_PROFILE</option>
                  <option value="TRANSACTION_DATA">TRANSACTION_DATA</option>
                  <option value="HEALTH_DATA">HEALTH_DATA</option>
                  <option value="LOCATION_DATA">LOCATION_DATA</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Purpose (Bound Usage)</label>
                <select
                  name="purpose"
                  className="form-select"
                  value={formData.purpose}
                  onChange={handleChange}
                >
                  <option value="AI_TRAINING">AI_TRAINING</option>
                  <option value="FRAUD_DETECTION">FRAUD_DETECTION</option>
                  <option value="ANALYTICS">ANALYTICS</option>
                  <option value="MARKETING">MARKETING</option>
                </select>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                type="button"
                onClick={() => setActiveTab('consents')}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                id="btn-submit-consent"
                disabled={loading}
                className="btn btn-primary"
              >
                <ShieldPlus size={16} />
                {loading ? 'Submitting Request...' : 'Create Consent Request'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
