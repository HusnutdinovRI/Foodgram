from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPostOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method == 'POST' or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or
            (request.user.is_authenticated and obj.author == request.user)
        )


class IsAdminUserOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        return request.user and request.user.is_staff
