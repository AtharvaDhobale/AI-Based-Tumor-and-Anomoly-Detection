import React from "react";
import AuthCard from "./components/AuthCard";
import UploadDetectCard from "./components/UploadDetectCard";

function loadToken(): string | null {
  try { return localStorage.getItem("token"); } catch { return null; }
}

export default function App() {
  const [token, setToken] = React.useState<string | null>(() => loadToken());
  const [activeTab, setActiveTab] = React.useState<"upload" | "dashboard" | "patients">("upload");

  function onToken(t: string | null) {
    setToken(t);
    try {
      if (t) localStorage.setItem("token", t);
      else localStorage.removeItem("token");
    } catch { /* ignore */ }
  }

  // EHR clinical dashboard mocked statistics
  const stats = [
    { icon: "👥", label: "Patient Records", val: "1,248", color: "primary" },
    { icon: "🔬", label: "Scans Analyzed",  val: "412",   color: "success" },
    { icon: "⏳", label: "Pending Sign-off", val: "7",     color: "warning" },
    { icon: "🚨", label: "Critical Alerts", val: "2",     color: "critical" }
  ];

  const recentTimeline = [
    { type: "success", text: "Patient ID P015 - Brain MRI scan analysis complete (Normal).", time: "10:30 AM" },
    { type: "warning", text: "Patient ID P012 - Hematology Lab Report parsed (biomarkers flagged).", time: "09:45 AM" },
    { type: "critical", text: "Patient ID P008 - Spine MRI anomaly detected (severe compression).", time: "09:15 AM" },
    { type: "info", text: "System - AI Model Classifier v1.0.4 loaded successfully.", time: "Yesterday" }
  ];

  const modelInventory = [
    { name: "Brain Tumor Segmenter (U-Net)", ver: "v1.0 (BraTS)", status: "normal" },
    { name: "MRI Classifier (ResNet18)", ver: "v1.0 (BraTS)", status: "normal" },
    { name: "Pelvis Cancer Screener", ver: "v0.9 (Calibrating)", status: "warning" },
    { name: "Spine Disc Analyzer", ver: "v0.8 (Alpha)", status: "warning" }
  ];

  const patientRegistry = [
    { mrn: "MRN-9201", name: "Sarah Connor", age: 34, sex: "Female", scan: "Brain MRI", result: "Normal", status: "success" },
    { mrn: "MRN-1823", name: "Bruce Wayne", age: 42, sex: "Male", scan: "Spine MRI", result: "Abnormal", status: "critical" },
    { mrn: "MRN-4890", name: "Clark Kent", age: 30, sex: "Male", scan: "Brain MRI", result: "Normal", status: "success" },
    { mrn: "MRN-0391", name: "Peter Parker", age: 22, sex: "Male", scan: "Lab Report", result: "Pending", status: "warning" },
    { mrn: "MRN-7734", name: "Selina Kyle", age: 29, sex: "Female", scan: "Breast MRI", result: "Normal", status: "success" }
  ];

  const getPill = (status: string, text: string) => {
    return (
      <span className={`pill-clinical ${status}`}>
        <span className="pulse-bullet"></span> {text}
      </span>
    );
  };

  return (
    <div className={token ? "app-container" : ""}>
      {/* ── Side Bar (Visible only when authenticated) ── */}
      {token && (
        <aside className="app-sidebar">
          <div className="sidebar-logo">
            <div className="logo-badge">🏥</div>
            <div>
              <div className="logo-text-title">NeuraScan MD</div>
              <div className="logo-text-sub">EHR Workstation</div>
            </div>
          </div>

          <ul className="sidebar-menu">
            {[
              { id: "upload", label: "Diagnostic Workspace", icon: "🛰️" },
              { id: "dashboard", label: "Clinical Analytics", icon: "◫" },
              { id: "patients", label: "Patient Registry", icon: "👥" }
            ].map(item => (
              <li key={item.id}>
                <button
                  id={`nav-tab-${item.id}`}
                  className={`menu-item-btn ${activeTab === item.id ? "active" : ""}`}
                  onClick={() => setActiveTab(item.id as typeof activeTab)}
                >
                  <span style={{ fontSize: 16 }}>{item.icon}</span>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>

          <div className="sidebar-user">
            <div className="user-avatar">Dr</div>
            <div style={{ flex: 1 }}>
              <div className="user-info-name">Dr. Atharva Dhobale</div>
              <div className="user-info-role">Hospital Physician</div>
            </div>
            <button
              className="btn-clinical ghost btn-sm"
              onClick={() => onToken(null)}
              title="Sign Out"
              style={{ padding: 4 }}
            >
              🚪
            </button>
          </div>
        </aside>
      )}

      {/* ── Main Workspace ── */}
      {token ? (
        <div className="app-workspace">
          {/* Header */}
          <header className="workspace-header">
            <div>
              <h1 className="header-title-main">
                {activeTab === "upload" && "Diagnostic Workspace"}
                {activeTab === "dashboard" && "Clinical Analytics Dashboard"}
                {activeTab === "patients" && "EHR Patient Registry"}
              </h1>
              <div className="header-title-sub">
                {activeTab === "upload" && "Run AI diagnostic inference & generate physician sign-off reports"}
                {activeTab === "dashboard" && "Hospital-wide patient stats, alert tracking & AI service telemetry"}
                {activeTab === "patients" && "Browse, search, and register patient medical histories"}
              </div>
            </div>

            <div className="header-controls">
              <span className="pill-clinical success">
                <span className="pulse-bullet"></span> PACS Server Online
              </span>
              <span className="text-muted text-xs">v1.0.4-release</span>
            </div>
          </header>

          {/* ── Tab: Workspace / Scan Analysis ── */}
          {activeTab === "upload" && (
            <UploadDetectCard token={token} />
          )}

          {/* ── Tab: Clinical Analytics ── */}
          {activeTab === "dashboard" && (
            <div className="clinic-fade-in-up">
              {/* Stats Bar */}
              <div className="stats-container">
                {stats.map(s => (
                  <div key={s.label} className="stat-metric-card">
                    <div>
                      <div className="stat-metric-value">{s.val}</div>
                      <div className="stat-metric-label">{s.label}</div>
                    </div>
                    <div className={`stat-metric-icon ${s.color}`}>{s.icon}</div>
                  </div>
                ))}
              </div>

              {/* Charts & Timeline Layout */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
                {/* AI Timeline Feed */}
                <div className="card-clinical">
                  <div className="card-clinical-header">
                    <h2 className="card-clinical-title"><span>📋</span> Realtime Clinical Activity Feed</h2>
                  </div>
                  <div className="card-clinical-body">
                    <div className="clinical-timeline">
                      {recentTimeline.map((item, idx) => (
                        <div key={idx} className="timeline-event-item">
                          <div className={`timeline-event-marker ${item.type}`}></div>
                          <div>
                            <div className="timeline-event-desc">{item.text}</div>
                            <div className="timeline-event-timestamp">{item.time}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* AI Service Inventory */}
                <div className="card-clinical">
                  <div className="card-clinical-header">
                    <h2 className="card-clinical-title"><span>🤖</span> AI Diagnostic Modality Telemetry</h2>
                  </div>
                  <div className="card-clinical-body no-padding">
                    <table className="clinical-registry-table">
                      <thead>
                        <tr>
                          <th>Model Modality</th>
                          <th>Engine Version</th>
                          <th>Telemetry Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelInventory.map(m => (
                          <tr key={m.name}>
                            <td style={{ fontWeight: 600 }}>{m.name}</td>
                            <td className="font-mono text-muted">{m.ver}</td>
                            <td>
                              {m.status === "normal"
                                ? getPill("success", "Active & Calibrated")
                                : getPill("warning", "In Calibration")
                              }
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Warning center */}
              <div className="card-clinical">
                <div className="card-clinical-header">
                  <h2 className="card-clinical-title"><span>🚨</span> Hospital Alert Warning Center</h2>
                </div>
                <div className="card-clinical-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div className="risk-notification-panel critical">
                    <div className="risk-panel-icon">🔴</div>
                    <div>
                      <div className="risk-panel-title">Critical Diagnostic Escalations</div>
                      <div className="risk-panel-desc">2 patients (Bruce Wayne, Clark Kent) present severe MRI anomalies. Specialist review is required immediately.</div>
                    </div>
                  </div>
                  <div className="risk-notification-panel warning">
                    <div className="risk-panel-icon">🟡</div>
                    <div>
                      <div className="risk-panel-title">Pending Radiologist Verification</div>
                      <div className="risk-panel-desc">5 scans are fully analyzed by the AI pipeline and waiting for radiologist approval.</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Tab: Patient Registry ── */}
          {activeTab === "patients" && (
            <div className="card-clinical clinic-fade-in-up">
              <div className="card-clinical-header">
                <h2 className="card-clinical-title"><span>👥</span> EHR Patient Registry Search</h2>
                <button className="btn-clinical primary btn-sm">+ Add New Record</button>
              </div>
              <div className="card-clinical-body no-padding">
                <table className="clinical-registry-table">
                  <thead>
                    <tr>
                      <th>Patient MRN</th>
                      <th>Patient Name</th>
                      <th>Age / Sex</th>
                      <th>Active Scan</th>
                      <th>Inference Result</th>
                      <th>EHR Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patientRegistry.map(p => (
                      <tr key={p.mrn}>
                        <td className="font-mono" style={{ fontWeight: 600 }}>{p.mrn}</td>
                        <td style={{ fontWeight: 600 }}>{p.name}</td>
                        <td className="text-secondary">{p.age} Y / {p.sex}</td>
                        <td>{p.scan}</td>
                        <td>{p.result}</td>
                        <td>
                          {p.status === "success" && getPill("success", "Archived")}
                          {p.status === "critical" && getPill("critical", "Flagged")}
                          {p.status === "warning" && getPill("warning", "Reviewing")}
                        </td>
                        <td>
                          <button className="btn-clinical ghost btn-sm">Open File →</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <AuthCard token={token} onToken={onToken} />
      )}
    </div>
  );
}
