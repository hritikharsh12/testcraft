import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/login");
  }

  return (
    <header
      style={{
        borderBottom: "1px solid var(--line)",
        background: "var(--panel)",
      }}
    >
      <div
        className="container"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 56,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontWeight: 600,
            fontSize: 15,
            letterSpacing: "-0.02em",
          }}
        >
          testcraft
        </span>
        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>{user.username}</span>
            <button className="btn btn-secondary" onClick={handleSignOut}>
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
