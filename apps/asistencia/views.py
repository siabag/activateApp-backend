from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Count, Q, Max
from datetime import timedelta

from apps.asistencia.models import RegistroAsistencia, ResumenAsistenciaDiaria
from apps.asistencia.serializers import (
    RegistroAsistenciaCreateSerializer,
    RegistroAsistenciaDetailSerializer,
    RegistroAsistenciaListSerializer,
    RegistroAsistenciaUpdateSerializer,
    ResumenAsistenciaDiariaSerializer
)
from apps.usuarios.permissions import IsPropietarioOrPersonal
from apps.membresias.models import Membresia


class RegistroAsistenciaViewSet(viewsets.ModelViewSet):
    """
    CRUD de registros de asistencia.
    - Cliente: Solo consulta su propio historial.
    - Personal/Propietario: Crea, corrige y filtra registros de todos.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['usuario__email', 'usuario__first_name', 'usuario__last_name']
    ordering_fields = ['fecha_hora', 'fecha']
    ordering = ['-fecha_hora']

    def get_serializer_class(self):
        if self.action == 'create':
            return RegistroAsistenciaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RegistroAsistenciaUpdateSerializer
        elif self.action == 'retrieve':
            return RegistroAsistenciaDetailSerializer
        return RegistroAsistenciaListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = RegistroAsistencia.objects.select_related('usuario', 'membresia', 'registrado_por')

        # 🔒 Aislamiento por rol
        if user.role == 'CLIENTE':
            return queryset.filter(usuario=user)

        # 🔍 Filtros avanzados para Staff
        fecha = self.request.query_params.get('fecha')
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')
        tipo = self.request.query_params.get('tipo')
        usuario_id = self.request.query_params.get('usuario')

        if fecha:
            queryset = queryset.filter(fecha=fecha)
        if fecha_inicio:
            queryset = queryset.filter(fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(fecha__lte=fecha_fin)
        if tipo:
            queryset = queryset.filter(tipo_registro=tipo)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)

        return queryset

    def perform_create(self, serializer):
        # 👤 Asignar automáticamente al staff que registra el check-in
        user = self.request.user
        data = serializer.validated_data
        
        # Si no se envió membresía, buscar la activa del usuario
        if 'membresia' not in data or data['membresia'] is None:
            usuario_id = data.get('usuario').id if hasattr(data.get('usuario'), 'id') else data.get('usuario')
            
            membresia_activa = Membresia.objects.filter(
                usuario_id=usuario_id,
                estado='ACTIVA',
                fecha_vencimiento__gte=timezone.now().date()
            ).first()
            
            if membresia_activa:
                if user.role in ['PROPIETARIO', 'PERSONAL']:
                    serializer.save(membresia=membresia_activa, registrado_por=user)
                else:
                    serializer.save(membresia=membresia_activa)
            else:
                raise ValidationError({"membresia": "El usuario no tiene una membresía activa. No se puede registrar asistencia."})
        else:
            # Si ya se envió membresía, guardar normalmente
            if user.role in ['PROPIETARIO', 'PERSONAL']:
                serializer.save(registrado_por=user)
            else:
                serializer.save()

    @action(detail=False, methods=['get'], permission_classes=[IsPropietarioOrPersonal])
    def resumen_hoy(self, request):
        """📊 Estadísticas rápidas del día actual para dashboard"""
        hoy = timezone.now().date()
        ingresos = self.get_queryset().filter(fecha=hoy, tipo_registro='INGRESO')

        return Response({
            'fecha': hoy.isoformat(),
            'total_ingresos': ingresos.count(),
            'usuarios_unicos': ingresos.values('usuario').distinct().count(),
            'sesiones_consumidas': ingresos.filter(session_consumida=True).count()
        })


class ResumenDiarioViewSet(viewsets.ReadOnlyModelViewSet):
    """
    📈 Historial de resúmenes diarios (generado automáticamente).
    Solo lectura, usado para reportes históricos y auditoría.
    """
    serializer_class = ResumenAsistenciaDiariaSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]
    queryset = ResumenAsistenciaDiaria.objects.all().order_by('-fecha')


class ReporteAsistenciaView(APIView):
    """
    📑 Reporte operativo de asistencia por período (Semanal/Mensual).
    Cumple con el Objetivo Específico 7 del plan de trabajo.
    """
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]

    def get(self, request):
        periodo = request.query_params.get('periodo', 'semanal')
        hoy = timezone.now().date()

        if periodo == 'semanal':
            inicio = hoy - timedelta(days=hoy.weekday())  # Lunes
        else:  # mensual
            inicio = hoy.replace(day=1)

        # Base de datos filtrada
        base = RegistroAsistencia.objects.filter(
            fecha__gte=inicio,
            fecha__lte=hoy,
            tipo_registro='INGRESO'
        )

        # Agregaciones
        totales = {
            'ingresos': base.count(),
            'sesiones_consumidas': base.filter(session_consumida=True).count(),
            'usuarios_unicos': base.values('usuario').distinct().count()
        }

        # Desglose por día para gráficos
        detalle_diario = list(
            base.values('fecha').annotate(
                ingresos=Count('id'),
                sesiones=Count('id', filter=Q(session_consumida=True))
            ).order_by('fecha')
        )

        return Response({
            'periodo': periodo,
            'rango': {'inicio': inicio.isoformat(), 'fin': hoy.isoformat()},
            'totales': totales,
            'detalle_diario': detalle_diario
        })


class ClientesActivosView(APIView):
    """
    🟢 Lista de clientes que están actualmente en el gimnasio.
    Busca el último registro de cada usuario (sin importar la fecha).
    Si el último registro fue INGRESO y no tiene SALIDA posterior, está activo.
    """
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]

    def get(self, request):
        from django.db.models import Max

        # 1. Obtenemos el ID del último registro de CADA usuario
        ultimos_registros = RegistroAsistencia.objects.values('usuario').annotate(
            ultimo_id=Max('id')
        )
        
        # 2. Obtenemos los objetos completos de esos últimos registros
        ids_ultimos = [r['ultimo_id'] for r in ultimos_registros]
        
        # Filtramos los que terminaron con INGRESO
        ultimos = RegistroAsistencia.objects.filter(
            id__in=ids_ultimos,
            tipo_registro='INGRESO'
        ).select_related('usuario', 'membresia')

        # 3. Construimos la lista de activos
        activos = []
        for registro in ultimos:
            # ✅ CORRECCIÓN: Usar get_tipo_display() en lugar de .tipo_display
            membresia_nombre = registro.membresia.get_tipo_display() if registro.membresia else 'Sin membresía'
            
            activos.append({
                'id': registro.id,
                'usuario_id': registro.usuario.id,
                'nombre': f"{registro.usuario.first_name} {registro.usuario.last_name}",
                'hora_ingreso': registro.fecha_hora.strftime('%H:%M %d/%m'),
                'membresia': membresia_nombre
            })

        return Response(activos)