from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('correos/', views.lista_correos, name='lista_correos'),
    path('correos/nuevo/', views.crear_correo, name='crear_correo'),
    path('destinatarios/', views.lista_destinatarios, name='lista_destinatarios'),
]