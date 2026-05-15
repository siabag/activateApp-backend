from django.urls import path
from apps.planes.views import PlanEntrenamientoViewSet, HistorialPlanViewSet, MisPlanesView

urlpatterns = [
    # CRUD de Planes (rutas manuales)
    path('', PlanEntrenamientoViewSet.as_view({'get': 'list', 'post': 'create'}), name='plan-list'),
    path('<int:pk>/', PlanEntrenamientoViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='plan-detail'),
    
    # Historial de Planes (rutas manuales)
    path('historial/', HistorialPlanViewSet.as_view({'get': 'list'}), name='historial-list'),
    path('historial/<int:pk>/', HistorialPlanViewSet.as_view({'get': 'retrieve'}), name='historial-detail'),
    
    # Acciones personalizadas de Planes
    path('<int:pk>/asignar/', PlanEntrenamientoViewSet.as_view({'post': 'asignar'}), name='plan-asignar'),
    path('<int:pk>/desasignar/', PlanEntrenamientoViewSet.as_view({'post': 'desasignar'}), name='plan-desasignar'),
    path('<int:pk>/marcar_completado/', PlanEntrenamientoViewSet.as_view({'post': 'marcar_completado'}), name='plan-marcar-completado'),
    
    # Ruta personalizada adicional
    path('mis-planes/', MisPlanesView.as_view(), name='mis-planes'),
]