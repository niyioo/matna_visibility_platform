import { NavLink } from "react-router-dom";
import { useAppSelector } from "../../app/hooks";
import { canManageData } from "../../utils/permissions";

export default function Sidebar() {
  const { user } = useAppSelector((state) => state.auth);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h3>Matna</h3>
        <span>Visibility Platform</span>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/dashboard">Dashboard</NavLink>

        {canManageData(user) && <NavLink to="/production">Production</NavLink>}
        {canManageData(user) && <NavLink to="/suppliers">Suppliers</NavLink>}

        <NavLink to="/inventory">Inventory</NavLink>
        <NavLink to="/analytics">Analytics</NavLink>
        <NavLink to="/reports">Reports</NavLink>
      </nav>
    </aside>
  );
}