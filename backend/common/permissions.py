from rest_framework.permissions import SAFE_METHODS, BasePermission

ADMIN = "ADMIN"
OPERATIONS = "OPERATIONS"
MANAGEMENT = "MANAGEMENT"
ALL_ROLES = frozenset({ADMIN, OPERATIONS, MANAGEMENT})


def _has_role(request, roles) -> bool:
    user = request.user
    return bool(user and user.is_authenticated and user.is_active and getattr(user, "role", None) in roles)


class RolePermission(BasePermission):
    """Grants access to authenticated, active users whose role is in `roles`."""

    roles: frozenset = frozenset()

    def has_permission(self, request, view):
        return _has_role(request, self.roles)


class IsAdminRole(RolePermission):
    roles = frozenset({ADMIN})


class IsAdminOrOperations(RolePermission):
    roles = frozenset({ADMIN, OPERATIONS})


class IsAnyOperationalRole(RolePermission):
    roles = ALL_ROLES


class IsAdminOrReadOnly(BasePermission):
    """Any known role may read; only admins may write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return _has_role(request, ALL_ROLES)
        return _has_role(request, {ADMIN})
