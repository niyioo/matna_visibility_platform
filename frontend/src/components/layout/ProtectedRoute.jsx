import { Navigate, useLocation } from "react-router-dom";
import { useAppSelector } from "../../app/hooks";
import Loader from "../common/Loader";

/**
 * Guards authenticated routes. While a stored session is being re-validated
 * on boot, shows a loader instead of flashing the login page.
 */
export default function ProtectedRoute({ children }) {
  const { user, initializing } = useAppSelector((state) => state.auth);
  const location = useLocation();

  if (initializing && !user) {
    return (
      <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
        <Loader text="Restoring session…" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return children;
}
