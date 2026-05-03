from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.usuarios.models import Usuario
from apps.membresias.models import Membresia

class RegistroAsistencia(models.Model):
    """
    Modelo de registro de asistencia para controlar el ingreso de usuarios al centro.
    Cada registro representa una sesión de entrenamiento y consume automáticamente
    una unidad de la membresía activa del usuario.
    """
    
    METODO_INGRESO_CHOICES = [
        ('MANUAL', 'Manual (Personal)'),
        ('AUTOMATICO', 'Automático (Sistema)'),
        ('QR', 'Código QR'),
    ]
    
    ESTADO_CHOICES = [
        ('INGRESO', 'Ingreso'),
        ('SALIDA', 'Salida'),
    ]

    # 🔗 Relaciones
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='asistencias',
        verbose_name='usuario'
    )
    membresia = models.ForeignKey(
        Membresia,
        on_delete=models.CASCADE,
        related_name='asistencias',
        verbose_name='membresía',
        help_text='Membresía activa al momento del registro.'
    )
    
    # 📅 Fecha y hora
    fecha_hora = models.DateTimeField(
        'fecha y hora',
        default=timezone.now,
        help_text='Fecha y hora del registro de asistencia.'
    )
    fecha = models.DateField(
        'fecha',
        auto_now_add=True,
        editable=False,
        help_text='Fecha del registro (para índices y filtros rápidos).'
    )
    
    # 👤 Registro
    registrado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asistencias_registradas',
        verbose_name='registrado por',
        help_text='Personal que registró la asistencia (si aplica).'
    )
    
    # 📋 Información adicional
    metodo_ingreso = models.CharField(
        'método de ingreso',
        max_length=15,
        choices=METODO_INGRESO_CHOICES,
        default='MANUAL',
        help_text='Cómo se registró el ingreso.'
    )
    tipo_registro = models.CharField(
        'tipo de registro',
        max_length=10,
        choices=ESTADO_CHOICES,
        default='INGRESO',
        help_text='Indica si es ingreso o salida.'
    )
    observaciones = models.TextField(
        'observaciones',
        blank=True,
        null=True,
        help_text='Notas adicionales sobre el registro.'
    )
    
    # ⚙️ Control
    es_consumo_sesion = models.BooleanField(
        '¿consume sesión?',
        default=True,
        help_text='Indica si este registro consume una sesión de la membresía.'
    )
    session_consumida = models.BooleanField(
        'sesión consumida',
        default=False,
        help_text='Confirma si ya se descontó la sesión de la membresía.'
    )

    class Meta:
        verbose_name = 'registro de asistencia'
        verbose_name_plural = 'registros de asistencia'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['usuario', 'fecha'], name='idx_asist_usuario_fecha'),
            models.Index(fields=['membresia', 'fecha'], name='idx_asist_membresia_fecha'),
            models.Index(fields=['fecha'], name='idx_asist_fecha'),
            models.Index(fields=['tipo_registro'], name='idx_asist_tipo'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'fecha', 'tipo_registro'],
                name='unique_asistencia_usuario_fecha_tipo',
                violation_error_message='Ya existe un registro de este tipo para el usuario en esta fecha.'
            ),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')} ({self.tipo_registro})"

    def clean(self):
        """Validaciones antes de guardar el registro."""
        if self.tipo_registro == 'INGRESO' and self.membresia:
            # Validar que la membresía pertenezca al usuario
            if self.membresia.usuario != self.usuario:
                raise ValidationError({
                    'membresia': 'La membresía no pertenece al usuario especificado.'
                })
            
            # Validar que la membresía esté activa
            if not self.membresia.puede_asistir():
                raise ValidationError({
                    'membresia': f'La membresía no permite el ingreso. Estado: {self.membresia.estado}. '
                                f'Vencimiento: {self.membresia.fecha_vencimiento}.'
                })

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para:
        1. Validar datos
        2. Consumir sesión automáticamente si es un ingreso
        3. Actualizar fecha automáticamente
        """
        # Ejecutar validaciones
        self.full_clean()
        
        # Si es un ingreso y debe consumir sesión
        if self.tipo_registro == 'INGRESO' and self.es_consumo_sesion and not self.session_consumida:
            if self.membresia and self.membresia.puede_asistir():
                self.membresia.consumir_sesion()
                self.session_consumida = True
        
        # Actualizar fecha si no existe
        if not self.fecha:
            self.fecha = timezone.now().date()
        
        super().save(*args, **kwargs)

    def to_dict(self):
        """Retorna un diccionario con la información del registro."""
        return {
            'id': self.id,
            'usuario': {
                'id': self.usuario.id,
                'nombre': f"{self.usuario.first_name} {self.usuario.last_name}",
                'email': self.usuario.email,
            },
            'membresia': {
                'id': self.membresia.id,
                'tipo': self.membresia.tipo,
                'estado': self.membresia.estado,
            } if self.membresia else None,
            'fecha_hora': self.fecha_hora.isoformat(),
            'fecha': self.fecha.isoformat(),
            'tipo_registro': self.tipo_registro,
            'metodo_ingreso': self.metodo_ingreso,
            'registrado_por': str(self.registrado_por) if self.registrado_por else None,
            'observaciones': self.observaciones,
        }


class ResumenAsistenciaDiaria(models.Model):
    """
    Modelo para almacenar resúmenes diarios de asistencia.
    Útil para reportes rápidos y estadísticas sin tener que hacer
    agregaciones complejas sobre la tabla de registros.
    """
    fecha = models.DateField('fecha', unique=True)
    total_ingresos = models.PositiveIntegerField('total ingresos', default=0)
    total_sesiones_consumidas = models.PositiveIntegerField('total sesiones', default=0)
    usuarios_unicos = models.PositiveIntegerField('usuarios únicos', default=0)
    membresias_utilizadas = models.PositiveIntegerField('membresías usadas', default=0)
    
    class Meta:
        verbose_name = 'resumen de asistencia diaria'
        verbose_name_plural = 'resúmenes de asistencia diaria'
        ordering = ['-fecha']

    def __str__(self):
        return f"Resumen {self.fecha} - {self.total_ingresos} ingresos"

    def calcular_resumen(self):
        """Calcula y actualiza las estadísticas del día."""
        registros = RegistroAsistencia.objects.filter(
            fecha=self.fecha,
            tipo_registro='INGRESO'
        )
        
        self.total_ingresos = registros.count()
        self.total_sesiones_consumidas = registros.filter(session_consumida=True).count()
        self.usuarios_unicos = registros.values('usuario').distinct().count()
        self.membresias_utilizadas = registros.values('membresia').distinct().count()
        
        return self

    def save(self, *args, **kwargs):
        """Calcula automáticamente el resumen antes de guardar."""
        if not self.pk:  # Solo calcular si es nuevo
            self.calcular_resumen()
        super().save(*args, **kwargs)