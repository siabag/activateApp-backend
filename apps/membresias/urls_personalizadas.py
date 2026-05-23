from django.urls import path
from apps.membresias.views import (
    MisMembresiasView,
    MisMembresiasActualizadasView,
    MembresiasEstadisticasView,
    AlertasMembresiasView,
    ValidarMembresiasVencidasView,
)

urlpatterns = [
    path('mis-membresias/', MisMembresiasView.as_view(), name='mis-membresias'),
    path('estadisticas/', MembresiasEstadisticasView.as_view(), name='estadisticas-membresias'),
    path('alertas/', AlertasMembresiasView.as_view(), name='alertas-membresias'),
    path('validar-vencidas/', ValidarMembresiasVencidasView.as_view(), name='validar-vencidas'),
    path('mis-membresias-actualizadas/', MisMembresiasActualizadasView.as_view(), name='mis-membresias-actualizadas'),
]