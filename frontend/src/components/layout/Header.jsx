import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { logout } from "../../features/auth/authSlice";

export default function Header() {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);

  return (
    <header className="topbar">
      <div>
        <h2>Operations Dashboard</h2>
        <p>Welcome, {user?.first_name || user?.username}</p>
      </div>

      <button className="btn btn-secondary" onClick={() => dispatch(logout())}>
        Logout
      </button>
    </header>
  );
}