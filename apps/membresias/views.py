from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from datetime import timedelta

from apps.membresias.models import Membresia, HistorialMembresia
from apps.membresias.serializers import (
    MembresiaCreateSerializer,
    MembresiaDetailSerializer,
    MembresiaUpdateSerializer,
    MembresiaResumenSerializer,
    MembresiaEstadisticasSerializer,
    MembresiaConHistorialSerializer,
    HistorialMembresiaSerializer
)
from apps.usuarios.permissions import IsPropietarioOrPersonal


class MembresiaViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de membresías.
    - Propietario/Personal: Crear, listar todas, actualizar, eliminar
    - Cliente: Solo ver sus propias membresías (endpoint separado)
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['usuario__email', 'usuario__first_name', 'usuario__last_name', 'tipo']
    ordering_fields = ['fecha_inicio', 'fecha_vencimiento', 'precio', 'estado']
    ordering = ['-fecha_inicio']

    def get_serializer_class(self):
        if self.action == 'create':
            return MembresiaCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MembresiaUpdateSerializer
        elif self.action == 'retrieve':
            return MembresiaConHistorialSerializer
        return MembresiaDetailSerializer

    def get_queryset(self):
        user = self.request.user
        
        # Si es cliente, solo ve sus propias membresías
        if user.role == 'CLIENTE':
            return Membresia.objects.filter(usuario=user)
        
        # Propietario y Personal ven todas las membresías
        queryset = Membresia.objects.select_related('usuario').all()
        
        # Filtro por estado (query param: ?estado=ACTIVA)
        estado = self.request.query_params.get('estado', None)
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por tipo (query param: ?tipo=MENSUAL)
        tipo = self.request.query_params.get('tipo', None)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset

    def perform_create(self, serializer):
        # Asignar automáticamente el estado inicial
        membresia = serializer.save(estado='ACTIVA')
        
        # Registrar en historial
        HistorialMembresia.objects.create(
            membresia=membresia,
            estado_anterior='',
            estado_nuevo='ACTIVA',
            motivo='Creación de membresía'
        )

    @action(detail=True, methods=['post'], permission_classes=[IsPropietarioOrPersonal])
    def renovar(self, request, pk=None):
        """Renovar una membresía vencida o próxima a vencer"""
        membresia = self.get_object()
        
        if membresia.estado == 'VENCIDA':
            # Crear nueva membresía con los mismos datos
            # Pasar fecha_inicio explícitamente como date para evitar error de comparación
            nueva_membresia = Membresia.objects.create(
                usuario=membresia.usuario,
                tipo=membresia.tipo,
                precio=membresia.precio,
                sesiones_totales=membresia.sesiones_totales,
                fecha_inicio=timezone.now().date(), 
                observaciones=f"Renovación de membresía #{membresia.id}"
            )
            
            HistorialMembresia.objects.create(
                membresia=nueva_membresia,
                estado_anterior='',
                estado_nuevo='ACTIVA',
                motivo='Renovación automática'
            )
            
            serializer = MembresiaDetailSerializer(nueva_membresia)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(
            {'detail': 'La membresía aún está activa. No requiere renovación.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], permission_classes=[IsPropietarioOrPersonal])
    def cancelar(self, request, pk=None):
        """Cancelar una membresía activa (por solicitud del cliente o incumplimiento)"""
        membresia = self.get_object()
        estado_anterior = membresia.estado
        
        if membresia.estado == 'ACTIVA':
            membresia.estado = 'VENCIDA'
            membresia.save()
            
            HistorialMembresia.objects.create(
                membresia=membresia,
                estado_anterior=estado_anterior,
                estado_nuevo='VENCIDA',
                motivo=request.data.get('motivo', 'Cancelación manual')
            )
            
            return Response({'detail': 'Membresía cancelada exitosamente.'})
        
        return Response(
            {'detail': 'La membresía ya no está activa.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MisMembresiasView(APIView):
    """
    Endpoint para que el cliente vea solo sus membresías.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        membresias = Membresia.objects.filter(usuario=request.user).order_by('-fecha_inicio')
        serializer = MembresiaDetailSerializer(membresias, many=True)
        return Response(serializer.data)


class MembresiasEstadisticasView(APIView):
    """
    Dashboard de estadísticas de membresías (solo Propietario).
    """
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]

    def get(self, request):
        hoy = timezone.now().date()
        siete_dias = hoy + timedelta(days=7)
        treinta_dias = hoy + timedelta(days=30)

        # Estadísticas generales
        total_membresias = Membresia.objects.count()
        membresias_activas = Membresia.objects.filter(estado='ACTIVA').count()
        membresias_vencidas = Membresia.objects.filter(estado='VENCIDA').count()
        membresias_por_vencer_7_dias = Membresia.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lte=siete_dias,
            fecha_vencimiento__gte=hoy
        ).count()
        membresias_por_vencer_30_dias = Membresia.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lte=treinta_dias,
            fecha_vencimiento__gt=siete_dias
        ).count()

        # Ingresos
        ingreso_total = Membresia.objects.aggregate(Sum('precio'))['precio__sum'] or 0
        promedio_precio = Membresia.objects.aggregate(Avg('precio'))['precio__avg'] or 0

        # Membresías por tipo
        membresias_por_tipo = dict(
            Membresia.objects.values_list('tipo').annotate(count=Count('id'))
        )

        data = {
            'total_membresias': total_membresias,
            'membresias_activas': membresias_activas,
            'membresias_vencidas': membresias_vencidas,
            'membresias_por_vencer_7_dias': membresias_por_vencer_7_dias,
            'membresias_por_vencer_30_dias': membresias_por_vencer_30_dias,
            'ingreso_total': float(ingreso_total),
            'promedio_precio': float(promedio_precio),
            'membresias_por_tipo': membresias_por_tipo,
        }

        serializer = MembresiaEstadisticasSerializer(data)
        return Response(serializer.data)


class AlertasMembresiasView(APIView):
    """
    Alertas de membresías próximas a vencer (para notificaciones).
    """
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]

    def get(self, request):
        hoy = timezone.now().date()
        siete_dias = hoy + timedelta(days=7)

        # Membresías que vencen en los próximos 7 días
        por_vencer = Membresia.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lte=siete_dias,
            fecha_vencimiento__gte=hoy
        ).select_related('usuario')

        alertas = []
        for membresia in por_vencer:
            dias_restantes = (membresia.fecha_vencimiento - hoy).days
            alertas.append({
                'membresia_id': membresia.id,
                'usuario': f"{membresia.usuario.first_name} {membresia.usuario.last_name}",
                'email': membresia.usuario.email,
                'tipo': membresia.get_tipo_display(),
                'fecha_vencimiento': membresia.fecha_vencimiento.isoformat(),
                'dias_restantes': dias_restantes,
                'nivel_alerta': 'CRITICA' if dias_restantes <= 3 else 'ADVERTENCIA'
            })

        return Response({
            'total_alertas': len(alertas),
            'alertas': alertas
        })


class HistorialMembresiaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura del historial de cambios de membresías.
    Útil para auditoría.
    """
    serializer_class = HistorialMembresiaSerializer
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_cambio']
    ordering = ['-fecha_cambio']

    def get_queryset(self):
        membresia_id = self.request.query_params.get('membresia', None)
        if membresia_id:
            return HistorialMembresia.objects.filter(membresia_id=membresia_id)
        return HistorialMembresia.objects.all()