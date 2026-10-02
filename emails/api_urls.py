from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'ofertas', views.OfertaViewSet)
router.register(r'destinatarios', views.DestinatarioViewSet)
router.register(r'envios', views.EnvioViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('recibir-oferta/', views.recibir_oferta_api, name='recibir_oferta'),
]