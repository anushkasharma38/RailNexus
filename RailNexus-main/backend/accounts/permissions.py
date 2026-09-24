from rest_framework.permissions import SAFE_METHODS, BasePermission


class RoleWritePermission(BasePermission):
    """Read for authenticated users; controlled writes for the prototype roles."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        if request.user.role in {"ADMIN", "CONTROL_OFFICE"}:
            return True
        resource = getattr(view, "basename", "")
        if request.method == "POST" and resource == "maintenancetask":
            return request.data.get("department") == request.user.role
        if request.method == "POST" and resource == "blockrequest":
            from maintenance.models import MaintenanceTask
            return MaintenanceTask.objects.filter(
                id=request.data.get("maintenance_task"), department=request.user.role
            ).exists()
        return False
