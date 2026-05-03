from django.urls import path
from apps.planes.views import MisPlanesView

urlpatterns = [
    # Ruta personalizada para que el cliente vea sus planes
    path('mis-planes/', MisPlanesView.as_view(), name='mis-planes'),
]