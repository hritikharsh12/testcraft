import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return null; // avoid a login-page flash while session restores
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
