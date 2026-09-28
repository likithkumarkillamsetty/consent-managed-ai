import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import ConsentList from './components/ConsentList';
import CreateConsent from './components/CreateConsent';
import ConsentGateTest from './components/ConsentGateTest';
import TrainingPipeline from './components/TrainingPipeline';
import AuditLogs from './components/AuditLogs';
import ConsentDetailsModal from './components/ConsentDetailsModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedConsentId, setSelectedConsentId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const triggerRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  const handleSelectConsent = (id) => {
    setSelectedConsentId(id);
  };

  const handleConsentCreated = (newConsent) => {
    triggerRefresh();
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="container" style={{ flex: 1, paddingBottom: '3rem' }}>
        {activeTab === 'dashboard' && (
          <Dashboard
            key={refreshKey}
            setActiveTab={setActiveTab}
            onSelectConsent={handleSelectConsent}
          />
        )}

        {activeTab === 'consents' && (
          <ConsentList
            key={refreshKey}
            onSelectConsent={handleSelectConsent}
            onRefreshSummary={triggerRefresh}
          />
        )}

        {activeTab === 'create' && (
          <CreateConsent
            setActiveTab={setActiveTab}
            onConsentCreated={handleConsentCreated}
          />
        )}

        {activeTab === 'gate' && (
          <ConsentGateTest
            onAccessChecked={triggerRefresh}
          />
        )}

        {activeTab === 'training' && (
          <TrainingPipeline
            key={refreshKey}
          />
        )}

        {activeTab === 'audit' && (
          <AuditLogs
            key={refreshKey}
          />
        )}
      </main>

      {/* Consent Details Modal */}
      {selectedConsentId && (
        <ConsentDetailsModal
          consentId={selectedConsentId}
          onClose={() => setSelectedConsentId(null)}
          onRefresh={triggerRefresh}
        />
      )}

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #1e293b',
        backgroundColor: '#070b14',
        padding: '1.25rem 0',
        color: '#64748b',
        fontSize: '0.8rem',
        textAlign: 'center',
      }}>
        <div className="container">
          <p style={{ marginBottom: '0.25rem' }}>
            <strong>Consent-Managed Data Pipelines for Enterprise AI</strong> &bull; Module 1 & 2 (DEPA-Inspired)
          </p>
          <p style={{ color: '#475569', fontSize: '0.75rem' }}>
            This project implements a DEPA/Account-Aggregator-inspired consent management model and consent-gated ML training pipeline. It is not an official Account Aggregator implementation.
          </p>
        </div>
      </footer>
    </div>
  );
}

