from rest_framework import serializers
from django.utils import timezone
from apps.asistencia.models import RegistroAsistencia, ResumenAsistenciaDiaria
from apps.usuarios.serializers import UsuarioBaseSerializer
from apps.membresias.serializers import MembresiaBaseSerializer


class RegistroAsistenciaListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados (historial de asistencia).
    Incluye datos básicos del usuario y membresía para no sobrecargar la respuesta.
    """
    usuario_info = UsuarioBaseSerializer(source='usuario', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_registro_display', read_only=True)
    metodo_display = serializers.CharField(source='get_metodo_ingreso_display', read_only=True)

    class Meta:
        model = RegistroAsistencia
        fields = [
            'id', 'usuario', 'usuario_info', 
            'fecha_hora', 'tipo_registro', 'tipo_display',
            'metodo_ingreso', 'metodo_display', 
            'session_consumida', 'observaciones'
        ]


class RegistroAsistenciaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para registrar nueva asistencia (Ingreso/Salida).
    Valida que la membresía esté activa y pertenezca al usuario.
    """
    class Meta:
        model = RegistroAsistencia
        fields = [
            'usuario', 'membresia', 'tipo_registro', 
            'metodo_ingreso', 'observaciones'
        ]
        # 🔧 CORRECCIÓN: Hacer que membresia sea opcional para que el ViewSet la busque
        extra_kwargs = {
            'membresia': {'required': False, 'allow_null': True}
        }

    def validate(self, attrs):
        usuario = attrs.get('usuario')
        membresia = attrs.get('membresia')
        tipo_registro = attrs.get('tipo_registro', 'INGRESO')

        # 1. Validar que la membresía pertenezca al usuario (si se envió)
        if membresia and membresia.usuario != usuario:
            raise serializers.ValidationError({
                "membresia": "La membresía seleccionada no pertenece al usuario especificado."
            })

        # 2. Validar que no exista un ingreso para hoy (si es tipo INGRESO)
        if tipo_registro == 'INGRESO':
            hoy = timezone.now().date()
            existe_ingreso = RegistroAsistencia.objects.filter(
                usuario=usuario,
                fecha=hoy,
                tipo_registro='INGRESO'
            ).exists()
            
            if existe_ingreso:
                raise serializers.ValidationError({
                    "tipo_registro": "El usuario ya tiene un registro de ingreso para hoy."
                })

        # Ahora el perform_create del ViewSet se encarga de buscarla automáticamente
        # y lanzar un error si no existe ninguna activa.

        return attrs

    def create(self, validated_data):
        # Aseguramos que session_consumida sea False inicialmente
        # El modelo se encargará de cambiarlo a True si es un INGRESO válido
        validated_data['session_consumida'] = False
        
        # Asignar fecha y hora actual si no vienen (por seguridad)
        if 'fecha_hora' not in validated_data:
            validated_data['fecha_hora'] = timezone.now()
            
        return super().create(validated_data)


class RegistroAsistenciaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para vista individual de un registro.
    Muestra información completa anidada.
    """
    usuario = UsuarioBaseSerializer(read_only=True)
    membresia = MembresiaBaseSerializer(read_only=True)
    registrado_por_info = UsuarioBaseSerializer(source='registrado_por', read_only=True)
    
    tipo_display = serializers.CharField(source='get_tipo_registro_display', read_only=True)
    metodo_display = serializers.CharField(source='get_metodo_ingreso_display', read_only=True)

    class Meta:
        model = RegistroAsistencia
        fields = [
            'id', 'usuario', 'membresia', 'registrado_por', 'registrado_por_info',
            'fecha_hora', 'fecha', 'tipo_registro', 'tipo_display',
            'metodo_ingreso', 'metodo_display',
            'es_consumo_sesion', 'session_consumida', 'observaciones'
        ]


class ResumenAsistenciaDiariaSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar resúmenes de asistencia por día (para reportes).
    """
    class Meta:
        model = ResumenAsistenciaDiaria
        fields = [
            'fecha', 'total_ingresos', 'total_sesiones_consumidas', 
            'usuarios_unicos', 'membresias_utilizadas'
        ]


class RegistroAsistenciaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para correcciones administrativas (ej. corregir hora u observaciones).
    MUY restrictivo: NO permite cambiar usuario, membresía ni estado de consumo de sesión.
    """
    class Meta:
        model = RegistroAsistencia
        fields = ['observaciones', 'metodo_ingreso']