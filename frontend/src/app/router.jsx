import { lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import AppLayout from "../components/layout/AppLayout";
import NotFoundPage from "../components/layout/NotFoundPage";
import ProtectedRoute from "../components/layout/ProtectedRoute";
import RequireRole from "../components/layout/RequireRole";
import LoginPage from "../features/auth/LoginPage";
import { DATA_ENTRY_ROLES, ROLES } from "../utils/permissions";

// Pages are split into separate chunks; chart-heavy pages (Recharts) only
// download when first visited.
const DashboardPage = lazy(() => import("../features/dashboard/DashboardPage"));
const ProductionPage = lazy(() => import("../features/production/ProductionPage"));
const SuppliersPage = lazy(() => import("../features/suppliers/SuppliersPage"));
const InventoryPage = lazy(() => import("../features/inventory/InventoryPage"));
const AnalyticsPage = lazy(() => import("../features/analytics/AnalyticsPage"));
const ReportsPage = lazy(() => import("../features/reports/ReportsPage"));
const UsersPage = lazy(() => import("../features/users/UsersPage"));

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "production",
        element: <RequireRole allow={DATA_ENTRY_ROLES}><ProductionPage /></RequireRole>,
      },
      {
        path: "suppliers",
        element: <RequireRole allow={DATA_ENTRY_ROLES}><SuppliersPage /></RequireRole>,
      },
      { path: "inventory", element: <InventoryPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
      { path: "reports", element: <ReportsPage /> },
      {
        path: "users",
        element: <RequireRole allow={[ROLES.ADMIN]}><UsersPage /></RequireRole>,
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
