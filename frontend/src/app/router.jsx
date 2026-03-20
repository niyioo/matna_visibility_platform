import { createBrowserRouter, Navigate } from "react-router-dom";
import LoginPage from "../features/auth/LoginPage";
import DashboardPage from "../features/dashboard/DashboardPage";
import ProductionPage from "../features/production/ProductionPage";
import SuppliersPage from "../features/suppliers/SuppliersPage";
import InventoryPage from "../features/inventory/InventoryPage";
import AnalyticsPage from "../features/analytics/AnalyticsPage";
import ReportsPage from "../features/reports/ReportsPage";
import AppLayout from "../components/layout/AppLayout";
import ProtectedRoute from "../components/layout/ProtectedRoute";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />
  },
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
      { path: "production", element: <ProductionPage /> },
      { path: "suppliers", element: <SuppliersPage /> },
      { path: "inventory", element: <InventoryPage /> },
      { path: "analytics", element: <AnalyticsPage /> },
      { path: "reports", element: <ReportsPage /> }
    ]
  }
]);