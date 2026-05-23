from django.urls import path
from apps.usuarios.views import (
    UsuarioRegisterView,
    UsuarioProfileView,
    UsuarioPasswordChangeView,
    UsuarioFichaFisicaView,
)

urlpatterns = [
    path('register/', UsuarioRegisterView.as_view(), name='register'),
    path('change-password/', UsuarioPasswordChangeView.as_view(), name='change-password'),
    path('profile/', UsuarioProfileView.as_view(), name='profile'),
    path('ficha-fisica/', UsuarioFichaFisicaView.as_view(), name='ficha-fisica'),
    path('mi-perfil/', UsuarioProfileView.as_view(), name='mi-perfil'),
]