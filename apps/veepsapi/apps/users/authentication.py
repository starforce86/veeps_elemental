from rest_framework import permissions
from .models import AllowList


class AllowListPermission(permissions.BasePermission):
    """
    Global permission check for allowed IPs.
    """

    def has_permission(self, request, view):
        ip_addr = request.META["REMOTE_ADDR"]
        allowed = AllowList.objects.filter(ip_addr=ip_addr).exists()
        return allowed


class IsAdminOrAllowListPermission(permissions.BasePermission):
    """
    Global permission check for allowed IPs.
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        ip_addr = request.META["REMOTE_ADDR"]
        allowed = AllowList.objects.filter(ip_addr=ip_addr).exists()
        return allowed
