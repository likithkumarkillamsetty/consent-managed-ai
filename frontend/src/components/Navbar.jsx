import React from 'react';
import { ShieldCheck, LayoutDashboard, FileText, PlusCircle, Key, History, Cpu } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'consents', label: 'Consent Requests', icon: FileText },
    { id: 'create', label: 'Create Consent', icon: PlusCircle },
    { id: 'gate', label: 'Consent Gate Test', icon: Key },
    { id: 'training', label: 'ML Training & Lineage', icon: Cpu },
    { id: 'audit', label: 'Audit Logs', icon: History },
  ];

  return (
    <header style={{
      backgroundColor: '#0b1120',
      borderBottom: '1px solid #1e293b',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      backdropFilter: 'blur(12px)',
    }}>
      <div className="container" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingTop: '0.85rem',
        paddingBottom: '0.85rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #3b82f6 100%)',
            padding: '0.5rem',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(2, 132, 199, 0.4)',
          }}>
            <ShieldCheck size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontWeight: 700, fontSize: '1.1rem', letterSpacing: '-0.02em', color: '#f8fafc' }}>
                Consent-Managed AI
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 600,
                padding: '0.15rem 0.5rem',
                borderRadius: '9999px',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}>
                DEPA-Inspired
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
              Consent Governance & Gated ML Training Pipeline with Lineage Tracking
            </div>
          </div>
        </div>


        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                onClick={() => setActiveTab(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.9rem',
                  borderRadius: '8px',
                  fontSize: '0.85rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  border: isActive ? '1px solid #38bdf8' : '1px solid transparent',
                  backgroundColor: isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  transition: 'all 0.2s ease',
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
