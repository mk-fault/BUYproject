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
        
# class IsOwner(BasePermission):
#     def has_permission(self, request, view):
        


class IsRole0(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "0"
    
class IsRole1(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "1"

class IsRole2(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "2"
    
class IsRole0OrRole1(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "1" or request.user.role == '0'

class IsRole3(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "3"

class IsRole4(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "4"

class IsRole5(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return request.user.role == "5"


            