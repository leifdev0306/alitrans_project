from django.contrib import admin
from .models import Email, Destinatario


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'estado', 'fecha_creacion', 'fecha_envio', 'es_aleatorio')
    list_filter = ('estado', 'es_aleatorio')
    search_fields = ('asunto', 'destinatarios')
    actions = ['enviar_seleccionados']

    def enviar_seleccionados(self, request, queryset):
        from .tasks import enviar_correo
        for email in queryset:
            enviar_correo.delay(email.id)
        self.message_user(request, f'{queryset.count()} correos enviados en cola.')
    enviar_seleccionados.short_description = 'Enviar correos seleccionados'


@admin.register(Destinatario)
class DestinatarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'nombre', 'activo', 'fecha_suscripcion')
    list_filter = ('activo',)
    search_fields = ('email', 'nombre')