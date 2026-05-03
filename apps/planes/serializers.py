from rest_framework import serializers
from apps.planes.models import PlanEntrenamiento, Ejercicio, HistorialPlanUsuario
from apps.usuarios.serializers import UsuarioBaseSerializer


class EjercicioSerializer(serializers.ModelSerializer):
    """
    Serializer para ejercicios dentro de un plan.
    """
    descanso_formateado = serializers.CharField(source='get_descanso_formatted', read_only=True)

    class Meta:
        model = Ejercicio
        fields = [
            'id', 'nombre', 'descripcion', 'series', 'repeticiones',
            'descanso_segundos', 'descanso_formateado', 'peso_sugerido',
            'orden', 'area_especifica', 'observaciones', 'activo'
        ]


class EjercicioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear/actualizar ejercicios (permite write).
    """
    class Meta:
        model = Ejercicio
        fields = [
            'id', 'nombre', 'descripcion', 'series', 'repeticiones',
            'descanso_segundos', 'peso_sugerido', 'orden',
            'area_especifica', 'observaciones', 'activo'
        ]


class PlanEntrenamientoListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados de planes.
    """
    creado_por_info = UsuarioBaseSerializer(source='creado_por', read_only=True)
    area_display = serializers.CharField(source='get_area_muscular_display', read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_dificultad_display', read_only=True)
    total_ejercicios = serializers.IntegerField(read_only=True)
    usuarios_count = serializers.IntegerField(source='usuarios_asignados.count', read_only=True)

    class Meta:
        model = PlanEntrenamiento
        fields = [
            'id', 'nombre', 'descripcion', 'area_muscular', 'area_display',
            'nivel_dificultad', 'nivel_display', 'duracion_semanas',
            'creado_por', 'creado_por_info', 'fecha_creacion',
            'activo', 'total_ejercicios', 'usuarios_count'
        ]


class PlanEntrenamientoDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para ver un plan con sus ejercicios.
    """
    creado_por_info = UsuarioBaseSerializer(source='creado_por', read_only=True)
    area_display = serializers.CharField(source='get_area_muscular_display', read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_dificultad_display', read_only=True)
    ejercicios = EjercicioSerializer(many=True, read_only=True)
    usuarios_asignados_info = UsuarioBaseSerializer(source='usuarios_asignados', many=True, read_only=True)

    class Meta:
        model = PlanEntrenamiento
        fields = [
            'id', 'nombre', 'descripcion', 'area_muscular', 'area_display',
            'nivel_dificultad', 'nivel_display', 'duracion_semanas',
            'creado_por', 'creado_por_info', 'fecha_creacion', 'fecha_actualizacion',
            'activo', 'observaciones_generales', 'ejercicios', 'usuarios_asignados',
            'usuarios_asignados_info'
        ]


class PlanEntrenamientoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear planes con ejercicios anidados.
    Permite crear el plan y sus ejercicios en una sola petición.
    """
    ejercicios = EjercicioCreateSerializer(many=True, required=False)

    class Meta:
        model = PlanEntrenamiento
        fields = [
            'id', 'nombre', 'descripcion', 'area_muscular',
            'nivel_dificultad', 'duracion_semanas', 'observaciones_generales',
            'activo', 'usuarios_asignados', 'ejercicios'
        ]

    def create(self, validated_data):
        ejercicios_data = validated_data.pop('ejercicios', [])
        plan = PlanEntrenamiento.objects.create(**validated_data)
        
        for ejercicio_data in ejercicios_data:
            Ejercicio.objects.create(plan=plan, **ejercicio_data)
        
        return plan

    def update(self, instance, validated_data):
        ejercicios_data = validated_data.pop('ejercicios', None)
        
        # Actualizar campos del plan
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si se enviaron ejercicios, actualizarlos
        if ejercicios_data is not None:
            # Eliminar ejercicios existentes (simplificación)
            instance.ejercicios.all().delete()
            for ejercicio_data in ejercicios_data:
                Ejercicio.objects.create(plan=instance, **ejercicio_data)
        
        return instance


class HistorialPlanUsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para el historial de planes por usuario.
    """
    plan_info = PlanEntrenamientoListSerializer(source='plan', read_only=True)
    usuario_info = UsuarioBaseSerializer(source='usuario', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = HistorialPlanUsuario
        fields = [
            'id', 'usuario', 'usuario_info', 'plan', 'plan_info',
            'fecha_asignacion', 'fecha_finalizacion', 'estado',
            'estado_display', 'progreso_porcentaje', 'observaciones_seguimiento'
        ]
        read_only_fields = ['id', 'fecha_asignacion', 'progreso_porcentaje']


class MisPlanesSerializer(serializers.ModelSerializer):
    """
    Serializer para que el cliente vea SUS planes asignados.
    """
    area_display = serializers.CharField(source='get_area_muscular_display', read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_dificultad_display', read_only=True)
    ejercicios = EjercicioSerializer(many=True, read_only=True)
    historial = serializers.SerializerMethodField()

    class Meta:
        model = PlanEntrenamiento
        fields = [
            'id', 'nombre', 'descripcion', 'area_muscular', 'area_display',
            'nivel_dificultad', 'nivel_display', 'duracion_semanas',
            'fecha_creacion', 'ejercicios', 'historial'
        ]

    def get_historial(self, obj):
        # Obtener el historial del usuario actual con este plan
        request = self.context.get('request')
        if request:
            historial = HistorialPlanUsuario.objects.filter(
                usuario=request.user,
                plan=obj
            ).first()
            if historial:
                return {
                    'estado': historial.estado,
                    'progreso': historial.progreso_porcentaje,
                    'fecha_asignacion': historial.fecha_asignacion
                }
        return None