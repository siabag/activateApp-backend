from django.utils import timezone
from apps.membresias.models import Membresia

def actualizar_membresias_vencidas():
    """
    Actualiza automáticamente el estado de las membresías vencidas.
    Retorna el número de membresías actualizadas.
    """
    hoy = timezone.now().date()
    
    membresias_vencidas = Membresia.objects.filter(
        estado='ACTIVA',
        fecha_vencimiento__lt=hoy
    )
    
    count = membresias_vencidas.count()
    
    if count > 0:
        # Actualizar estado a VENCIDA
        membresias_vencidas.update(estado='VENCIDA')
        
        # Registrar en historial
        from apps.membresias.models import HistorialMembresia
        
        for membresia in membresias_vencidas:
            HistorialMembresia.objects.create(
                membresia=membresia,
                estado_anterior='ACTIVA',
                estado_nuevo='VENCIDA',
                motivo='Vencimiento automático por fecha'
            )
    
    return count