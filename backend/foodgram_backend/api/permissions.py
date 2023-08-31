from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedOrAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated or request.user.is_superuser


class IsAdminOrSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_superuser or  
            (request.user.is_authenticated and obj == request.user) 
        )