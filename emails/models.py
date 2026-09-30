from django.db import models


class Email(models.Model):
    """Modelo para almacenar correos (ofertas/promociones)."""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('programado', 'Programado'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
    ]

    asunto = models.CharField(max_length=255, verbose_name='Asunto')
    cuerpo = models.TextField(verbose_name='Cuerpo del correo (HTML)')
    destinatarios = models.TextField(
        verbose_name='Destinatarios',
        help_text='Separa los correos con comas'
    )
    estado = models.CharField(
        max_length=20, choices=ESTADO_CHOICES, default='borrador'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_programada = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Fecha programada de envío'
    )
    fecha_envio = models.DateTimeField(null=True, blank=True)
    es_aleatorio = models.BooleanField(
        default=False,
        verbose_name='¿Enviar aleatoriamente?'
    )

    class Meta:
        verbose_name = 'Correo'
        verbose_name_plural = 'Correos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.asunto} - {self.get_estado_display()}"


class Destinatario(models.Model):
    """Destinatarios suscritos para recibir ofertas."""
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Destinatario'
        verbose_name_plural = 'Destinatarios'

    def __str__(self):
        return self.email