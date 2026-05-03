from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Prefetch

from apps.planes.models import PlanEntrenamiento, Ejercicio, HistorialPlanUsuario
from apps.planes.serializers import (
    PlanEntrenamientoListSerializer,
    PlanEntrenamientoDetailSerializer,
    PlanEntrenamientoCreateSerializer,
    EjercicioCreateSerializer,
    HistorialPlanUsuarioSerializer,
    MisPlanesSerializer
)
from apps.usuarios.permissions import IsPropietarioOrPersonal
from apps.usuarios.models import Usuario


class PlanEntrenamientoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Planes de Entrenamiento.
    - Propietario/Personal: Crean, editan, asignan y gestionan todos los planes.
    - Cliente: Solo visualiza los planes que tiene asignados y están activos.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'area_muscular', 'nivel_dificultad']
    ordering_fields = ['fecha_creacion', 'nombre', 'nivel_dificultad']
    ordering = ['-fecha_creacion']

    def get_serializer_class(self):
        if self.action == 'create':
            return PlanEntrenamientoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlanEntrenamientoCreateSerializer  # Reutilizamos el mismo para update
        elif self.action == 'retrieve':
            return PlanEntrenamientoDetailSerializer
        return PlanEntrenamientoListSerializer

    def get_queryset(self):
        user = self.request.user
        # prefetch_related evita el problema N+1 al cargar ejercicios y usuarios
        queryset = PlanEntrenamiento.objects.prefetch_related(
            Prefetch('ejercicios', queryset=Ejercicio.objects.filter(activo=True).order_by('orden')),
            'usuarios_asignados'
        )

        if user.role == 'CLIENTE':
            # Clientes solo ven sus planes asignados y activos
            return queryset.filter(usuarios_asignados=user, activo=True).distinct()
        
        # Staff ve todos los planes del sistema
        return queryset.all()

    def perform_create(self, serializer):
        # Asigna automáticamente al creador (Personal/Propietario)
        serializer.save(creado_por=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsPropietarioOrPersonal])
    def asignar(self, request, pk=None):
        """Asigna el plan a una lista de usuarios y registra en el historial"""
        plan = self.get_object()
        usuarios_ids = request.data.get('usuarios', [])

        if not usuarios_ids:
            return Response({'error': 'Se requiere la lista de IDs de usuarios.'}, status=status.HTTP_400_BAD_REQUEST)

        # Asignación masiva segura
        plan.usuarios_asignados.add(*usuarios_ids)

        # Registro en historial (bulk para rendimiento)
        historial_entries = [
            HistorialPlanUsuario(usuario_id=uid, plan=plan, estado='ASIGNADO')
            for uid in usuarios_ids
        ]
        HistorialPlanUsuario.objects.bulk_create(historial_entries, ignore_conflicts=True)

        return Response({'detail': f'Plan asignado a {len(usuarios_ids)} usuarios correctamente.'})

    @action(detail=True, methods=['post'], permission_classes=[IsPropietarioOrPersonal])
    def desasignar(self, request, pk=None):
        """Retira el plan de una lista de usuarios y actualiza el historial"""
        plan = self.get_object()
        usuarios_ids = request.data.get('usuarios', [])
        
        plan.usuarios_asignados.remove(*usuarios_ids)

        # Marcar en historial como cancelado
        HistorialPlanUsuario.objects.filter(
            usuario_id__in=usuarios_ids,
            plan=plan,
            estado='ASIGNADO'
        ).update(estado='CANCELADO', fecha_finalizacion=timezone.now())

        return Response({'detail': 'Usuarios desasignados correctamente.'})

    @action(detail=True, methods=['post'], permission_classes=[IsPropietarioOrPersonal])
    def marcar_completado(self, request, pk=None):
        """Marca un plan como completado para un usuario específico"""
        plan = self.get_object()
        usuario_id = request.data.get('usuario')
        
        if not usuario_id:
            return Response({'error': 'ID de usuario requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        historial = HistorialPlanUsuario.objects.filter(usuario_id=usuario_id, plan=plan).first()
        if historial:
            historial.estado = 'COMPLETADO'
            historial.progreso_porcentaje = 100.00
            historial.fecha_finalizacion = timezone.now()
            historial.save()
            return Response({'detail': 'Plan marcado como completado correctamente.'})
            
        return Response({'error': 'No se encontró registro de asignación para este usuario.'}, status=status.HTTP_404_NOT_FOUND)


class MisPlanesView(APIView):
    """
    Endpoint optimizado para que el cliente consulte sus planes activos.
    Incluye ejercicios precargados para evitar consultas adicionales en frontend.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        planes = PlanEntrenamiento.objects.filter(
            usuarios_asignados=request.user,
            activo=True
        ).prefetch_related(
            Prefetch('ejercicios', queryset=Ejercicio.objects.filter(activo=True).order_by('orden'))
        ).distinct()

        serializer = MisPlanesSerializer(planes, many=True, context={'request': request})
        return Response(serializer.data)


class HistorialPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Seguimiento de asignación, progreso y estado de planes por usuario.
    """
    serializer_class = HistorialPlanUsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_asignacion']
    ordering = ['-fecha_asignacion']

    def get_queryset(self):
        user = self.request.user
        queryset = HistorialPlanUsuario.objects.select_related('usuario', 'plan')

        if user.role == 'CLIENTE':
            return queryset.filter(usuario=user)
        return queryset.all()