from rest_framework import permissions

class IsPropietario(permissions.BasePermission):
    """Permite acceso únicamente al rol PROPIETARIO"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'PROPIETARIO'

class IsPropietarioOrPersonal(permissions.BasePermission):
    """Permite acceso a PROPIETARIO y PERSONAL (entrenadores/recepción)"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['PROPIETARIO', 'PERSONAL']

class IsOwnerOrPropietario(permissions.BasePermission):
    """Permite editar recursos solo si eres el dueño o el PROPIETARIO"""
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.role == 'PROPIETARIO'