from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'emails', views.EmailViewSet)
router.register(r'destinatarios', views.DestinatarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('recibir-email/', views.recibir_email_api, name='recibir_email'),
]