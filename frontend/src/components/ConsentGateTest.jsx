import React, { useState } from 'react';
import { api } from '../services/api';
import { Key, ShieldCheck, ShieldAlert, CheckCircle2, XCircle, ArrowRight, Play } from 'lucide-react';

export default function ConsentGateTest({ onAccessChecked }) {
  const [formData, setFormData] = useState({
    user_id: 'user001',
    data_scope: 'TRANSACTION_DATA',
    purpose: 'AI_TRAINING',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleCheckAccess = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await api.checkGateAccess(formData);
      setResult(res);
      if (onAccessChecked) onAccessChecked();
    } catch (err) {
      setError(err.message || 'Error communicating with Consent Gate');
    } finally {
      setLoading(false);
    }
  };

  const setScenario = (user_id, data_scope, purpose) => {
    setFormData({ user_id, data_scope, purpose });
    setResult(null);
  };

  return (
    <div style={{ maxWidth: '850px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.25rem' }}>
          Consent Gate Enforcement Simulator
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
          Real-time enforcement checkpoint. The backend validates user identity, purpose binding, data scope, and expiry directly from the database.
        </p>
      </div>

      {/* Demo Scenario Presets */}
      <div className="card" style={{ marginBottom: '1.5rem', backgroundColor: '#0b1120' }}>
        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
          Project Review Demo Scenarios
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.5rem' }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '0.78rem' }}
            onClick={() => setScenario('user001', 'TRANSACTION_DATA', 'AI_TRAINING')}
          >
            <Play size={12} color="#34d399" /> Step 3: Valid Access (AI_TRAINING)
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '0.78rem' }}
            onClick={() => setScenario('user001', 'TRANSACTION_DATA', 'MARKETING')}
          >
            <Play size={12} color="#f87171" /> Step 4: Wrong Purpose (MARKETING)
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '0.78rem' }}
            onClick={() => setScenario('user001', 'HEALTH_DATA', 'AI_TRAINING')}
          >
            <Play size={12} color="#f87171" /> Wrong Scope Test (HEALTH_DATA)
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ textAlign: 'left', justifyContent: 'flex-start', fontSize: '0.78rem' }}
            onClick={() => setScenario('unknown_user', 'TRANSACTION_DATA', 'AI_TRAINING')}
          >
            <Play size={12} color="#f87171" /> Non-Existent User Test
          </button>
        </div>
      </div>

      {/* Check Access Form */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleCheckAccess}>
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">User ID (Principal)</label>
              <input
                type="text"
                name="user_id"
                id="input-gate-user"
                className="form-input"
                required
                placeholder="e.g. user001"
                value={formData.user_id}
                onChange={handleChange}
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Requested Data Scope</label>
              <select
                name="data_scope"
                id="input-gate-scope"
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

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Requested Purpose</label>
              <select
                name="purpose"
                id="input-gate-purpose"
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

          <button
            type="submit"
            id="btn-gate-check"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem', fontSize: '1rem', fontWeight: 600 }}
          >
            <Key size={18} />
            {loading ? 'Evaluating Policy Enforcement...' : 'Check Access'}
          </button>
        </form>
      </div>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
        }}>
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div
          id="gate-result-box"
          className="card"
          style={{
            backgroundColor: result.allowed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
            borderColor: result.allowed ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)',
            textAlign: 'center',
            padding: '2rem 1.5rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            {result.allowed ? (
              <div style={{
                background: 'rgba(16, 185, 129, 0.2)',
                borderRadius: '50%',
                padding: '1rem',
                border: '2px solid rgba(16, 185, 129, 0.5)',
              }}>
                <CheckCircle2 size={48} color="#34d399" />
              </div>
            ) : (
              <div style={{
                background: 'rgba(239, 68, 68, 0.2)',
                borderRadius: '50%',
                padding: '1rem',
                border: '2px solid rgba(239, 68, 68, 0.5)',
              }}>
                <XCircle size={48} color="#f87171" />
              </div>
            )}
          </div>

          <div style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            letterSpacing: '0.05em',
            color: result.allowed ? '#34d399' : '#f87171',
            marginBottom: '0.5rem',
          }}>
            {result.allowed ? 'ACCESS ALLOWED' : 'ACCESS BLOCKED'}
          </div>

          <div style={{ fontSize: '1.1rem', color: '#f8fafc', fontWeight: 500, marginBottom: '1rem' }}>
            Reason: <span className="font-mono" style={{ color: result.allowed ? '#34d399' : '#f87171', fontWeight: 700 }}>{result.reason}</span>
          </div>

          <div style={{
            display: 'inline-block',
            backgroundColor: '#0b1120',
            border: '1px solid #1e293b',
            borderRadius: '6px',
            padding: '0.5rem 1rem',
            fontSize: '0.8rem',
            color: '#94a3b8',
          }}>
            Evaluated for Principal <strong style={{ color: '#38bdf8' }}>{formData.user_id}</strong> &bull; Scope <strong style={{ color: '#cbd5e1' }}>{formData.data_scope}</strong> &bull; Purpose <strong style={{ color: '#cbd5e1' }}>{formData.purpose}</strong>
          </div>
        </div>
      )}
    </div>
  );
}
