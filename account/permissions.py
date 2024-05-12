from rest_framework.permissions import BasePermission

class IsAdminOrOwnerPutOnly(BasePermission):
    def has_permission(self, request, view):
            if request.method in ['GET', 'POST', 'PATCH', 'DELETE']:
                return request.user.is_superuser
            elif request.method == 'PUT':
                return True
            else:
                return False

    def has_object_permission(self, request, view, obj):
        if request.method == 'PUT':
            return str(obj.username) == str(request.user)
        else:
            return True
            