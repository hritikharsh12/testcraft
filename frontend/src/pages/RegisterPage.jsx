import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/authClient";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(username, email, password);
      navigate("/login");
    } catch (err) {
      setError(err.message || "Couldn't create that account.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="container" style={{ maxWidth: 380, paddingTop: 96 }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Create account</h1>
      <p style={{ color: "var(--ink-soft)", fontSize: 14, marginBottom: 28 }}>
        Passwords need at least 10 characters.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input id="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
            minLength={10}
            required
          />
        </div>
        <button className="btn" type="submit" disabled={submitting} style={{ width: "100%" }}>
          {submitting ? "Creating…" : "Create account"}
        </button>
      </form>

      <p style={{ fontSize: 13, color: "var(--ink-soft)", marginTop: 20 }}>
        Already have one? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
