from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.usuarios.models import Usuario
from datetime import timedelta

class Membresia(models.Model):
    """
    Modelo de membresías para el centro Activate.
    Controla el tipo, vigencia, estado y consumo de sesiones por usuario.
    """
    TIPO_CHOICES = [
        ('MENSUAL', 'Mensual (30 días)'),
        ('BIMESTRAL', 'Bimestral (60 días)'),
        ('TRIMESTRAL', 'Trimestral (90 días)'),
        ('SEMESTRAL', 'Semestral (180 días)'),
    ]

    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('VENCIDA', 'Vencida'),
    ]

    # 🔗 Relación con Usuario (1:N)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='membresias',
        verbose_name='usuario'
    )

    # 📋 Información de la membresía
    tipo = models.CharField(
        'tipo de membresía',
        max_length=20,
        choices=TIPO_CHOICES,
        help_text='Duración de la membresía.'
    )
    precio = models.DecimalField(
        'precio',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Valor pagado por la membresía en pesos colombianos.'
    )

    # 📅 Fechas importantes
    fecha_inicio = models.DateField(
        'fecha de inicio',
        default=timezone.now,
        help_text='Fecha en que inicia la vigencia de la membresía.'
    )
    fecha_vencimiento = models.DateField(
        'fecha de vencimiento',
        help_text='Fecha en que expira la membresía.'
    )
    fecha_compra = models.DateTimeField(
        'fecha de compra',
        auto_now_add=True,
        help_text='Fecha y hora del registro de la membresía.'
    )

    # 📊 Estado y control
    estado = models.CharField(
        'estado',
        max_length=10,
        choices=ESTADO_CHOICES,
        default='ACTIVA',
        help_text='Estado actual de la membresía.'
    )
    sesiones_totales = models.PositiveIntegerField(
        'sesiones totales',
        default=0,
        help_text='Número total de sesiones permitidas (0 = ilimitadas).'
    )
    sesiones_consumidas = models.PositiveIntegerField(
        'sesiones consumidas',
        default=0,
        help_text='Número de sesiones ya utilizadas.'
    )

    # 📝 Observaciones
    observaciones = models.TextField(
        'observaciones',
        blank=True,
        null=True,
        help_text='Notas adicionales sobre la membresía.'
    )

    class Meta:
        verbose_name = 'membresía'
        verbose_name_plural = 'membresías'
        ordering = ['-fecha_inicio', 'usuario']
        indexes = [
            models.Index(fields=['usuario', 'estado'], name='idx_memb_usuario_estado'),
            models.Index(fields=['fecha_vencimiento'], name='idx_memb_vencimiento'),
            models.Index(fields=['estado'], name='idx_memb_estado'),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_display()} ({self.estado})"

    def get_dias_restantes(self):
        """Calcula los días restantes hasta el vencimiento."""
        if self.estado == 'VENCIDA':
            return 0
        hoy = timezone.now().date()
        dias_restantes = (self.fecha_vencimiento - hoy).days
        return max(0, dias_restantes)

    def sesiones_disponibles(self):
        """Retorna el número de sesiones disponibles."""
        if self.sesiones_totales == 0:  # Ilimitadas
            return float('inf')
        return self.sesiones_totales - self.sesiones_consumidas

    def puede_asistir(self):
        """
        Verifica si el usuario puede asistir basado en:
        1. Estado activo
        2. Fecha de vencimiento
        3. Sesiones disponibles
        """
        if self.estado != 'ACTIVA':
            return False
        if timezone.now().date() > self.fecha_vencimiento:
            return False
        if self.sesiones_totales > 0 and self.sesiones_consumidas >= self.sesiones_totales:
            return False
        return True

    def consumir_sesion(self):
        """Incrementa el contador de sesiones consumidas."""
        if self.puede_asistir():
            self.sesiones_consumidas += 1
            self.save(update_fields=['sesiones_consumidas'])
            return True
        return False

    def calcular_fecha_vencimiento(self):
        """Calcula la fecha de vencimiento basada en el tipo de membresía."""
        dias = {
            'MENSUAL': 30,
            'BIMESTRAL': 60,
            'TRIMESTRAL': 90,
            'SEMESTRAL': 180,
        }
        return self.fecha_inicio + timedelta(days=dias.get(self.tipo, 30))

    def actualizar_estado(self):
        """
        Actualiza automáticamente el estado de la membresía.
        Debe llamarse antes de guardar o mediante signals/celery.
        """
        hoy = timezone.now().date()
        
        # Verificar si venció por fecha
        if hoy > self.fecha_vencimiento:
            self.estado = 'VENCIDA'
        else:
            # Verificar si agotó sesiones
            if self.sesiones_totales > 0 and self.sesiones_consumidas >= self.sesiones_totales:
                self.estado = 'VENCIDA'
            else:
                self.estado = 'ACTIVA'
        
        return self.estado

    def save(self, *args, **kwargs):
        """
        Sobrescribe save para:
        1. Calcular fecha de vencimiento si es nueva
        2. Actualizar estado automáticamente
        """
        # Si es una nueva membresía, calcular fecha de vencimiento
        if not self.pk and not self.fecha_vencimiento:
            self.fecha_vencimiento = self.calcular_fecha_vencimiento()
        
        # Actualizar estado
        self.actualizar_estado()
        
        super().save(*args, **kwargs)

    def to_dict(self):
        """Retorna un diccionario con la información esencial de la membresía."""
        return {
            'id': self.id,
            'usuario': str(self.usuario),
            'tipo': self.tipo,
            'precio': float(self.precio),
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_vencimiento': self.fecha_vencimiento.isoformat(),
            'estado': self.estado,
            'dias_restantes': self.get_dias_restantes(),
            'sesiones_disponibles': self.sesiones_disponibles() if self.sesiones_totales > 0 else 'Ilimitadas',
        }


class HistorialMembresia(models.Model):
    """
    Modelo para mantener un historial de todas las membresías compradas.
    Útil para reportes, análisis de retención y auditoría.
    """
    membresia = models.ForeignKey(
        Membresia,
        on_delete=models.CASCADE,
        related_name='historial'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    estado_anterior = models.CharField(max_length=10, choices=Membresia.ESTADO_CHOICES)
    estado_nuevo = models.CharField(max_length=10, choices=Membresia.ESTADO_CHOICES)
    motivo = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Motivo del cambio de estado (vencimiento, agotamiento de sesiones, etc.)'
    )

    class Meta:
        verbose_name = 'historial de membresía'
        verbose_name_plural = 'historial de membresías'
        ordering = ['-fecha_cambio']

    def __str__(self):
        return f"{self.membresia} - {self.estado_anterior} → {self.estado_nuevo}"
    