from rest_framework import permissions

from ..users.models import ShowRunner


class IsAdminOrShowRunner(permissions.BasePermission):
    """
    Permission to check if an object can be created.
    """

    def has_permission(self, request, view):
        from .views import PlayoutViewSet

        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Limit the playouts if the user isn't an admin
        playouts = [s.playout.id for s in ShowRunner.objects.filter(user=request.user).all()]
        if isinstance(view, PlayoutViewSet):
            view.queryset = view.queryset.filter(id__in=playouts)
        else:
            view.queryset = view.queryset.filter(playout__id__in=playouts)

        # if the user is authenticated, then let them in for all functions
        return True
