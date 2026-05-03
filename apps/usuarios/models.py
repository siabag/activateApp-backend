from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator

class UsuarioManager(BaseUserManager):
    """Manager personalizado para el modelo Usuario con email como identificador principal"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'PROPIETARIO')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Un superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Un superusuario debe tener is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo personalizado de usuario para el sistema Activate.
    Usa email como identificador principal en lugar de username.
    """
    ROLE_CHOICES = [
        ('PROPIETARIO', 'Propietario'),
        ('PERSONAL', 'Personal'),
        ('CLIENTE', 'Cliente'),
    ]

    # 🔐 Identificación y contacto
    email = models.EmailField('correo electrónico', unique=True)
    first_name = models.CharField('nombres', max_length=150)
    last_name = models.CharField('apellidos', max_length=150)
    telefono = models.CharField('teléfono', max_length=15, blank=True, null=True)
    role = models.CharField('rol en el sistema', max_length=15, choices=ROLE_CHOICES, default='CLIENTE')

    # 📏 Ficha física básica
    peso = models.DecimalField(
        'peso (kg)', max_digits=5, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(0.1)],
        help_text='Peso en kilogramos.'
    )
    altura = models.DecimalField(
        'altura (cm)', max_digits=5, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(50.0)],
        help_text='Altura en centímetros.'
    )
    imc = models.DecimalField(
        'Índice de Masa Corporal', max_digits=5, decimal_places=2,
        blank=True, null=True, editable=False,
        help_text='Se calcula automáticamente al guardar peso y altura.'
    )

    # ⚙️ Campos requeridos por Django
    is_active = models.BooleanField('activo', default=True)
    is_staff = models.BooleanField('es personal', default=False)
    date_joined = models.DateTimeField('fecha de registro', auto_now_add=True)

    # Configurar manager y campo de identificación
    objects = UsuarioManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['email'], name='idx_usuario_email'),
            models.Index(fields=['role'], name='idx_usuario_role'),
        ]

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name or self.email} ({self.get_role_display()})"

    def calcular_imc(self):
        """Calcula el IMC basado en peso (kg) y altura (cm)."""
        if self.peso and self.altura:
            altura_m = self.altura / 100
            return round(self.peso / (altura_m ** 2), 2)
        return None

    def save(self, *args, **kwargs):
        """Sobrescribe save para actualizar el IMC automáticamente."""
        self.imc = self.calcular_imc()
        super().save(*args, **kwargs)