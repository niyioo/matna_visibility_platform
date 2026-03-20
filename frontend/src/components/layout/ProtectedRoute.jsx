import { Navigate } from "react-router-dom";
import { useAppSelector } from "../../app/hooks";

export default function ProtectedRoute({ children }) {
  const { user } = useAppSelector((state) => state.auth);

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}