from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from apps.membresias.models import Membresia, HistorialMembresia
from apps.usuarios.serializers import UsuarioBaseSerializer


class MembresiaBaseSerializer(serializers.ModelSerializer):
    """
    Serializer base para mostrar información básica de la membresía.
    Usado en listados y relaciones anidadas.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    dias_restantes = serializers.SerializerMethodField()
    sesiones_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Membresia
        fields = [
            'id', 'usuario', 'usuario_nombre', 'tipo', 'tipo_display',
            'precio', 'fecha_inicio', 'fecha_vencimiento', 'estado', 
            'estado_display', 'dias_restantes', 'sesiones_totales', 
            'sesiones_consumidas', 'sesiones_disponibles'
        ]
        read_only_fields = ['id', 'fecha_compra']

    def get_dias_restantes(self, obj):
        return obj.get_dias_restantes()

    def get_sesiones_disponibles(self, obj):
        disponibles = obj.sesiones_disponibles()
        return 'Ilimitadas' if disponibles == float('inf') else disponibles


class MembresiaCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas membresías.
    Incluye validación de fechas y cálculo automático de vencimiento.
    """
    fecha_vencimiento = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Membresia
        fields = [
            'usuario', 'tipo', 'precio', 'fecha_inicio', 
            'fecha_vencimiento', 'sesiones_totales', 'observaciones'
        ]

    def validate(self, attrs):
        usuario = attrs.get('usuario')
        
        # Verificar si ya existe una membresía activa
        if usuario:
            membresia_activa = Membresia.objects.filter(usuario=usuario, estado='ACTIVA').exists()
            if membresia_activa:
                raise serializers.ValidationError({
                    "usuario": "Este cliente ya tiene una membresía activa. No se puede asignar otra."
                })

        tipo = attrs.get('tipo')
        precio = attrs.get('precio')
        fecha_inicio = attrs.get('fecha_inicio', timezone.now().date())
        fecha_vencimiento = attrs.get('fecha_vencimiento')
        sesiones_totales = attrs.get('sesiones_totales', 0)

        # Validar precio
        if precio < 0:
            raise serializers.ValidationError({
                "precio": "El precio no puede ser negativo."
            })

        # Validar sesiones totales
        if sesiones_totales < 0:
            raise serializers.ValidationError({
                "sesiones_totales": "Las sesiones totales no pueden ser negativas."
            })

        # Validar fecha de inicio no sea en el pasado
        if fecha_inicio < timezone.now().date():
            raise serializers.ValidationError({
                "fecha_inicio": "La fecha de inicio no puede ser en el pasado."
            })

        # Si no se proporciona fecha_vencimiento, calcularla automáticamente
        if not fecha_vencimiento:
            dias_map = {
                'MENSUAL': 30,
                'BIMESTRAL': 60,
                'TRIMESTRAL': 90,
                'SEMESTRAL': 180,
            }
            dias = dias_map.get(tipo, 30)
            fecha_vencimiento = fecha_inicio + timedelta(days=dias)
            attrs['fecha_vencimiento'] = fecha_vencimiento

        # Validar que fecha_vencimiento sea posterior a fecha_inicio
        if fecha_vencimiento <= fecha_inicio:
            raise serializers.ValidationError({
                "fecha_vencimiento": "La fecha de vencimiento debe ser posterior a la fecha de inicio."
            })

        return attrs

    def create(self, validated_data):
        # Asegurar que fecha_inicio sea solo DATE, no DATETIME
        if 'fecha_inicio' in validated_data:
            fecha = validated_data['fecha_inicio']
            # Si viene como datetime, extraemos solo la fecha
            if hasattr(fecha, 'date'):
                validated_data['fecha_inicio'] = fecha.date()
        
        # Si no se envió fecha_inicio, usar hoy
        if 'fecha_inicio' not in validated_data:
            validated_data['fecha_inicio'] = timezone.now().date()
            
        # La membresía se crea con estado ACTIVA por defecto
        return super().create(validated_data)


class MembresiaDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para mostrar toda la información de una membresía.
    Incluye datos calculados y relaciones completas.
    """
    usuario = UsuarioBaseSerializer(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    dias_restantes = serializers.SerializerMethodField()
    sesiones_disponibles = serializers.SerializerMethodField()
    puede_asistir = serializers.SerializerMethodField()

    class Meta:
        model = Membresia
        fields = [
            'id', 'usuario', 'tipo', 'tipo_display', 'precio',
            'fecha_inicio', 'fecha_vencimiento', 'fecha_compra',
            'estado', 'estado_display', 'dias_restantes',
            'sesiones_totales', 'sesiones_consumidas', 'sesiones_disponibles',
            'puede_asistir', 'observaciones'
        ]
        read_only_fields = ['id', 'fecha_compra', 'estado']

    def get_dias_restantes(self, obj):
        return obj.get_dias_restantes()

    def get_sesiones_disponibles(self, obj):
        disponibles = obj.sesiones_disponibles()
        return 'Ilimitadas' if disponibles == float('inf') else disponibles

    def get_puede_asistir(self, obj):
        return obj.puede_asistir()


class MembresiaUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar membresías existentes.
    Permite modificar ciertos campos pero mantiene otros como read-only.
    """
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado = serializers.CharField(read_only=True)  # El estado se calcula automáticamente

    class Meta:
        model = Membresia
        fields = [
            'tipo', 'tipo_display', 'precio', 'fecha_vencimiento',
            'sesiones_totales', 'sesiones_consumidas', 'observaciones', 'estado'
        ]
        read_only_fields = ['estado', 'sesiones_consumidas']

    def validate(self, attrs):
        precio = attrs.get('precio')
        sesiones_totales = attrs.get('sesiones_totales')

        if precio is not None and precio < 0:
            raise serializers.ValidationError({
                "precio": "El precio no puede ser negativo."
            })

        if sesiones_totales is not None and sesiones_totales < 0:
            raise serializers.ValidationError({
                "sesiones_totales": "Las sesiones totales no pueden ser negativas."
            })

        # Validar que no se puedan modificar sesiones_consumidas manualmente
        # (solo se actualizan automáticamente al registrar asistencia)
        if 'sesiones_consumidas' in attrs:
            raise serializers.ValidationError({
                "sesiones_consumidas": "Las sesiones consumidas no se pueden modificar manualmente."
            })

        return attrs

    def update(self, instance, validated_data):
        # Actualizar campos permitidos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Recalcular estado después de actualizar
        instance.actualizar_estado()
        instance.save(update_fields=['estado'])
        
        return instance


class MembresiaResumenSerializer(serializers.ModelSerializer):
    """
    Serializer para resúmenes y reportes.
    Información esencial para listados rápidos.
    """
    usuario_email = serializers.EmailField(source='usuario.email', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    dias_restantes = serializers.SerializerMethodField()
    porcentaje_consumo = serializers.SerializerMethodField()

    class Meta:
        model = Membresia
        fields = [
            'id', 'usuario', 'usuario_email', 'usuario_nombre',
            'tipo', 'tipo_display', 'estado', 'estado_display',
            'fecha_inicio', 'fecha_vencimiento', 'dias_restantes',
            'sesiones_totales', 'sesiones_consumidas', 'porcentaje_consumo',
            'precio'
        ]

    def get_dias_restantes(self, obj):
        return obj.get_dias_restantes()

    def get_porcentaje_consumo(self, obj):
        if obj.sesiones_totales == 0:  # Ilimitadas
            return 0.0
        if obj.sesiones_totales == 0:
            return 0.0
        return round((obj.sesiones_consumidas / obj.sesiones_totales) * 100, 2)


class MembresiaEstadisticasSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de membresías.
    No está ligado directamente al modelo, sino que agrega datos.
    """
    total_membresias = serializers.IntegerField()
    membresias_activas = serializers.IntegerField()
    membresias_vencidas = serializers.IntegerField()
    membresias_por_vencer_7_dias = serializers.IntegerField()
    membresias_por_vencer_30_dias = serializers.IntegerField()
    ingreso_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    promedio_precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    membresias_por_tipo = serializers.DictField()


class HistorialMembresiaSerializer(serializers.ModelSerializer):
    """
    Serializer para el historial de cambios de estado de membresías.
    """
    membresia_info = MembresiaBaseSerializer(source='membresia', read_only=True)
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model = HistorialMembresia
        fields = [
            'id', 'membresia', 'membresia_info', 'fecha_cambio',
            'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'motivo'
        ]
        read_only_fields = ['id', 'fecha_cambio']


class MembresiaConHistorialSerializer(MembresiaDetailSerializer):
    """
    Serializer que incluye la membresía detallada con su historial de cambios.
    """
    historial_cambios = serializers.SerializerMethodField()

    class Meta(MembresiaDetailSerializer.Meta):
        fields = MembresiaDetailSerializer.Meta.fields + ['historial_cambios']

    def get_historial_cambios(self, obj):
        historial = obj.historial.all()[:10]  # Últimos 10 cambios
        return HistorialMembresiaSerializer(historial, many=True).data