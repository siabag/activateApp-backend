from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ['email', 'first_name', 'last_name', 'role', 'peso', 'altura', 'imc', 'is_active']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'telefono']
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información personal', {'fields': ('first_name', 'last_name', 'telefono', 'role')}),
        ('Ficha física', {'fields': ('peso', 'altura', 'imc')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role'),
        }),
    )