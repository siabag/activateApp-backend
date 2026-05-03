# Activate App - Backend

Sistema de gestión integral para el centro de entrenamiento "Activate"

## Tecnologías
- Python + Django + Django REST Framework
- PostgreSQL
- JWT Authentication

## Instalación
1. Crear entorno virtual: `python -m venv venv`
2. Activar: `.\venv\Scripts\Activate.ps1`
3. Instalar dependencias: `pip install -r requirements.txt`
4. Configurar base de datos en `.env`
5. Migrar: `python manage.py migrate`
6. Ejecutar: `python manage.py runserver`