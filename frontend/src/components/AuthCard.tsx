import React from "react";
import { apiLogin, apiRegister } from "../lib/api";

type Props = {
  token: string | null;
  onToken: (t: string | null) => void;
};

export default function AuthCard({ token, onToken }: Props) {
  const [mode, setMode] = React.useState<"login" | "register">("login");
  const [email, setEmail] = React.useState("");
  const [fullName, setFullName] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp =
        mode === "login"
          ? await apiLogin(email, password)
          : await apiRegister(email, fullName, password);
      onToken(resp.access_token);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ehr-portal-centered clinic-fade-in-up">
      <div className="ehr-portal-card">
        <div className="ehr-portal-header">
          <div className="ehr-portal-logo">🏥</div>
          <div className="ehr-portal-title">NeuraScan MD Portal</div>
          <div className="ehr-portal-sub">Secure Hospital Authentication</div>
        </div>

        <div className="ehr-portal-body">
          {token ? (
            <div className="grid-gap-20">
              <div className="flex-center gap-3" style={{ padding: "12px 16px", backgroundColor: "var(--bg-accent)", borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                <div className="user-avatar">DR</div>
                <div style={{ flex: 1 }}>
                  <div className="user-info-name">Clinical Session Active</div>
                  <div className="user-info-role">Hospital Physician Access</div>
                </div>
                <span className="pill-clinical success">
                  <span className="pulse-bullet"></span> Active
                </span>
              </div>
              <button id="auth-logout-btn" className="btn-clinical danger" style={{ width: "100%" }} onClick={() => onToken(null)}>
                Sign Out / Disconnect Session
              </button>
            </div>
          ) : (
            <>
              <div className="auth-tabs">
                <button
                  id="tab-mode-login"
                  className={`auth-tab ${mode === "login" ? "active" : ""}`}
                  onClick={() => { setMode("login"); setError(null); }}
                >
                  Clinical Sign In
                </button>
                <button
                  id="tab-mode-register"
                  className={`auth-tab ${mode === "register" ? "active" : ""}`}
                  onClick={() => { setMode("register"); setError(null); }}
                >
                  Register Account
                </button>
              </div>

              <form onSubmit={submit} className="grid-gap-20">
                <div className="form-group">
                  <label className="form-label">Hospital Email Address</label>
                  <input
                    id="auth-email"
                    className="form-input-field"
                    type="email"
                    placeholder="doctor@hospital.org"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>

                {mode === "register" && (
                  <div className="form-group">
                    <label className="form-label">Full Name & Credentials</label>
                    <input
                      id="auth-name"
                      className="form-input-field"
                      type="text"
                      placeholder="Dr. Jane Smith, MD"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      required
                    />
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Secure Access Key (Password)</label>
                  <input
                    id="auth-password"
                    className="form-input-field"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                  />
                </div>

                {error && (
                  <div className="alert alert-red" style={{ margin: "4px 0" }}>
                    <span>⚠</span>
                    <span>{error}</span>
                  </div>
                )}

                <button id="auth-submit-btn" className="btn-clinical primary" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
                  {loading ? (
                    <><span className="clinical-spinner" style={{ width: 14, height: 14, borderWidth: 2, marginRight: 8 }}></span> Verifying...</>
                  ) : mode === "login" ? (
                    "Authorize Credentials"
                  ) : (
                    "Complete Registration"
                  )}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
