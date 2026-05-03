from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.usuarios.models import Usuario


class UsuarioBaseSerializer(serializers.ModelSerializer):
    """
    Serializer base para mostrar información básica del usuario.
    Usado en listados y relaciones anidadas.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'nombre_completo', 'telefono', 'role', 'role_display',
            'is_active', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class UsuarioRegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios.
    Incluye validación de contraseña y campos requeridos.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
        help_text='La contraseña debe tener al menos 8 caracteres.'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text='Confirme la contraseña.'
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'first_name', 'last_name', 'telefono', 
            'role', 'password', 'password_confirm',
            'peso', 'altura'
        ]

    def validate(self, attrs):
        # Validar que las contraseñas coincidan
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        
        # Validar que si se proporciona peso, también se proporcione altura (para calcular IMC)
        if attrs.get('peso') and not attrs.get('altura'):
            raise serializers.ValidationError({
                "altura": "La altura es requerida si se proporciona el peso."
            })
        if attrs.get('altura') and not attrs.get('peso'):
            raise serializers.ValidationError({
                "peso": "El peso es requerido si se proporciona la altura."
            })
        
        # Validar peso y altura si se proporcionan
        peso = attrs.get('peso')
        altura = attrs.get('altura')
        
        if peso and peso < 0.1:
            raise serializers.ValidationError({
                "peso": "El peso debe ser mayor a 0.1 kg."
            })
        
        if altura and altura < 50.0:
            raise serializers.ValidationError({
                "altura": "La altura debe ser mayor a 50 cm."
            })

        return attrs

    def create(self, validated_data):
        # Eliminar password_confirm antes de crear
        validated_data.pop('password_confirm')
        
        # Extraer contraseña
        password = validated_data.pop('password')
        
        # Calcular IMC si se proporcionan peso y altura
        imc = None
        if validated_data.get('peso') and validated_data.get('altura'):
            altura_m = validated_data['altura'] / 100
            imc = round(validated_data['peso'] / (altura_m ** 2), 2)
            validated_data['imc'] = imc
        
        # Usar create_user para hashear la contraseña
        usuario = Usuario.objects.create_user(
            password=password,  # Ahora se hashea automáticamente
            **validated_data
        )
        
        return usuario


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para que el usuario gestione su propio perfil.
    Permite actualizar datos personales y ficha física.
    """
    nombre_completo = serializers.SerializerMethodField(read_only=True)
    imc = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'nombre_completo', 'telefono', 'role',
            'peso', 'altura', 'imc',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'role', 'imc', 
            'date_joined', 'last_login', 'is_active'
        ]

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate(self, attrs):
        peso = attrs.get('peso')
        altura = attrs.get('altura')
        
        # Si se actualiza peso o altura, validar
        if peso is not None and peso < 0.1:
            raise serializers.ValidationError({
                "peso": "El peso debe ser mayor a 0.1 kg."
            })
        
        if altura is not None and altura < 50.0:
            raise serializers.ValidationError({
                "altura": "La altura debe ser mayor a 50 cm."
            })

        return attrs

    def update(self, instance, validated_data):
        # Si se actualizó peso o altura, recalcular IMC
        peso_actualizado = 'peso' in validated_data
        altura_actualizada = 'altura' in validated_data
        
        if peso_actualizado or altura_actualizada:
            peso = validated_data.get('peso', instance.peso)
            altura = validated_data.get('altura', instance.altura)
            
            if peso and altura:
                altura_m = altura / 100
                instance.imc = round(peso / (altura_m ** 2), 2)
        
        return super().update(instance, validated_data)


class UsuarioAdminSerializer(serializers.ModelSerializer):
    """
    Serializer completo para administración por parte del propietario/personal.
    Incluye todos los campos y permite gestión completa.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    imc = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'nombre_completo', 'telefono', 'role', 'role_display',
            'peso', 'altura', 'imc',
            'is_active', 'is_staff', 'is_superuser',
            'date_joined', 'last_login',
            'groups', 'user_permissions'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'imc']

    def get_nombre_completo(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def validate(self, attrs):
        peso = attrs.get('peso')
        altura = attrs.get('altura')
        
        if peso is not None and peso < 0.1:
            raise serializers.ValidationError({
                "peso": "El peso debe ser mayor a 0.1 kg."
            })
        
        if altura is not None and altura < 50.0:
            raise serializers.ValidationError({
                "altura": "La altura debe ser mayor a 50 cm."
            })

        return attrs


class UsuarioCambioPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambio de contraseña.
    """
    current_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        user = self.context['request'].user
        
        # Validar contraseña actual
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                "current_password": "La contraseña actual es incorrecta."
            })
        
        # Validar que las nuevas contraseñas coincidan
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "Las nuevas contraseñas no coinciden."
            })
        
        # Validar que la nueva contraseña no sea igual a la actual
        if user.check_password(attrs['new_password']):
            raise serializers.ValidationError({
                "new_password": "La nueva contraseña debe ser diferente a la actual."
            })

        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UsuarioUpdateFichaFisicaSerializer(serializers.ModelSerializer):
    """
    Serializer específico para actualizar solo la ficha física.
    Usado cuando el usuario solo quiere actualizar peso/altura.
    """
    imc = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = Usuario
        fields = ['peso', 'altura', 'imc']

    def validate(self, attrs):
        peso = attrs.get('peso')
        altura = attrs.get('altura')
        
        if peso is not None and peso < 0.1:
            raise serializers.ValidationError({
                "peso": "El peso debe ser mayor a 0.1 kg."
            })
        
        if altura is not None and altura < 50.0:
            raise serializers.ValidationError({
                "altura": "La altura debe ser mayor a 50 cm."
            })

        return attrs

    def update(self, instance, validated_data):
        # Calcular IMC automáticamente
        peso = validated_data.get('peso', instance.peso)
        altura = validated_data.get('altura', instance.altura)
        
        if peso and altura:
            altura_m = altura / 100
            instance.imc = round(peso / (altura_m ** 2), 2)
        
        return super().update(instance, validated_data)