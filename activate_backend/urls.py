"""
URL configuration for activate_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# Importar ViewSets de todas las apps
from apps.usuarios.views import UsuarioAdminViewSet
from apps.membresias.views import MembresiaViewSet, HistorialMembresiaViewSet
from apps.asistencia.views import RegistroAsistenciaViewSet, ResumenDiarioViewSet
from apps.planes.views import PlanEntrenamientoViewSet, HistorialPlanViewSet

# Crear UN SOLO router central
router = DefaultRouter()

# Registrar todos los ViewSets
router.register(r'usuarios/admin', UsuarioAdminViewSet, basename='usuario-admin')
router.register(r'membresias', MembresiaViewSet, basename='membresia')
router.register(r'membresias/historial', HistorialMembresiaViewSet, basename='historial-membresia')
router.register(r'asistencia', RegistroAsistenciaViewSet, basename='asistencia')
router.register(r'asistencia/resumenes', ResumenDiarioViewSet, basename='resumen-diario')
router.register(r'planes', PlanEntrenamientoViewSet, basename='plan')
router.register(r'planes/historial', HistorialPlanViewSet, basename='historial-plan')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 1️⃣ PRIMERO: Rutas personalizadas (Tienen prioridad sobre el router)
    path('api/usuarios/', include('apps.usuarios.urls_personalizadas')),
    path('api/membresias/', include('apps.membresias.urls_personalizadas')),
    path('api/planes/', include('apps.planes.urls_personalizadas')),
    path('api/asistencia/', include('apps.asistencia.urls_personalizadas')),
    
    # 2️⃣ DESPUÉS: Rutas del router estándar (CRUD genérico)
    path('api/', include(router.urls)),
]