import React from "react";
import AuthCard from "./components/AuthCard";
import UploadDetectCard from "./components/UploadDetectCard";

function loadToken(): string | null {
  try {
    return localStorage.getItem("token");
  } catch {
    return null;
  }
}

export default function App() {
  const [token, setToken] = React.useState<string | null>(() => loadToken());
  const [activeTab, setActiveTab] = React.useState<"upload" | "dashboard" | "patients">("upload");

  function onToken(t: string | null) {
    setToken(t);
    try {
      if (t) localStorage.setItem("token", t);
      else localStorage.removeItem("token");
    } catch {
      // ignore
    }
  }

  // Mock statistics for dashboard
  const stats = {
    totalPatients: 156,
    analyzedToday: 12,
    pendingReview: 5,
    criticalCases: 2
  };

  return (
    <div className="container">
      <div className="topbar">
        <div>
          <div className="title">🏥 MRI AI Tumor & Anomaly Detection</div>
          <div className="subtitle">Doctor dashboard for MRI + lab report decision-support</div>
        </div>
        <div className="row">
          <div className="pill">Backend: /api</div>
          <div className={`pill ${token ? "ok" : ""}`}>{token ? "Session active" : "Please login"}</div>
        </div>
      </div>

      {/* Quick Stats Bar */}
      {token && (
        <div className="statsBar">
          <div className="statItem">
            <div className="statValue">{stats.totalPatients}</div>
            <div className="statLabel">Total Patients</div>
          </div>
          <div className="statItem">
            <div className="statValue highlight">{stats.analyzedToday}</div>
            <div className="statLabel">Analyzed Today</div>
          </div>
          <div className="statItem">
            <div className="statValue warning">{stats.pendingReview}</div>
            <div className="statLabel">Pending Review</div>
          </div>
          <div className="statItem">
            <div className="statValue danger">{stats.criticalCases}</div>
            <div className="statLabel">Critical Cases</div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      {token && (
        <div className="navTabs">
          <button 
            className={`tabButton ${activeTab === "upload" ? "active" : ""}`}
            onClick={() => setActiveTab("upload")}
          >
            📤 Upload & Analysis
          </button>
          <button 
            className={`tabButton ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            📊 Dashboard
          </button>
          <button 
            className={`tabButton ${activeTab === "patients" ? "active" : ""}`}
            onClick={() => setActiveTab("patients")}
          >
            👥 Patients
          </button>
        </div>
      )}

      <div className="grid">
        <AuthCard token={token} onToken={onToken} />
        {token ? (
          activeTab === "upload" ? (
            <UploadDetectCard token={token} />
          ) : activeTab === "dashboard" ? (
            <div className="card mainCard">
              <h2>📊 Doctor Overview Dashboard</h2>
              <div className="dashboardGrid">
                <div className="dashboardCard">
                  <h3>Recent Activity</h3>
                  <div className="activityList">
                    <div className="activityItem">
                      <span className="activityTime">10:30 AM</span>
                      <span className="activityText">Patient P015 Brain MRI analyzed - Normal</span>
                    </div>
                    <div className="activityItem">
                      <span className="activityTime">09:45 AM</span>
                      <span className="activityText">Patient P012 Lab report uploaded</span>
                    </div>
                    <div className="activityItem">
                      <span className="activityTime">09:15 AM</span>
                      <span className="activityText">Patient P008 Spine MRI - Critical review needed</span>
                    </div>
                    <div className="activityItem">
                      <span className="activityTime">Yesterday</span>
                      <span className="activityText">Patient P003 Breast MRI - Follow-up scheduled</span>
                    </div>
                  </div>
                </div>
                <div className="dashboardCard">
                  <h3>Quick Actions</h3>
                  <div className="quickActions">
                    <button className="actionButton">🔍 Search Patient</button>
                    <button className="actionButton">📋 Generate Report</button>
                    <button className="actionButton">📅 View Schedule</button>
                    <button className="actionButton">⚙️ Model Settings</button>
                  </div>
                </div>
                <div className="dashboardCard">
                  <h3>AI Model Status</h3>
                  <div className="modelStatus">
                    <div className="statusRow">
                      <span>Brain MRI Classifier</span>
                      <span className="statusBadge ok">✅ Trained</span>
                    </div>
                    <div className="statusRow">
                      <span>Spine Segmentation</span>
                      <span className="statusBadge ok">✅ Trained</span>
                    </div>
                    <div className="statusRow">
                      <span>Pelvis Classifier</span>
                      <span className="statusBadge warning">⚠️ Calibrating</span>
                    </div>
                    <div className="statusRow">
                      <span>Breast Cancer Detector</span>
                      <span className="statusBadge ok">✅ Trained</span>
                    </div>
                  </div>
                </div>
                <div className="dashboardCard">
                  <h3>Alerts & Notifications</h3>
                  <div className="alertsList">
                    <div className="alertItem critical">
                      <span>🔴</span> 2 critical cases require immediate attention
                    </div>
                    <div className="alertItem warning">
                      <span>🟡</span> 5 results pending expert review
                    </div>
                    <div className="alertItem info">
                      <span>🔵</span> Model update available v2.1.0
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="card mainCard">
              <h2>👥 Patient Management</h2>
              <div className="patientTable">
                <div className="tableHeader">
                  <span>Patient ID</span>
                  <span>Last Scan</span>
                  <span>Modality</span>
                  <span>Result</span>
                  <span>Status</span>
                </div>
                <div className="tableRow">
                  <span>P015</span>
                  <span>Today 10:30</span>
                  <span>Brain MRI</span>
                  <span>Normal</span>
                  <span className="statusTag ok">Completed</span>
                </div>
                <div className="tableRow">
                  <span>P012</span>
                  <span>Today 09:45</span>
                  <span>Lab Report</span>
                  <span>Pending</span>
                  <span className="statusTag warning">Processing</span>
                </div>
                <div className="tableRow">
                  <span>P008</span>
                  <span>Today 09:15</span>
                  <span>Spine MRI</span>
                  <span>Abnormal</span>
                  <span className="statusTag critical">Critical</span>
                </div>
                <div className="tableRow">
                  <span>P003</span>
                  <span>Yesterday</span>
                  <span>Breast MRI</span>
                  <span>Follow-up</span>
                  <span className="statusTag info">Scheduled</span>
                </div>
              </div>
            </div>
          )
        ) : (
          <div className="card">
            <h2>Upload & Results</h2>
            <div className="muted">Please login to upload MRI images and run AI detection.</div>
          </div>
        )}
      </div>
    </div>
  );
}

