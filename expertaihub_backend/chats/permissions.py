# chats/permissions.py

from rest_framework import permissions

class IsOwnerOrPublicOrAllowed(permissions.BasePermission):
    """
    - If share_option=="link", anyone can GET.
    - If request.user is owner or in allowed_users, they can GET.
    - Otherwise deny.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if obj.share_option == "link":
                return True
            if request.user and request.user.is_authenticated:
                if obj.user == request.user:
                    return True
                if obj.allowed_users.filter(pk=request.user.pk).exists():
                    return True
        # for non-safe methods, only owner:
        return obj.user == request.user
