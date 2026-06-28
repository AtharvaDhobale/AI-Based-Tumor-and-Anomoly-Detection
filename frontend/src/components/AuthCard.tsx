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
    <div className="auth-card animate-in">
      <div className="auth-card-header">
        <div className="auth-card-logo">🏥</div>
        <div className="auth-card-title">NeuraScan MD</div>
        <div className="auth-card-sub">AI-powered clinical imaging system</div>
      </div>

      <div className="auth-card-body">
        {token ? (
          <>
            <div className="auth-user-block">
              <div className="auth-avatar">Dr</div>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)" }}>
                  Authenticated
                </div>
                <div className="text-muted mt-2" style={{ marginTop: 2 }}>
                  Session active
                </div>
              </div>
              <div className="flex-center gap-2" style={{ marginLeft: "auto" }}>
                <span className="dot dot-green pulse"></span>
                <span className="badge badge-green">Online</span>
              </div>
            </div>
            <button className="btn btn-danger btn-full" onClick={() => onToken(null)}>
              <span>⎋</span> Sign Out
            </button>
          </>
        ) : (
          <>
            <div className="auth-tabs">
              <button
                className={`auth-tab ${mode === "login" ? "active" : ""}`}
                onClick={() => { setMode("login"); setError(null); }}
              >
                Sign In
              </button>
              <button
                className={`auth-tab ${mode === "register" ? "active" : ""}`}
                onClick={() => { setMode("register"); setError(null); }}
              >
                Register
              </button>
            </div>

            <form onSubmit={submit}>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  id="auth-email"
                  className="form-input"
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
                  <label className="form-label">Full Name</label>
                  <input
                    id="auth-name"
                    className="form-input"
                    type="text"
                    placeholder="Dr. Jane Smith"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    required
                  />
                </div>
              )}

              <div className="form-group">
                <label className="form-label">Password</label>
                <input
                  id="auth-password"
                  className="form-input"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
              </div>

              {error && (
                <div className="alert alert-red mb-4">
                  <span>⚠</span>
                  <span>{error}</span>
                </div>
              )}

              <button id="auth-submit" className="btn btn-primary btn-full" disabled={loading}>
                {loading ? (
                  <><span className="spinner spinner-sm"></span> Processing...</>
                ) : mode === "login" ? (
                  <><span>→</span> Sign In</>
                ) : (
                  <><span>✓</span> Create Account</>
                )}
              </button>
            </form>

            <div className="divider"></div>
            <p className="text-muted" style={{ textAlign: "center", fontSize: 12 }}>
              Demo: Register with any email, then upload a brain MRI PNG/JPG to run AI analysis.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
