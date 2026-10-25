export const ROLES = Object.freeze({
  ADMIN: "ADMIN",
  OPERATIONS: "OPERATIONS",
  MANAGEMENT: "MANAGEMENT",
});

export const DATA_ENTRY_ROLES = [ROLES.ADMIN, ROLES.OPERATIONS];

export const isAdmin = (user) => user?.role === ROLES.ADMIN;

/** Can record production entries, suppliers and deliveries. */
export const canManageData = (user) => DATA_ENTRY_ROLES.includes(user?.role);

/** Can void records and adjust stock (reverses inventory). */
export const canVoidRecords = isAdmin;
