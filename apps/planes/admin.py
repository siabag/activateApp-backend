from django.contrib import admin
from django.utils.html import format_html
from .models import PlanEntrenamiento, Ejercicio, HistorialPlanUsuario

class EjercicioInline(admin.TabularInline):
    """Inline para mostrar ejercicios dentro del plan"""
    model = Ejercicio
    extra = 1
    fields = ['nombre', 'series', 'repeticiones', 'descanso_segundos', 'orden', 'activo']
    ordering = ['orden']

@admin.register(PlanEntrenamiento)
class PlanEntrenamientoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'area_muscular', 'nivel_dificultad', 
        'total_ejercicios', 'usuarios_activos_count',
        'activo', 'fecha_creacion'
    ]
    list_filter = ['area_muscular', 'nivel_dificultad', 'activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion', 'area_muscular']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'total_ejercicios']
    inlines = [EjercicioInline]
    filter_horizontal = ['usuarios_asignados']
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información del Plan', {
            'fields': ('nombre', 'descripcion', 'area_muscular')
        }),
        ('Configuración', {
            'fields': ('nivel_dificultad', 'duracion_semanas', 'activo')
        }),
        ('Asignación', {
            'fields': ('creado_por', 'usuarios_asignados')
        }),
        ('Información Adicional', {
            'fields': ('observaciones_generales', 'fecha_creacion', 'fecha_actualizacion', 'total_ejercicios'),
            'classes': ('collapse',)
        }),
    )
    
    def total_ejercicios(self, obj):
        return obj.total_ejercicios()
    total_ejercicios.short_description = 'Total Ejercicios'
    
    def usuarios_activos_count(self, obj):
        count = obj.usuarios_activos_count()
        if count > 0:
            return format_html('<span style="color: green;">{} usuarios</span>', count)
        return format_html('<span style="color: gray;">Sin asignar</span>')
    usuarios_activos_count.short_description = 'Usuarios Activos'

@admin.register(Ejercicio)
class EjercicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'plan', 'series', 'repeticiones', 'descanso_formatted', 'orden', 'activo']
    list_filter = ['plan', 'area_especifica', 'activo']
    search_fields = ['nombre', 'descripcion', 'area_especifica']
    readonly_fields = ['descanso_formatted']
    ordering = ['plan', 'orden']
    
    fieldsets = (
        ('Información del Ejercicio', {
            'fields': ('plan', 'nombre', 'descripcion', 'area_especifica')
        }),
        ('Parámetros de Entrenamiento', {
            'fields': ('series', 'repeticiones', 'descanso_segundos', 'peso_sugerido')
        }),
        ('Configuración', {
            'fields': ('orden', 'activo', 'observaciones')
        }),
    )
    
    def descanso_formatted(self, obj):
        return obj.get_descanso_formatted()
    descanso_formatted.short_description = 'Descanso'

@admin.register(HistorialPlanUsuario)
class HistorialPlanUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plan', 'estado', 'progreso_porcentaje', 'fecha_asignacion', 'fecha_finalizacion']
    list_filter = ['estado', 'fecha_asignacion']
    search_fields = ['usuario__email', 'usuario__first_name', 'plan__nombre']
    readonly_fields = ['fecha_asignacion', 'progreso_porcentaje']
    date_hierarchy = 'fecha_asignacion'
    
    fieldsets = (
        ('Información', {
            'fields': ('usuario', 'plan', 'estado')
        }),
        ('Fechas', {
            'fields': ('fecha_asignacion', 'fecha_finalizacion')
        }),
        ('Seguimiento', {
            'fields': ('progreso_porcentaje', 'observaciones_seguimiento')
        }),
    )