from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.usuarios.models import Usuario

class PlanEntrenamiento(models.Model):
    """
    Modelo de planes de entrenamiento personalizados.
    Permite crear, asignar y gestionar planes con ejercicios específicos
    para cada usuario del centro Activate.
    """
    AREA_MUSCULAR_CHOICES = [
        ('PECHO', 'Pecho'),
        ('ESPALDA', 'Espalda'),
        ('PIERNAS', 'Piernas'),
        ('HOMBROS', 'Hombros'),
        ('BRAZOS', 'Brazos (Bíceps/Tríceps)'),
        ('ABDOMEN', 'Abdomen/Core'),
        ('GLUTEOS', 'Glúteos'),
        ('CARDIO', 'Cardiovascular'),
        ('Cuerpo_COMPLETO', 'Cuerpo Completo'),
        ('OTRO', 'Otro'),
    ]

    # 📋 Información del plan
    nombre = models.CharField(
        'nombre del plan',
        max_length=100,
        help_text='Nombre descriptivo del plan de entrenamiento.'
    )
    descripcion = models.TextField(
        'descripción',
        blank=True,
        null=True,
        help_text='Descripción general del plan y sus objetivos.'
    )
    area_muscular = models.CharField(
        'área muscular objetivo',
        max_length=20,
        choices=AREA_MUSCULAR_CHOICES,
        help_text='Grupo muscular principal que trabaja el plan.'
    )
    
    # 📅 Fechas
    fecha_creacion = models.DateTimeField(
        'fecha de creación',
        auto_now_add=True,
        help_text='Fecha en que se creó el plan.'
    )
    fecha_actualizacion = models.DateTimeField(
        'fecha de última actualización',
        auto_now=True,
        help_text='Fecha de la última modificación del plan.'
    )
    
    # 👤 Creación y asignación
    creado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planes_creados',
        verbose_name='creado por',
        help_text='Personal/entrenador que creó el plan.'
    )
    usuarios_asignados = models.ManyToManyField(
        Usuario,
        related_name='planes_asignados',
        verbose_name='usuarios asignados',
        help_text='Usuarios que tienen asignado este plan.',
        blank=True
    )
    
    # ⚙️ Configuración
    activo = models.BooleanField(
        'activo',
        default=True,
        help_text='Indica si el plan está activo y disponible para asignar.'
    )
    nivel_dificultad = models.CharField(
        'nivel de dificultad',
        max_length=20,
        choices=[
            ('PRINCIPIANTE', 'Principiante'),
            ('INTERMEDIO', 'Intermedio'),
            ('AVANZADO', 'Avanzado'),
        ],
        default='INTERMEDIO',
        help_text='Nivel de dificultad del plan.'
    )
    duracion_semanas = models.PositiveIntegerField(
        'duración (semanas)',
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(52)],
        help_text='Duración estimada del plan en semanas.'
    )
    observaciones_generales = models.TextField(
        'observaciones generales',
        blank=True,
        null=True,
        help_text='Notas adicionales sobre el plan.'
    )

    class Meta:
        verbose_name = 'plan de entrenamiento'
        verbose_name_plural = 'planes de entrenamiento'
        ordering = ['-fecha_creacion', 'nombre']
        indexes = [
            models.Index(fields=['area_muscular'], name='idx_plan_area'),
            models.Index(fields=['activo'], name='idx_plan_activo'),
            models.Index(fields=['nivel_dificultad'], name='idx_plan_nivel'),
        ]

    def __str__(self):
        return f"{self.nombre} - {self.get_area_muscular_display()}"

    def total_ejercicios(self):
        """Retorna el número total de ejercicios en el plan."""
        return self.ejercicios.count()

    def usuarios_activos_count(self):
        """Retorna el número de usuarios activos con este plan asignado."""
        return self.usuarios_asignados.filter(is_active=True).count()

    def to_dict(self):
        """Retorna un diccionario con la información del plan."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'area_muscular': self.area_muscular,
            'nivel_dificultad': self.nivel_dificultad,
            'duracion_semanas': self.duracion_semanas,
            'total_ejercicios': self.total_ejercicios(),
            'usuarios_asignados': self.usuarios_activos_count(),
            'activo': self.activo,
        }


class Ejercicio(models.Model):
    """
    Modelo de ejercicios que componen un plan de entrenamiento.
    Cada ejercicio incluye detalles específicos de ejecución.
    """
    # 🔗 Relación con Plan (1:N)
    plan = models.ForeignKey(
        PlanEntrenamiento,
        on_delete=models.CASCADE,
        related_name='ejercicios',
        verbose_name='plan'
    )
    
    # 📋 Información del ejercicio
    nombre = models.CharField(
        'nombre del ejercicio',
        max_length=150,
        help_text='Nombre del ejercicio (ej: Press de banca, Sentadilla).'
    )
    descripcion = models.TextField(
        'descripción',
        blank=True,
        null=True,
        help_text='Descripción detallada de la técnica del ejercicio.'
    )
    
    # 📊 Parámetros de entrenamiento
    series = models.PositiveIntegerField(
        'número de series',
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Cantidad de series a realizar.'
    )
    repeticiones = models.CharField(
        'repeticiones',
        max_length=50,
        help_text='Número de repeticiones (ej: "10-12", "15", "Fallo").'
    )
    descanso_segundos = models.PositiveIntegerField(
        'descanso (segundos)',
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(600)],
        help_text='Tiempo de descanso entre series en segundos.'
    )
    peso_sugerido = models.DecimalField(
        'peso sugerido (kg)',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text='Peso sugerido en kilogramos (opcional).'
    )
    
    # 🎯 Orden y configuración
    orden = models.PositiveIntegerField(
        'orden de ejecución',
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Orden en que se realiza el ejercicio dentro del plan.'
    )
    area_especifica = models.CharField(
        'área específica',
        max_length=100,
        blank=True,
        null=True,
        help_text='Músculo o zona específica que trabaja el ejercicio.'
    )
    observaciones = models.TextField(
        'observaciones',
        blank=True,
        null=True,
        help_text='Notas adicionales sobre la ejecución del ejercicio.'
    )
    
    # ⚙️ Estado
    activo = models.BooleanField(
        'activo',
        default=True,
        help_text='Indica si el ejercicio está activo en el plan.'
    )

    class Meta:
        verbose_name = 'ejercicio'
        verbose_name_plural = 'ejercicios'
        ordering = ['plan', 'orden']
        indexes = [
            models.Index(fields=['plan', 'orden'], name='idx_ejercicio_plan_orden'),
            models.Index(fields=['area_especifica'], name='idx_ejercicio_area'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'nombre', 'orden'],
                name='unique_ejercicio_plan_nombre_orden',
                violation_error_message='Ya existe un ejercicio con este nombre y orden en el plan.'
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.series} series x {self.repeticiones} reps)"

    def get_descanso_formatted(self):
        """Retorna el tiempo de descanso formateado en minutos y segundos."""
        minutos = self.descanso_segundos // 60
        segundos = self.descanso_segundos % 60
        if minutos > 0:
            return f"{minutos}m {segundos}s"
        return f"{segundos}s"

    def to_dict(self):
        """Retorna un diccionario con la información del ejercicio."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'series': self.series,
            'repeticiones': self.repeticiones,
            'descanso': self.get_descanso_formatted(),
            'descanso_segundos': self.descanso_segundos,
            'peso_sugerido': float(self.peso_sugerido) if self.peso_sugerido else None,
            'orden': self.orden,
            'area_especifica': self.area_especifica,
            'observaciones': self.observaciones,
        }


