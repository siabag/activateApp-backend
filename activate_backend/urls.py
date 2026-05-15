from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.usuarios.views import UsuarioAdminViewSet
from apps.membresias.views import MembresiaViewSet, HistorialMembresiaViewSet
from apps.asistencia.views import RegistroAsistenciaViewSet, ResumenDiarioViewSet

# Router principal (SOLO para apps que no tienen router local)
router = DefaultRouter()
router.register(r'usuarios/admin', UsuarioAdminViewSet, basename='usuario-admin')
router.register(r'membresias', MembresiaViewSet, basename='membresia')
router.register(r'membresias/historial', HistorialMembresiaViewSet, basename='historial-membresia')
router.register(r'asistencia', RegistroAsistenciaViewSet, basename='asistencia')
router.register(r'asistencia/resumenes', ResumenDiarioViewSet, basename='resumen-diario')
# ❌ NO registrar planes aquí

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Rutas personalizadas
    path('api/usuarios/', include('apps.usuarios.urls_personalizadas')),
    path('api/membresias/', include('apps.membresias.urls_personalizadas')),
    path('api/planes/', include('apps.planes.urls_personalizadas')),
    path('api/asistencia/', include('apps.asistencia.urls_personalizadas')),
    
    # Router principal
    path('api/', include(router.urls)),
]