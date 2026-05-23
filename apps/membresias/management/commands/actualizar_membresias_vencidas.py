from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.membresias.models import Membresia
from datetime import date

class Command(BaseCommand):
    help = 'Actualiza el estado de las membresías vencidas'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        
        # Buscar membresías activas que ya vencieron
        membresias_vencidas = Membresia.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lt=hoy
        )
        
        # Actualizar estado a VENCIDA
        count = membresias_vencidas.update(estado='VENCIDA')
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {count} membresías a VENCIDAS')
        )