class HistorialPlanUsuario(models.Model):
    """
    Modelo para rastrear el historial de planes asignados a cada usuario.
    Permite llevar un registro de qué planes ha tenido cada usuario,
    cuándo los recibió y su estado de cumplimiento.
    """
    ESTADO_CHOICES = [
        ('ASIGNADO', 'Asignado'),
        ('EN_PROGRESO', 'En progreso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='historial_planes'
    )
    plan = models.ForeignKey(
        PlanEntrenamiento,
        on_delete=models.CASCADE,
        related_name='historial_usuarios'
    )
    fecha_asignacion = models.DateTimeField(
        'fecha de asignación',
        auto_now_add=True
    )
    fecha_finalizacion = models.DateTimeField(
        'fecha de finalización',
        blank=True,
        null=True
    )
    estado = models.CharField(
        'estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ASIGNADO'
    )
    progreso_porcentaje = models.DecimalField(
        'progreso (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    observaciones_seguimiento = models.TextField(
        'observaciones de seguimiento',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'historial de plan por usuario'
        verbose_name_plural = 'historial de planes por usuario'
        ordering = ['-fecha_asignacion']
        indexes = [
            models.Index(fields=['usuario', 'estado'], name='idx_historial_usuario_estado'),
            models.Index(fields=['fecha_asignacion'], name='idx_historial_fecha'),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.plan.nombre} ({self.estado})"

    def actualizar_progreso(self):
        """
        Calcula y actualiza el progreso del plan.
        Esto debería llamarse cuando el usuario complete sesiones.
        """
        # Lógica básica: si está completado, 100%
        if self.estado == 'COMPLETADO':
            self.progreso_porcentaje = 100.00
        elif self.estado == 'CANCELADO':
            self.progreso_porcentaje = 0.00
        return self.progreso_porcentaje