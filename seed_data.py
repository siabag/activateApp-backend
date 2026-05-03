"""
Script para poblar la base de datos con datos de prueba
Ejecutar: python seed_data.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone  # Esencial para manejar zonas horarias

# Configurar Django para que pueda importar los modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'activate_backend.settings')
django.setup()

from apps.usuarios.models import Usuario
from apps.membresias.models import Membresia, HistorialMembresia
from apps.planes.models import PlanEntrenamiento, Ejercicio, HistorialPlanUsuario
from apps.asistencia.models import RegistroAsistencia

def limpiar_base_datos():
    """
    Elimina todos los datos de prueba existentes para evitar duplicados y errores de integridad.
    El orden de eliminación es importante para respetar las llaves foráneas.
    """
    print("🧹 [1/6] Limpiando datos existentes...")
    
    # 1. Eliminar asistencia (depende de Membresía y Usuario)
    RegistroAsistencia.objects.all().delete()
    
    # 2. Eliminar historial de planes y asignaciones (depende de Plan y Usuario)
    HistorialPlanUsuario.objects.all().delete()
    
    # 3. Eliminar ejercicios (depende de Plan)
    Ejercicio.objects.all().delete()
    
    # 4. Eliminar planes (depende de Usuario 'creado_por')
    PlanEntrenamiento.objects.all().delete()
    
    # 5. Eliminar historial de membresías y membresías (depende de Usuario)
    HistorialMembresia.objects.all().delete()
    Membresia.objects.all().delete()
    
    # 6. Eliminar clientes (NO eliminamos Propietario ni Personal si se desea mantener, 
    # pero aquí eliminamos todos los clientes para recrearlos limpios)
    Usuario.objects.filter(role='CLIENTE').delete()
    
    print("   ✅ Base de datos limpia.")


def crear_usuarios():
    """Crear usuarios de prueba con diferentes roles"""
    print("📋 [2/6] Creando usuarios...")
    
    # Propietario
    propietario, _ = Usuario.objects.get_or_create(
        email='propietario@activate.com',
        defaults={
            'first_name': 'Carlos',
            'last_name': 'Valencia',
            'role': 'PROPIETARIO',
            'telefono': '3001234567',
            'peso': 78.5,
            'altura': 175.0,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    propietario.set_password('admin123')
    propietario.save()
    
    # Personal (Entrenadores)
    personal1, _ = Usuario.objects.get_or_create(
        email='entrenador1@activate.com',
        defaults={
            'first_name': 'Ana',
            'last_name': 'María Gómez',
            'role': 'PERSONAL',
            'telefono': '3102345678',
            'peso': 65.0,
            'altura': 168.0,
            'is_staff': True,
        }
    )
    personal1.set_password('personal123')
    personal1.save()
    
    personal2, _ = Usuario.objects.get_or_create(
        email='recepcion@activate.com',
        defaults={
            'first_name': 'Luis',
            'last_name': 'Fernando Ruiz',
            'role': 'PERSONAL',
            'telefono': '3153456789',
            'peso': 82.0,
            'altura': 180.0,
            'is_staff': True,
        }
    )
    personal2.set_password('personal123')
    personal2.save()
    
    # Clientes
    clientes_data = [
        {'email': 'juan.perez@email.com', 'first_name': 'Juan', 'last_name': 'Pérez', 'peso': 75.5, 'altura': 175.0},
        {'email': 'maria.lopez@email.com', 'first_name': 'María', 'last_name': 'López', 'peso': 62.0, 'altura': 165.0},
        {'email': 'pedro.sanchez@email.com', 'first_name': 'Pedro', 'last_name': 'Sánchez', 'peso': 88.0, 'altura': 182.0},
        {'email': 'laura.martinez@email.com', 'first_name': 'Laura', 'last_name': 'Martínez', 'peso': 58.5, 'altura': 160.0},
        {'email': 'diego.rodriguez@email.com', 'first_name': 'Diego', 'last_name': 'Rodríguez', 'peso': 92.0, 'altura': 178.0},
        {'email': 'sofia.garcia@email.com', 'first_name': 'Sofía', 'last_name': 'García', 'peso': 55.0, 'altura': 162.0},
        {'email': 'andres.torres@email.com', 'first_name': 'Andrés', 'last_name': 'Torres', 'peso': 80.0, 'altura': 176.0},
        {'email': 'carmen.flores@email.com', 'first_name': 'Carmen', 'last_name': 'Flores', 'peso': 68.0, 'altura': 170.0},
    ]
    
    clientes = []
    for i, data in enumerate(clientes_data, 1):
        cliente, _ = Usuario.objects.get_or_create(
            email=data['email'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': 'CLIENTE',
                'telefono': f'320{i}234567',
                'peso': data['peso'],
                'altura': data['altura'],
            }
        )
        cliente.set_password('cliente123')
        cliente.save()
        clientes.append(cliente)
    
    print(f"   ✅ {len(clientes) + 3} usuarios creados.")
    return propietario, personal1, personal2, clientes


def crear_membresias(clientes):
    """Crear membresías de diferentes tipos y estados"""
    print("💳 [3/6] Creando membresías...")
    
    hoy = datetime.now().date()
    membresias_creadas = []
    
    # Membresías activas
    membresias_activas = [
        {'tipo': 'MENSUAL', 'precio': 150000, 'dias_vencimiento': 30, 'sesiones': 12},
        {'tipo': 'BIMESTRAL', 'precio': 280000, 'dias_vencimiento': 60, 'sesiones': 24},
        {'tipo': 'TRIMESTRAL', 'precio': 400000, 'dias_vencimiento': 90, 'sesiones': 36},
        {'tipo': 'SEMESTRAL', 'precio': 750000, 'dias_vencimiento': 180, 'sesiones': 0},
    ]
    
    for i, cliente in enumerate(clientes):
        membresia_data = membresias_activas[i % len(membresias_activas)]
        fecha_inicio = hoy - timedelta(days=10)
        fecha_vencimiento = fecha_inicio + timedelta(days=membresia_data['dias_vencimiento'])
        
        membresia = Membresia.objects.create(
            usuario=cliente,
            tipo=membresia_data['tipo'],
            precio=membresia_data['precio'],
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            estado='ACTIVA',
            sesiones_totales=membresia_data['sesiones'],
            sesiones_consumidas=0,
            observaciones=f'Membresía {membresia_data["tipo"]} - Cliente {i+1}'
        )
        membresias_creadas.append(membresia)
    
    # Membresías vencidas (para probar alertas)
    for i in range(2):
        cliente = clientes[i + 4]
        Membresia.objects.create(
            usuario=cliente,
            tipo='MENSUAL',
            precio=150000,
            fecha_inicio=hoy - timedelta(days=45),
            fecha_vencimiento=hoy - timedelta(days=15),
            estado='VENCIDA',
            sesiones_totales=12,
            sesiones_consumidas=12,
            observaciones='Membresía vencida - Requiere renovación'
        )
    
    print(f"   ✅ Membresías creadas.")
    return membresias_creadas


def crear_planes_entrenamiento(propietario):
    """Crear planes de entrenamiento con ejercicios"""
    print("🏋️ [4/6] Creando planes de entrenamiento...")
    
    planes_data = [
        {
            'nombre': 'Hipertrofia Pecho y Tríceps',
            'descripcion': 'Plan enfocado en desarrollo de pecho y tríceps para nivel intermedio',
            'area_muscular': 'PECHO',
            'nivel_dificultad': 'INTERMEDIO',
            'duracion_semanas': 4,
            'ejercicios': [
                {'nombre': 'Press de Banca Plano', 'series': 4, 'repeticiones': '8-10', 'descanso': 90, 'orden': 1, 'area': 'Pecho'},
                {'nombre': 'Press Inclinado con Mancuernas', 'series': 3, 'repeticiones': '10-12', 'descanso': 75, 'orden': 2, 'area': 'Pecho Superior'},
                {'nombre': 'Aperturas en Polea', 'series': 3, 'repeticiones': '12-15', 'descanso': 60, 'orden': 3, 'area': 'Pecho'},
                {'nombre': 'Fondos en Paralelas', 'series': 3, 'repeticiones': 'Fallo', 'descanso': 90, 'orden': 4, 'area': 'Tríceps'},
            ]
        },
        {
            'nombre': 'Fuerza Piernas y Glúteos',
            'descripcion': 'Plan de fuerza para miembros inferiores',
            'area_muscular': 'PIERNAS',
            'nivel_dificultad': 'AVANZADO',
            'duracion_semanas': 6,
            'ejercicios': [
                {'nombre': 'Sentadilla con Barra', 'series': 5, 'repeticiones': '5-6', 'descanso': 180, 'orden': 1, 'area': 'Cuádriceps'},
                {'nombre': 'Peso Muerto Rumano', 'series': 4, 'repeticiones': '6-8', 'descanso': 150, 'orden': 2, 'area': 'Isquiotibiales'},
                {'nombre': 'Hip Thrust', 'series': 4, 'repeticiones': '10-12', 'descanso': 90, 'orden': 3, 'area': 'Glúteos'},
                {'nombre': 'Zancadas con Mancuernas', 'series': 3, 'repeticiones': '12 por pierna', 'descanso': 90, 'orden': 4, 'area': 'Piernas'},
            ]
        },
        {
            'nombre': 'Definición Abdomen y Core',
            'descripcion': 'Plan de alta intensidad para definición abdominal',
            'area_muscular': 'ABDOMEN',
            'nivel_dificultad': 'INTERMEDIO',
            'duracion_semanas': 4,
            'ejercicios': [
                {'nombre': 'Crunch Abdominal', 'series': 4, 'repeticiones': '20-25', 'descanso': 45, 'orden': 1, 'area': 'Abdomen'},
                {'nombre': 'Plancha Isométrica', 'series': 3, 'repeticiones': '45-60 seg', 'descanso': 45, 'orden': 2, 'area': 'Core'},
                {'nombre': 'Elevación de Piernas', 'series': 3, 'repeticiones': '15-20', 'descanso': 45, 'orden': 3, 'area': 'Abdomen Inferior'},
                {'nombre': 'Russian Twist', 'series': 3, 'repeticiones': '20 por lado', 'descanso': 45, 'orden': 4, 'area': 'Oblicuos'},
            ]
        },
        {
            'nombre': 'Principiante Full Body',
            'descripcion': 'Plan completo para principiantes',
            'area_muscular': 'Cuerpo_COMPLETO',
            'nivel_dificultad': 'PRINCIPIANTE',
            'duracion_semanas': 4,
            'ejercicios': [
                {'nombre': 'Sentadilla con Peso Corporal', 'series': 3, 'repeticiones': '12-15', 'descanso': 60, 'orden': 1, 'area': 'Piernas'},
                {'nombre': 'Flexiones de Brazos', 'series': 3, 'repeticiones': '8-12', 'descanso': 60, 'orden': 2, 'area': 'Pecho'},
                {'nombre': 'Remo con Mancuernas', 'series': 3, 'repeticiones': '12-15', 'descanso': 60, 'orden': 3, 'area': 'Espalda'},
                {'nombre': 'Press de Hombros', 'series': 3, 'repeticiones': '10-12', 'descanso': 60, 'orden': 4, 'area': 'Hombros'},
            ]
        },
    ]
    
    planes_creados = []
    for plan_data in planes_data:
        ejercicios_data = plan_data.pop('ejercicios')
        
        plan = PlanEntrenamiento.objects.create(
            creado_por=propietario,
            **plan_data
        )
        
        for ejercicio in ejercicios_data:
            Ejercicio.objects.create(
                plan=plan,
                nombre=ejercicio['nombre'],
                series=ejercicio['series'],
                repeticiones=ejercicio['repeticiones'],
                descanso_segundos=ejercicio['descanso'],      # Nombre correcto del campo
                orden=ejercicio['orden'],
                area_especifica=ejercicio['area'],            # Nombre correcto del campo
            )
        
        planes_creados.append(plan)
    
    print(f"   ✅ {len(planes_creados)} planes creados con ejercicios.")
    return planes_creados


def asignar_planes_a_clientes(clientes, planes):
    """Asignar planes a clientes"""
    print("📅 [5/6] Asignando planes a clientes...")
    
    for i, cliente in enumerate(clientes[:6]):  # Asignar a los primeros 6 clientes
        plan = planes[i % len(planes)]
        plan.usuarios_asignados.add(cliente)
        
        HistorialPlanUsuario.objects.create(
            usuario=cliente,
            plan=plan,
            estado='EN_PROGRESO',
            progreso_porcentaje=35.0 if i % 3 == 0 else 15.0,
            observaciones_seguimiento=f'Cliente en semana {i % 4 + 1} del plan'
        )
    
    print("   ✅ Planes asignados.")


def crear_registros_asistencia(clientes, membresias):
    """Crear registros de asistencia de los últimos 15 días"""
    print("✅ [6/6] Creando registros de asistencia...")
    
    # Limpieza específica de asistencia por seguridad
    RegistroAsistencia.objects.all().delete()

    hoy = timezone.now().date()
    registros_creados = 0
    
    for dia in range(15):
        fecha = hoy - timedelta(days=dia)
        
        # Algunos clientes asisten cada día (pseudo-aleatorio)
        clientes_del_dia = [c for c in clientes if hash(f"{c.id}-{dia}") % 3 != 0]
        
        for cliente in clientes_del_dia:
            # Buscar membresía activa del cliente en esa fecha
            membresia = Membresia.objects.filter(
                usuario=cliente,
                fecha_inicio__lte=fecha,
                fecha_vencimiento__gte=fecha
            ).first()
            
            if membresia:
                # Generar hora aleatoria entre 6 AM y 9 PM
                hora_random = 6 + (hash(f"{cliente.id}-{dia}") % 15)
                
                # Crear fecha/hora y hacerla TIMEZONE AWARE
                fecha_hora_naive = datetime(fecha.year, fecha.month, fecha.day, hora_random, 0, 0)
                fecha_hora_aware = timezone.make_aware(fecha_hora_naive)

                # ✅ Usar get_or_create para garantizar unicidad en la llave (usuario, fecha, tipo)
                registro, creado = RegistroAsistencia.objects.get_or_create(
                    usuario=cliente,
                    fecha=fecha,
                    tipo_registro='INGRESO',
                    defaults={
                        'membresia': membresia,
                        'fecha_hora': fecha_hora_aware,
                        'metodo_ingreso': 'MANUAL',
                        'session_consumida': True,
                        'es_consumo_sesion': True,
                        'observaciones': 'Registro seed'
                    }
                )
                
                if creado:
                    registros_creados += 1
    
    print(f"   ✅ {registros_creados} registros de asistencia creados.")


def main():
    """Función principal"""
    print("=" * 60)
    print("🏋️ INICIANDO CARGA DE DATOS DE PRUEBA - ACTIVATE 🏋️")
    print("=" * 60)
    
    try:
        # 1. Limpiar todo para evitar duplicados
        limpiar_base_datos()
        
        # 2. Crear datos
        propietario, personal1, personal2, clientes = crear_usuarios()
        membresias = crear_membresias(clientes)
        planes = crear_planes_entrenamiento(propietario)
        asignar_planes_a_clientes(clientes, planes)
        crear_registros_asistencia(clientes, membresias)
        
        print("\n" + "=" * 60)
        print("✅ ¡DATOS DE PRUEBA CREADOS EXITOSAMENTE!")
        print("=" * 60)
        print("\n📊 RESUMEN:")
        print(f"   • Usuarios: {Usuario.objects.count()}")
        print(f"   • Membresías: {Membresia.objects.count()}")
        print(f"   • Planes: {PlanEntrenamiento.objects.count()}")
        print(f"   • Asistencias: {RegistroAsistencia.objects.count()}")
        print("\n🔐 CREDENCIALES:")
        print("   • Propietario: propietario@activate.com / admin123")
        print("   • Personal: entrenador1@activate.com / personal123")
        print("   • Cliente: juan.perez@email.com / cliente123")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()