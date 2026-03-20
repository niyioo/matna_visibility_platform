export const isAdmin = (user) => user?.role === "ADMIN";
export const isOperations = (user) => user?.role === "OPERATIONS";
export const isManagement = (user) => user?.role === "MANAGEMENT";

export const canManageData = (user) =>
  isAdmin(user) || isOperations(user);

export const canViewManagement = (user) =>
  isAdmin(user) || isManagement(user);