const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // Keep default text
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  async getSummary() {
    const res = await fetch(`${API_BASE_URL}/analytics/summary`);
    return handleResponse(res);
  },

  async getConsents(userId = null, status = null) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (status) params.append('status', status);
    const url = `${API_BASE_URL}/consents${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  async getConsentById(consentId) {
    const res = await fetch(`${API_BASE_URL}/consents/${consentId}`);
    return handleResponse(res);
  },

  async createConsent(data) {
    const res = await fetch(`${API_BASE_URL}/consents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async approveConsent(consentId) {
    const res = await fetch(`${API_BASE_URL}/consents/${consentId}/approve`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async denyConsent(consentId) {
    const res = await fetch(`${API_BASE_URL}/consents/${consentId}/deny`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async revokeConsent(consentId) {
    const res = await fetch(`${API_BASE_URL}/consents/${consentId}/revoke`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async getConsentAudit(consentId) {
    const res = await fetch(`${API_BASE_URL}/consents/${consentId}/audit`);
    return handleResponse(res);
  },

  async checkGateAccess(data) {
    const res = await fetch(`${API_BASE_URL}/consent-gate/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async getAuditLogs(userId = null, consentId = null, limit = 100) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (consentId) params.append('consent_id', consentId);
    if (limit) params.append('limit', limit);
    const url = `${API_BASE_URL}/audit-logs${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  // Module 2: Training Pipeline & Lineage
  async seedDataset(datasetName = 'transaction_fraud_dataset', forceReseed = false) {
    const params = new URLSearchParams();
    if (datasetName) params.append('dataset_name', datasetName);
    if (forceReseed) params.append('force_reseed', 'true');
    const res = await fetch(`${API_BASE_URL}/training/datasets/seed?${params.toString()}`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async getDatasets() {
    const res = await fetch(`${API_BASE_URL}/training/datasets`);
    return handleResponse(res);
  },

  async previewDataset(datasetName = 'transaction_fraud_dataset', limit = 50) {
    const res = await fetch(`${API_BASE_URL}/training/datasets/${datasetName}/preview?limit=${limit}`);
    return handleResponse(res);
  },

  async createTrainingBatch(data) {
    const res = await fetch(`${API_BASE_URL}/training/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async getTrainingBatches(limit = 100) {
    const res = await fetch(`${API_BASE_URL}/training/batches?limit=${limit}`);
    return handleResponse(res);
  },

  async getTrainingBatch(batchId) {
    const res = await fetch(`${API_BASE_URL}/training/batches/${batchId}`);
    return handleResponse(res);
  },

  async getBatchLineage(batchId) {
    const res = await fetch(`${API_BASE_URL}/training/batches/${batchId}/lineage`);
    return handleResponse(res);
  },

  getBatchDatasetUrl(batchId) {
    return `${API_BASE_URL}/training/batches/${batchId}/dataset`;
  },
};
