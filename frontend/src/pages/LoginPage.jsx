import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(username, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Couldn't sign in. Check your username and password.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 380, paddingTop: 96 }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Sign in</h1>
      <p style={{ color: "var(--ink-soft)", fontSize: 14, marginBottom: 28 }}>
        Upload code, get back tests.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
        <button className="btn" type="submit" disabled={submitting} style={{ width: "100%" }}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 20 }}>
        No account? <Link to="/register">Create one</Link>
      </p>
    </div>
  );
}
