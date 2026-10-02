from django.contrib import admin
from django.utils.html import format_html
from .models import Oferta, ImagenOferta, Destinatario, Envio


class ImagenOfertaInline(admin.TabularInline):
    model = ImagenOferta
    extra = 1
    fields = ('imagen', 'titulo', 'orden', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="max-height:80px;" />', obj.imagen.url)
        return '—'
    preview.short_description = 'Vista previa'


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'tipo_servicio', 'descuento_porcentaje',
                    'activa', 'esta_vigente', 'fecha_creacion')
    list_filter = ('activa', 'tipo_servicio')
    search_fields = ('titulo', 'subtitulo', 'descripcion_corta')
    list_editable = ('activa',)
    inlines = [ImagenOfertaInline]


@admin.register(Destinatario)
class DestinatarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'empresa', 'sector', 'activo')
    list_filter = ('activo', 'sector')
    search_fields = ('nombre', 'email', 'empresa')
    list_editable = ('activo',)


@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('nombre_campana', 'oferta', 'tipo_envio', 'estado',
                    'total_enviados', 'total_fallidos', 'fecha_creacion')
    list_filter = ('estado', 'tipo_envio')
    search_fields = ('nombre_campana', 'oferta__titulo')
    readonly_fields = ('total_enviados', 'total_fallidos',
                       'fecha_creacion', 'fecha_envio')
    filter_horizontal = ('destinatarios',)