from django.urls import path
from . import views

app_name = 'emails'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Ofertas
    path('ofertas/', views.lista_ofertas, name='lista_ofertas'),
    path('ofertas/nueva/', views.crear_oferta, name='crear_oferta'),
    path('ofertas/<int:pk>/', views.detalle_oferta, name='detalle_oferta'),
    path('ofertas/<int:pk>/editar/', views.editar_oferta, name='editar_oferta'),
    path('ofertas/<int:pk>/toggle/', views.toggle_oferta, name='toggle_oferta'),
    path('ofertas/<int:pk>/eliminar/', views.eliminar_oferta, name='eliminar_oferta'),
    path('ofertas/imagen/<int:pk>/eliminar/', views.eliminar_imagen_oferta,
         name='eliminar_imagen_oferta'),

    # Destinatarios
    path('destinatarios/', views.lista_destinatarios, name='lista_destinatarios'),
    path('destinatarios/nuevo/', views.crear_destinatario, name='crear_destinatario'),
    path('destinatarios/<int:pk>/editar/', views.editar_destinatario,
         name='editar_destinatario'),

    # Envíos
    path('envios/', views.lista_envios, name='lista_envios'),
    path('envios/nuevo/', views.crear_envio, name='crear_envio'),
    path('envios/<int:pk>/', views.detalle_envio, name='detalle_envio'),
    path('envios/<int:pk>/editar/', views.editar_envio, name='editar_envio'),
    path('envios/<int:pk>/lanzar/', views.lanzar_envio, name='lanzar_envio'),
    path('envios/<int:pk>/cancelar/', views.cancelar_envio, name='cancelar_envio'),
]