from django.urls import path
from apps.membresias.views import (
    MisMembresiasView,
    MembresiasEstadisticasView,
    AlertasMembresiasView,
)

urlpatterns = [
    path('mis-membresias/', MisMembresiasView.as_view(), name='mis-membresias'),
    path('estadisticas/', MembresiasEstadisticasView.as_view(), name='estadisticas-membresias'),
    path('alertas/', AlertasMembresiasView.as_view(), name='alertas-membresias'),
]