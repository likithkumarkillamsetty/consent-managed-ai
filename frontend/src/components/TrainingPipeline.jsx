import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function TrainingPipeline() {
  const [datasets, setDatasets] = useState([]);
  const [preview, setPreview] = useState(null);
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [lineage, setLineage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [training, setTraining] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    dataset_name: 'transaction_fraud_dataset',
    data_scope: 'TRANSACTION_DATA',
    purpose: 'AI_TRAINING',
    model_type: 'logistic_regression',
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [dsList, batchList] = await Promise.all([
        api.getDatasets().catch(() => []),
        api.getTrainingBatches().catch(() => []),
      ]);
      setDatasets(dsList);
      setBatches(batchList);
      if (dsList.length > 0) {
        loadPreview(dsList[0].dataset_name);
      }
    } catch (err) {
      setFeedback({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadPreview = async (name) => {
    try {
      const prev = await api.previewDataset(name, 10);
      setPreview(prev);
    } catch (err) {
      setPreview(null);
    }
  };

  const handleSeed = async (force = false) => {
    setSeeding(true);
    setFeedback(null);
    try {
      const res = await api.seedDataset('transaction_fraud_dataset', force);
      setFeedback({
        type: 'success',
        message: `Dataset seeded! ${res.records_seeded} records seeded (Total: ${res.total_records}).`,
      });
      loadData();
    } catch (err) {
      setFeedback({ type: 'error', message: `Seed error: ${err.message}` });
    } finally {
      setSeeding(false);
    }
  };

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    setTraining(true);
    setFeedback(null);
    try {
      const batch = await api.createTrainingBatch(formData);
      setFeedback({
        type: batch.status === 'COMPLETED' ? 'success' : 'warning',
        message: `Training Batch ${batch.batch_id} created! Status: ${batch.status}. Allowed: ${batch.allowed_records}, Blocked: ${batch.blocked_records}. Accuracy: ${(batch.accuracy * 100 || 0).toFixed(1)}%`,
      });
      loadData();
      viewBatchDetails(batch.batch_id);
    } catch (err) {
      setFeedback({ type: 'error', message: `Training error: ${err.message}` });
    } finally {
      setTraining(false);
    }
  };

  const viewBatchDetails = async (batchId) => {
    try {
      const [batchData, linData] = await Promise.all([
        api.getTrainingBatch(batchId),
        api.getBatchLineage(batchId),
      ]);
      setSelectedBatch(batchData);
      setLineage(linData);
    } catch (err) {
      setFeedback({ type: 'error', message: `Lineage error: ${err.message}` });
    }
  };

  return (
    <div style={{ marginTop: '1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.5rem' }}>
          Module 2: Consent-Aware ML Training & Data Lineage
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
          Real-time gated ML training pipeline enforcing DEPA-inspired purpose binding. Only records with active, approved consent enter training batches, with complete lineage tracking.
        </p>
      </div>

      {feedback && (
        <div style={{
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '1.5rem',
          backgroundColor: feedback.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : (feedback.type === 'warning' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)'),
          border: `1px solid ${feedback.type === 'success' ? '#10b981' : (feedback.type === 'warning' ? '#f59e0b' : '#ef4444')}`,
          color: feedback.type === 'success' ? '#34d399' : (feedback.type === 'warning' ? '#fbbf24' : '#f87171'),
          fontSize: '0.9rem',
        }}>
          {feedback.message}
        </div>
      )}

      {/* Grid: Dataset Seeding & Training Request */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        
        {/* Section 1: Synthetic Dataset */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f1f5f9' }}>1. Synthetic Dataset</h2>
            <button
              onClick={() => handleSeed(true)}
              disabled={seeding}
              style={{
                backgroundColor: '#3b82f6',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.4rem 0.8rem',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: seeding ? 'not-allowed' : 'pointer',
              }}
            >
              {seeding ? 'Seeding...' : 'Seed / Reseed Dataset'}
            </button>
          </div>

          {datasets.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No dataset seeded. Click "Seed Dataset" to populate synthetic transactions.</p>
          ) : (
            <div>
              {datasets.map((d) => (
                <div key={d.dataset_name} style={{ backgroundColor: '#1e293b', borderRadius: '8px', padding: '1rem', marginBottom: '0.75rem' }}>
                  <div style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.95rem' }}>{d.dataset_name}</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem', marginTop: '0.5rem', fontSize: '0.8rem', color: '#cbd5e1' }}>
                    <div>Total Records: <strong>{d.total_records}</strong></div>
                    <div>Unique Users: <strong>{d.unique_users}</strong></div>
                    <div>Fraud Cases: <strong style={{ color: '#f87171' }}>{d.fraud_count}</strong></div>
                    <div>Legitimate: <strong style={{ color: '#34d399' }}>{d.legit_count}</strong></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {preview && preview.records && (
            <div style={{ marginTop: '1rem' }}>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.5rem' }}>Sample Preview (First 5 records):</div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '0.75rem', textAlign: 'left', borderCollapse: 'collapse', color: '#e2e8f0' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                      <th style={{ padding: '4px' }}>ID</th>
                      <th style={{ padding: '4px' }}>User</th>
                      <th style={{ padding: '4px' }}>Amount</th>
                      <th style={{ padding: '4px' }}>Category</th>
                      <th style={{ padding: '4px' }}>Fraud</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.records.slice(0, 5).map((r) => (
                      <tr key={r.record_id} style={{ borderBottom: '1px solid #1e293b' }}>
                        <td style={{ padding: '4px' }}>{r.record_id}</td>
                        <td style={{ padding: '4px' }}>{r.user_id}</td>
                        <td style={{ padding: '4px' }}>${r.transaction_amount}</td>
                        <td style={{ padding: '4px' }}>{r.transaction_category}</td>
                        <td style={{ padding: '4px', color: r.fraud_label === 1 ? '#f87171' : '#34d399' }}>
                          {r.fraud_label === 1 ? 'Fraud' : 'Legit'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Section 2: Create Training Batch */}
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem' }}>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '1rem' }}>
            2. Run Consent-Gated Training Batch
          </h2>
          <form onSubmit={handleCreateBatch}>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Dataset Name</label>
              <input
                type="text"
                value={formData.dataset_name}
                onChange={(e) => setFormData({ ...formData, dataset_name: e.target.value })}
                required
                style={{ width: '100%', padding: '0.5rem', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', fontSize: '0.85rem' }}
              />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Data Scope</label>
              <select
                value={formData.data_scope}
                onChange={(e) => setFormData({ ...formData, data_scope: e.target.value })}
                style={{ width: '100%', padding: '0.5rem', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', fontSize: '0.85rem' }}
              >
                <option value="TRANSACTION_DATA">TRANSACTION_DATA</option>
                <option value="CUSTOMER_PROFILE">CUSTOMER_PROFILE</option>
                <option value="HEALTH_DATA">HEALTH_DATA</option>
                <option value="LOCATION_DATA">LOCATION_DATA</option>
              </select>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Purpose</label>
              <select
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                style={{ width: '100%', padding: '0.5rem', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#f8fafc', fontSize: '0.85rem' }}
              >
                <option value="AI_TRAINING">AI_TRAINING</option>
                <option value="FRAUD_DETECTION">FRAUD_DETECTION</option>
                <option value="MARKETING">MARKETING</option>
                <option value="ANALYTICS">ANALYTICS</option>
              </select>
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.25rem' }}>Model Type</label>
              <input
                type="text"
                value={formData.model_type}
                readOnly
                style={{ width: '100%', padding: '0.5rem', backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#94a3b8', fontSize: '0.85rem' }}
              />
            </div>

            <button
              type="submit"
              disabled={training}
              style={{
                width: '100%',
                backgroundColor: '#10b981',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                padding: '0.65rem',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: training ? 'not-allowed' : 'pointer',
              }}
            >
              {training ? 'Validating Consent & Training...' : 'Execute ML Training Run'}
            </button>
          </form>
        </div>
      </div>

      {/* Section 3: Training Batches List */}
      <div style={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 600, color: '#f1f5f9', marginBottom: '1rem' }}>
          3. Training Batches & Lineage History
        </h2>

        {batches.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No training batches executed yet.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '0.85rem', color: '#e2e8f0' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '8px' }}>Batch ID</th>
                  <th style={{ padding: '8px' }}>Purpose & Scope</th>
                  <th style={{ padding: '8px' }}>Status</th>
                  <th style={{ padding: '8px' }}>Records (Allowed/Blocked)</th>
                  <th style={{ padding: '8px' }}>Accuracy</th>
                  <th style={{ padding: '8px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((b) => (
                  <tr key={b.batch_id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '8px', fontWeight: 600, color: '#38bdf8' }}>{b.batch_id}</td>
                    <td style={{ padding: '8px' }}>
                      <div>{b.purpose}</div>
                      <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{b.data_scope}</div>
                    </td>
                    <td style={{ padding: '8px' }}>
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: b.status === 'COMPLETED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: b.status === 'COMPLETED' ? '#34d399' : '#f87171',
                      }}>
                        {b.status}
                      </span>
                    </td>
                    <td style={{ padding: '8px' }}>
                      <span style={{ color: '#34d399', fontWeight: 600 }}>{b.allowed_records}</span> / <span style={{ color: '#f87171' }}>{b.blocked_records}</span> (Total: {b.total_records})
                    </td>
                    <td style={{ padding: '8px', fontWeight: 600 }}>
                      {b.accuracy !== null ? `${(b.accuracy * 100).toFixed(1)}%` : 'N/A'}
                    </td>
                    <td style={{ padding: '8px' }}>
                      <button
                        onClick={() => viewBatchDetails(b.batch_id)}
                        style={{
                          backgroundColor: '#334155',
                          color: '#f8fafc',
                          border: 'none',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          fontSize: '0.75rem',
                          cursor: 'pointer',
                        }}
                      >
                        Inspect Lineage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 4: Lineage Details Modal/Panel */}
      {selectedBatch && lineage && (
        <div style={{ backgroundColor: '#0f172a', border: '1px solid #38bdf8', borderRadius: '12px', padding: '1.5rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>
                Batch Lineage: {selectedBatch.batch_id}
              </h2>
              <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                Total: {lineage.total_records} records &bull; Allowed: <span style={{ color: '#34d399', fontWeight: 600 }}>{lineage.allowed_records}</span> &bull; Blocked: <span style={{ color: '#f87171', fontWeight: 600 }}>{lineage.blocked_records}</span>
              </div>
            </div>
            <button
              onClick={() => { setSelectedBatch(null); setLineage(null); }}
              style={{ backgroundColor: '#334155', color: '#f8fafc', border: 'none', borderRadius: '6px', padding: '6px 12px', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              Close
            </button>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '0.8rem', color: '#e2e8f0' }}>
              <thead style={{ position: 'sticky', top: 0, backgroundColor: '#0f172a' }}>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '6px' }}>Record ID</th>
                  <th style={{ padding: '6px' }}>User ID</th>
                  <th style={{ padding: '6px' }}>Consent ID</th>
                  <th style={{ padding: '6px' }}>Decision</th>
                  <th style={{ padding: '6px' }}>Reason</th>
                  <th style={{ padding: '6px' }}>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {lineage.records.map((r) => (
                  <tr key={r.lineage_id} style={{ borderBottom: '1px solid #1e293b' }}>
                    <td style={{ padding: '6px' }}>{r.record_id}</td>
                    <td style={{ padding: '6px', fontWeight: 600 }}>{r.user_id}</td>
                    <td style={{ padding: '6px', fontSize: '0.75rem', color: r.consent_id ? '#38bdf8' : '#64748b' }}>
                      {r.consent_id || 'None'}
                    </td>
                    <td style={{ padding: '6px' }}>
                      <span style={{
                        padding: '2px 6px',
                        borderRadius: '8px',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        backgroundColor: r.access_result === 'ALLOWED' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: r.access_result === 'ALLOWED' ? '#34d399' : '#f87171',
                      }}>
                        {r.access_result}
                      </span>
                    </td>
                    <td style={{ padding: '6px', color: '#cbd5e1' }}>{r.reason}</td>
                    <td style={{ padding: '6px', color: '#64748b', fontSize: '0.75rem' }}>{new Date(r.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
