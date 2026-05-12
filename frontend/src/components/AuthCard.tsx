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
    <div className="card">
      <h2>Medical Professional Access</h2>
      {token ? (
        <>
          <div className="pill ok">Authenticated</div>
          <div style={{ height: 10 }} />
          <button onClick={() => onToken(null)}>Log out</button>
        </>
      ) : (
        <>
          <div className="segmented">
            <button
              onClick={() => setMode("login")}
              aria-pressed={mode === "login"}
            >
              Login
            </button>
            <button
              onClick={() => setMode("register")}
              aria-pressed={mode === "register"}
            >
              Register
            </button>
          </div>

          <form onSubmit={submit}>
            <div className="field">
              <label>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>

            {mode === "register" && (
              <div className="field">
                <label>Full name</label>
                <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
              </div>
            )}

            <div className="field">
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>

            {error && <div className="muted" style={{ color: "var(--danger)" }}>{error}</div>}
            <div style={{ height: 10 }} />
            <button className="primary" disabled={loading}>
              {loading ? "Please wait..." : mode === "login" ? "Login" : "Create account"}
            </button>
          </form>

          <div style={{ height: 10 }} />
          <div className="muted">
            Tip: For local demo, you can register any email, then upload a PNG/JPG MRI slice.
          </div>
        </>
      )}
    </div>
  );
}

