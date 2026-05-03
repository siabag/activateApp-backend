from django.urls import path
from apps.asistencia.views import ReporteAsistenciaView, ClientesActivosView

urlpatterns = [
    path('reportes/', ReporteAsistenciaView.as_view(), name='reporte-asistencia'),
    path('activos/', ClientesActivosView.as_view(), name='clientes-activos'),
]