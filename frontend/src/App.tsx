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

  const stats = [
    { icon: "👥", label: "Total Patients",   val: "156", color: "blue"   },
    { icon: "🔬", label: "Analyzed Today",   val: "12",  color: "green"  },
    { icon: "⏳", label: "Pending Review",   val: "5",   color: "yellow" },
    { icon: "🚨", label: "Critical Cases",   val: "2",   color: "red"    },
  ];

  const activity = [
    { color: "green",  text: "P015 — Brain MRI analyzed. Result: Normal.", time: "10:30 AM" },
    { color: "yellow", text: "P012 — Lab report uploaded, extraction pending.", time: "09:45 AM" },
    { color: "red",    text: "P008 — Spine MRI flagged. Expert review needed.", time: "09:15 AM" },
    { color: "blue",   text: "P003 — Follow-up imaging scheduled.", time: "Yesterday" },
    { color: "green",  text: "P011 — Breast MRI: No anomaly detected.", time: "Yesterday" },
  ];

  const models = [
    { name: "Brain Tumor Segmenter",   version: "v1.0  (BraTS)",  status: "ok"      },
    { name: "MRI Classifier (ResNet18)", version: "v1.0  (BraTS)", status: "ok"      },
    { name: "Pelvis Cancer Detector",  version: "v0.8",            status: "warning" },
    { name: "Breast MRI Screener",     version: "v0.9",            status: "ok"      },
  ];

  const patients = [
    { id: "P015", date: "Today 10:30", modality: "Brain MRI",  result: "Normal",   status: "ok" },
    { id: "P012", date: "Today 09:45", modality: "Lab Report", result: "Pending",  status: "warning" },
    { id: "P008", date: "Today 09:15", modality: "Spine MRI",  result: "Abnormal", status: "red" },
    { id: "P003", date: "Yesterday",   modality: "Breast MRI", result: "Follow-up",status: "blue" },
    { id: "P001", date: "Jun 26",      modality: "Brain MRI",  result: "Normal",   status: "ok" },
  ];

  const badgeForStatus = (s: string) => {
    if (s === "ok")      return <span className="badge badge-green">Completed</span>;
    if (s === "warning") return <span className="badge badge-yellow">Processing</span>;
    if (s === "red")     return <span className="badge badge-red">Critical</span>;
    if (s === "blue")    return <span className="badge badge-blue">Scheduled</span>;
    return <span className="badge badge-muted">{s}</span>;
  };

  return (
    <div className="app-shell">
      {/* ── Top Navigation ── */}
      <nav className="topnav">
        <div className="topnav-brand">
          <div className="topnav-logo">🧠</div>
          <div>
            <div className="topnav-title">NeuraScan MD</div>
            <div className="topnav-subtitle">AI Clinical Imaging</div>
          </div>
        </div>

        {token && (
          <div className="topnav-center">
            {[
              { key: "upload",    label: "Upload & Analysis", icon: "⬆" },
              { key: "dashboard", label: "Dashboard",         icon: "◫" },
              { key: "patients",  label: "Patients",          icon: "👤" },
            ].map(({ key, label, icon }) => (
              <button
                key={key}
                id={`tab-${key}`}
                className={`topnav-tab ${activeTab === key ? "active" : ""}`}
                onClick={() => setActiveTab(key as typeof activeTab)}
              >
                <span>{icon}</span> {label}
              </button>
            ))}
          </div>
        )}

        <div className="topnav-right">
          {token ? (
            <>
              <span className="flex-center gap-2">
                <span className="dot dot-green pulse"></span>
                <span className="text-muted text-sm">System Online</span>
              </span>
              <span className="badge badge-green">Authenticated</span>
            </>
          ) : (
            <span className="badge badge-yellow">Not Signed In</span>
          )}
        </div>
      </nav>

      {/* ── Page Content ── */}
      <main className="page-content">

        {/* Stat banner (logged in only) */}
        {token && (
          <div className="stat-banner">
            {stats.map((s) => (
              <div className="stat-card animate-in" key={s.label}>
                <div className={`stat-icon ${s.color}`}>{s.icon}</div>
                <div>
                  <div className={`stat-val ${s.color}`}>{s.val}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── UPLOAD TAB ── */}
        {(!token || activeTab === "upload") && (
          <div className="main-grid">
            <AuthCard token={token} onToken={onToken} />
            {token ? (
              <UploadDetectCard token={token} />
            ) : (
              <div className="card animate-in">
                <div className="card-header">
                  <div className="card-title">
                    <div className="card-title-icon">🔒</div>
                    Clinical Analysis
                  </div>
                </div>
                <div className="card-body">
                  <div className="loading-box">
                    <div style={{ fontSize: 48 }}>🏥</div>
                    <div style={{ fontWeight: 600, fontSize: 16, color: "var(--text-primary)" }}>
                      Sign in to access the system
                    </div>
                    <div className="text-muted" style={{ textAlign: "center", maxWidth: 300 }}>
                      Upload MRI scans, run AI detection, and generate clinical reports.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── DASHBOARD TAB ── */}
        {token && activeTab === "dashboard" && (
          <div className="dash-grid animate-in">

            {/* Recent Activity */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <div className="card-title-icon">📋</div>
                  Recent Activity
                </div>
              </div>
              <div className="card-body">
                <div className="activity-feed">
                  {activity.map((a, i) => (
                    <div className="activity-item" key={i}>
                      <div className={`activity-dot dot-${a.color}`}></div>
                      <div className="activity-content">
                        <div className="activity-text">{a.text}</div>
                        <div className="activity-time">{a.time}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <div className="card-title-icon">⚡</div>
                  Quick Actions
                </div>
              </div>
              <div className="card-body">
                <div className="quick-actions">
                  {[
                    { icon: "🔍", label: "Search Patient", bg: "blue-bg" },
                    { icon: "📄", label: "Generate Report", bg: "blue-bg" },
                    { icon: "📅", label: "View Schedule", bg: "blue-bg" },
                    { icon: "⚙", label: "Model Settings", bg: "blue-bg" },
                    { icon: "📊", label: "Analytics", bg: "blue-bg" },
                    { icon: "🔔", label: "Alerts (2)", bg: "blue-bg" },
                  ].map((a) => (
                    <button key={a.label} className="quick-action-btn">
                      <div className="quick-action-icon">{a.icon}</div>
                      {a.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* AI Model Status */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <div className="card-title-icon">🤖</div>
                  AI Model Status
                </div>
              </div>
              <div className="card-body">
                {models.map((m) => (
                  <div className="model-status-item" key={m.name}>
                    <div>
                      <div className="model-name">{m.name}</div>
                      <div className="model-version">{m.version}</div>
                    </div>
                    {m.status === "ok" ? (
                      <span className="badge badge-green">
                        <span className="dot dot-green"></span> Trained
                      </span>
                    ) : (
                      <span className="badge badge-yellow">
                        <span className="dot dot-yellow"></span> Calibrating
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Alerts */}
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <div className="card-title-icon">🚨</div>
                  Clinical Alerts
                </div>
              </div>
              <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div className="alert alert-red">
                  <span>🔴</span>
                  <span>2 critical cases require <strong>immediate</strong> specialist review.</span>
                </div>
                <div className="alert alert-yellow">
                  <span>🟡</span>
                  <span>5 results pending expert radiologist sign-off.</span>
                </div>
                <div className="alert alert-blue">
                  <span>ℹ</span>
                  <span>Model update available — Segmenter v1.1 ready to deploy.</span>
                </div>
                <div className="alert alert-green">
                  <span>✓</span>
                  <span>System health: All services running normally.</span>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* ── PATIENTS TAB ── */}
        {token && activeTab === "patients" && (
          <div className="card animate-in">
            <div className="card-header" style={{ paddingBottom: 16 }}>
              <div className="card-title">
                <div className="card-title-icon">👥</div>
                Patient Registry
              </div>
              <button className="btn btn-primary btn-sm">+ New Patient</button>
            </div>
            <div className="card-body flush">
              <table className="patient-table">
                <thead>
                  <tr>
                    <th>Patient ID</th>
                    <th>Last Scan</th>
                    <th>Modality</th>
                    <th>AI Result</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {patients.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <span style={{ fontWeight: 600, fontFamily: "JetBrains Mono, monospace" }}>{p.id}</span>
                      </td>
                      <td className="text-muted">{p.date}</td>
                      <td>{p.modality}</td>
                      <td style={{ fontWeight: 500 }}>{p.result}</td>
                      <td>{badgeForStatus(p.status)}</td>
                      <td>
                        <button className="btn btn-ghost btn-sm">View →</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer style={{
        borderTop: "1px solid var(--border)",
        padding: "14px 28px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: 12,
        color: "var(--text-muted)"
      }}>
        <span>NeuraScan MD — AI Clinical Imaging System</span>
        <span style={{ display: "flex", gap: 16 }}>
          <span>Backend: localhost:8000</span>
          <span>AI Model: v1.0 (BraTS)</span>
          <span className="badge badge-green" style={{ fontSize: 11 }}>
            <span className="dot dot-green"></span> System Online
          </span>
        </span>
      </footer>
    </div>
  );
}
