from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
from .models import Membresia, HistorialMembresia

@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'tipo', 'precio', 'fecha_inicio', 
        'fecha_vencimiento', 'estado', 'dias_restantes_display', 
        'sesiones_consumidas', 'sesiones_totales'
    ]
    list_filter = ['estado', 'tipo', 'fecha_inicio', 'fecha_vencimiento']
    search_fields = ['usuario__email', 'usuario__first_name', 'usuario__last_name']
    readonly_fields = ['fecha_compra', 'dias_restantes_display', 'estado_actual']
    date_hierarchy = 'fecha_inicio'
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario',)
        }),
        ('Detalles de la Membresía', {
            'fields': ('tipo', 'precio', 'observaciones')
        }),
        ('Fechas y Vigencia', {
            'fields': ('fecha_inicio', 'fecha_vencimiento', 'fecha_compra')
        }),
        ('Estado y Control', {
            'fields': ('estado_actual', 'dias_restantes_display', 'sesiones_totales', 'sesiones_consumidas')
        }),
    )
    
    def dias_restantes_display(self, obj):
        """Muestra los días restantes en el admin"""
        dias = obj.get_dias_restantes()
        if dias == 0:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Vencida</span>')
        elif dias <= 7:
            return format_html('<span style="color: orange; font-weight: bold;">{} días restantes</span>', dias)
        return format_html('<span style="color: green;">{} días restantes</span>', dias)
    dias_restantes_display.short_description = 'Días Restantes'
    
    def estado_actual(self, obj):
        """Muestra el estado actual con icono"""
        if obj.estado == 'ACTIVA':
            return format_html('<span style="color: green;">✓ {}</span>', obj.get_estado_display())
        return format_html('<span style="color: red;">✗ {}</span>', obj.get_estado_display())
    estado_actual.short_description = 'Estado'

@admin.register(HistorialMembresia)
class HistorialMembresiaAdmin(admin.ModelAdmin):
    list_display = ['membresia', 'fecha_cambio', 'estado_anterior', 'estado_nuevo', 'motivo']
    list_filter = ['fecha_cambio', 'estado_anterior', 'estado_nuevo']
    readonly_fields = ['fecha_cambio']