import { NavLink } from "react-router-dom";
import { useAppSelector } from "../../app/hooks";
import { canManageData, isAdmin } from "../../utils/permissions";

/* ── Inline SVG icons (no external dependency) ─────────────────────────── */
const Icon = ({ d, size = 16 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} />
  </svg>
);

const icons = {
  dashboard: "M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z M9 22V12h6v10",
  production: "M2 20h20M6 20V10M12 20V4M18 20v-6",
  suppliers:  "M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2 M23 21v-2a4 4 0 00-3-3.87 M16 3.13a4 4 0 010 7.75",
  inventory:  "M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z",
  analytics:  "M18 20V10 M12 20V4 M6 20v-6",
  reports:    "M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
  users:      "M12 11a4 4 0 100-8 4 4 0 000 8z M4 21v-1a6 6 0 016-6h4a6 6 0 016 6v1",
};

const NavItem = ({ to, iconKey, label, onClick }) => (
  <NavLink
    to={to}
    onClick={onClick}
    className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
  >
    <Icon d={icons[iconKey]} />
    <span>{label}</span>
  </NavLink>
);

export default function Sidebar({ open, onClose }) {
  const { user } = useAppSelector((state) => state.auth);

  return (
    <>
      {/* Mobile backdrop */}
      <div
        className={`sidebar-overlay${open ? " open" : ""}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside id="app-sidebar" className={`sidebar${open ? " open" : ""}`} aria-label="Main navigation">
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">M</div>
          <div className="sidebar-brand-text">
            <h3>Matna</h3>
            <span>Visibility Platform</span>
          </div>
        </div>

        {/* Main navigation */}
        <div className="sidebar-section">
          <p className="sidebar-section-label">Overview</p>
          <nav className="sidebar-nav">
            <NavItem to="/dashboard" iconKey="dashboard" label="Dashboard" onClick={onClose} />
          </nav>
        </div>

        {canManageData(user) && (
          <div className="sidebar-section">
            <p className="sidebar-section-label">Operations</p>
            <nav className="sidebar-nav">
              <NavItem to="/production" iconKey="production" label="Production"  onClick={onClose} />
              <NavItem to="/suppliers"  iconKey="suppliers"  label="Suppliers"   onClick={onClose} />
            </nav>
          </div>
        )}

        <div className="sidebar-section">
          <p className="sidebar-section-label">Intelligence</p>
          <nav className="sidebar-nav">
            <NavItem to="/inventory" iconKey="inventory" label="Inventory" onClick={onClose} />
            <NavItem to="/analytics" iconKey="analytics" label="Analytics" onClick={onClose} />
            <NavItem to="/reports"   iconKey="reports"   label="Reports"   onClick={onClose} />
          </nav>
        </div>

        {isAdmin(user) && (
          <div className="sidebar-section">
            <p className="sidebar-section-label">Administration</p>
            <nav className="sidebar-nav">
              <NavItem to="/users" iconKey="users" label="Users & access" onClick={onClose} />
            </nav>
          </div>
        )}
      </aside>
    </>
  );
}
