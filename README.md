# Activate App - Backend

Sistema de gestión integral para el centro de entrenamiento **"Activate"**. API RESTful desarrollada con Django REST Framework que gestiona usuarios, membresías, planes de entrenamiento y asistencia.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)

## ✨ Características

- 🔐 **Autenticación JWT** con tokens de acceso y refresco
- 👥 **Gestión de Usuarios** con roles (Propietario, Personal, Cliente)
- 💳 **Control de Membresías** con validación automática de vencimiento
- 🏋️ **Planes de Entrenamiento** personalizados con ejercicios
- 📊 **Dashboard Estadístico** para propietarios y personal
- 📅 **Registro de Asistencia** con control de entradas/salidas
- 📱 **API RESTful** documentada y escalable

## 🛠 Tecnologías

- **Backend Framework:** Django 5.0 + Django REST Framework
- **Base de Datos:** PostgreSQL 15+
- **Autenticación:** JWT (SimpleJWT)
- **CORS:** django-cors-headers
- **Validaciones:** Django Validators personalizados

## 📦 Requisitos

- Python 3.10 o superior
- PostgreSQL 15 o superior
- pip y virtualenv

## 🚀 Instalación

### 1. Clonar el repositorio

git clone <url-del-repositorio>
cd activateApp-backend

### 2. Crear entorno virtual

python -m venv venv

### 3. Activar entorno virtual

Windows:

.\venv\Scripts\activate

Linux/Mac:

source venv/bin/activate

### 4. Instalar dependencias

pip install -r requirements.txt

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo .env en la raíz del proyecto basado en .env.example:

SECRET_KEY=tu_clave_secreta_muy_segura
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos PostgreSQL
DB_NAME=activate_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

### 2. Configurar Base de Datos

# Crear base de datos en PostgreSQL
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

# Cargar datos de prueba (si existe)
python manage.py loaddata seed_data.json

# ▶️ Ejecución
Servidor de desarrollo

python manage.py runserver

La API estará disponible en: http://127.0.0.1:8000/api/
Comandos útiles

# Ejecutar migraciones
python manage.py migrate

# Crear nuevas migraciones
python manage.py makemigrations

# Actualizar membresías vencidas
python manage.py actualizar_membresias_vencidas

# Recopilar estáticos
python manage.py collectstatic

```bash