from rest_framework import viewsets, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.usuarios.models import Usuario
from apps.usuarios.serializers import (
    UsuarioRegistroSerializer,
    UsuarioPerfilSerializer,
    UsuarioAdminSerializer,
    UsuarioCambioPasswordSerializer,
    UsuarioUpdateFichaFisicaSerializer
)
from apps.usuarios.permissions import IsPropietarioOrPersonal

class UsuarioRegisterView(APIView):
    """Registro público de usuarios. Retorna tokens JWT para login inmediato."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UsuarioRegistroSerializer(data=request.data)
        if serializer.is_valid():
            usuario = serializer.save()
            # Generar tokens JWT
            refresh = RefreshToken.for_user(usuario)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'usuario': UsuarioPerfilSerializer(usuario).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsuarioProfileView(RetrieveUpdateAPIView):
    """Visualizar y actualizar el perfil propio (autogestión)"""
    serializer_class = UsuarioPerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

class UsuarioPasswordChangeView(APIView):
    """Cambio de contraseña seguro para usuario autenticado"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = UsuarioCambioPasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': 'Contraseña actualizada exitosamente.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsuarioFichaFisicaView(APIView):
    """Endpoint dedicado para actualizar peso, altura y recalcular IMC"""
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        usuario = request.user
        serializer = UsuarioUpdateFichaFisicaSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de usuarios.
    - Propietario: ve y gestiona todos los usuarios.
    - Personal: ve y gestiona solo clientes.
    """
    permission_classes = [permissions.IsAuthenticated, IsPropietarioOrPersonal]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'telefono']
    ordering_fields = ['date_joined', 'last_name', 'first_name']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return UsuarioRegistroSerializer
        return UsuarioAdminSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'PERSONAL':
            return Usuario.objects.filter(role='CLIENTE')
        return Usuario.objects.all()