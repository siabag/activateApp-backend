from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now, localtime
from .models import RegistroAsistencia, ResumenAsistenciaDiaria

@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 'tipo_registro_icon', 'fecha_hora_display', 
        'membresia_estado', 'metodo_ingreso', 'session_consumida_icon',
        'registrado_por_short'
    ]
    list_filter = [
        'tipo_registro', 'metodo_ingreso', 'fecha', 
        'session_consumida', 'es_consumo_sesion'
    ]
    search_fields = [
        'usuario__email', 'usuario__first_name', 
        'usuario__last_name', 'observaciones'
    ]
    readonly_fields = ['fecha', 'session_consumida']
    date_hierarchy = 'fecha_hora'
    
    fieldsets = (
        ('Información del Usuario', {
            'fields': ('usuario', 'membresia')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha_hora', 'fecha')
        }),
        ('Registro', {
            'fields': ('tipo_registro', 'metodo_ingreso', 'registrado_por')
        }),
        ('Control de Sesiones', {
            'fields': ('es_consumo_sesion', 'session_consumida')
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def fecha_hora_display(self, obj):
        """Muestra fecha y hora formateada"""
        fecha_local = localtime(obj.fecha_hora)
        return format_html(
            '<span style="font-weight: bold;">{}</span><br><small>{}</small>',
            fecha_local.strftime('%Y-%m-%d'),
            fecha_local.strftime('%H:%M:%S')
        )
    fecha_hora_display.short_description = 'Fecha y Hora'
    
    def tipo_registro_icon(self, obj):
        """Muestra icono según tipo de registro"""
        if obj.tipo_registro == 'INGRESO':
            return format_html('<span style="color: green;">✓ Ingreso</span>')
        return format_html('<span style="color: blue;">↪ Salida</span>')
    tipo_registro_icon.short_description = 'Tipo'
    
    def membresia_estado(self, obj):
        """Muestra el estado de la membresía"""
        if obj.membresia:
            if obj.membresia.estado == 'ACTIVA':
                return format_html('<span style="color: green;">{} ✓</span>', obj.membresia.get_tipo_display())
            return format_html('<span style="color: red;">{} ✗</span>', obj.membresia.get_tipo_display())
        return format_html('<span style="color: gray;">N/A</span>')
    membresia_estado.short_description = 'Membresía'
    
    def session_consumida_icon(self, obj):
        """Muestra si se consumió sesión"""
        if obj.session_consumida:
            return format_html('<span style="color: green;">✓</span>')
        return format_html('<span style="color: orange;">-</span>')
    session_consumida_icon.short_description = 'Sesión'
    
    def registrado_por_short(self, obj):
        """Muestra quién registró (abreviado)"""
        if obj.registrado_por:
            nombre = f"{obj.registrado_por.first_name} {obj.registrado_por.last_name}"
            return nombre[:20] + '...' if len(nombre) > 20 else nombre
        return format_html('<span style="color: gray;">Sistema</span>')
    registrado_por_short.short_description = 'Registrado por'

@admin.register(ResumenAsistenciaDiaria)
class ResumenAsistenciaDiariaAdmin(admin.ModelAdmin):
    list_display = ['fecha', 'total_ingresos', 'usuarios_unicos', 'total_sesiones_consumidas', 'membresias_utilizadas']
    list_filter = ['fecha']
    readonly_fields = ['fecha', 'total_ingresos', 'usuarios_unicos', 'total_sesiones_consumidas', 'membresias_utilizadas']
    date_hierarchy = 'fecha'