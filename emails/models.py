from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Oferta(models.Model):
    TIPO_CHOICES = [
        ('transporte_carga', 'Transporte de carga'),
        ('transporte_personal', 'Transporte de personal'),
        ('alquiler_vehiculos', 'Alquiler de vehículos'),
        ('logistica', 'Servicios logísticos'),
        ('paqueteria', 'Paquetería'),
        ('otro', 'Otro'),
    ]

    titulo = models.CharField(max_length=200, verbose_name='Título de la oferta')
    subtitulo = models.CharField(max_length=255, blank=True,
                                 verbose_name='Subtítulo / Gancho comercial')
    tipo_servicio = models.CharField(max_length=30, choices=TIPO_CHOICES,
                                     default='transporte_carga',
                                     verbose_name='Tipo de servicio')
    descripcion_corta = models.CharField(max_length=300,
                                         verbose_name='Descripción corta',
                                         help_text='Aparecerá en las tarjetas')
    contenido_html = models.TextField(
        verbose_name='Contenido del correo (HTML)',
        help_text='Cuerpo del correo que recibirán los clientes'
    )
    descuento_porcentaje = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Descuento (%)'
    )
    precio_desde = models.DecimalField(max_digits=10, decimal_places=2,
                                       null=True, blank=True,
                                       verbose_name='Precio desde (CUP)')
    valida_desde = models.DateField(null=True, blank=True, verbose_name='Válida desde')
    valida_hasta = models.DateField(null=True, blank=True, verbose_name='Válida hasta')
    imagen_principal = models.ImageField(
        upload_to='ofertas/portadas/', null=True, blank=True,
        verbose_name='Imagen principal'
    )
    activa = models.BooleanField(default=True, verbose_name='¿Oferta activa?')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.titulo

    @property
    def esta_vigente(self):
        hoy = timezone.now().date()
        if self.valida_hasta and hoy > self.valida_hasta:
            return False
        if self.valida_desde and hoy < self.valida_desde:
            return False
        return True

    @property
    def total_envios(self):
        return self.envios.count()

    @property
    def total_destinatarios_alcanzados(self):
        return sum(e.total_enviados for e in self.envios.all())


class ImagenOferta(models.Model):
    oferta = models.ForeignKey(Oferta, on_delete=models.CASCADE,
                               related_name='imagenes', verbose_name='Oferta')
    imagen = models.ImageField(upload_to='ofertas/imagenes/', verbose_name='Imagen')
    titulo = models.CharField(max_length=150, blank=True, verbose_name='Título / alt')
    orden = models.PositiveIntegerField(default=0, verbose_name='Orden')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Imagen de oferta'
        verbose_name_plural = 'Imágenes de oferta'
        ordering = ['orden', 'id']

    def __str__(self):
        return f'{self.oferta.titulo} - {self.titulo or self.imagen.name}'


class Destinatario(models.Model):
    SECTOR_CHOICES = [
        ('empresa', 'Empresa'),
        ('particular', 'Particular'),
        ('mayorista', 'Mayorista'),
        ('otro', 'Otro'),
    ]

    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    nombre = models.CharField(max_length=150, verbose_name='Nombre completo')
    telefono = models.CharField(max_length=30, blank=True, verbose_name='Teléfono')
    empresa = models.CharField(max_length=150, blank=True, verbose_name='Empresa')
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES,
                              default='particular', verbose_name='Sector')
    activo = models.BooleanField(default=True, verbose_name='¿Activo?')
    fecha_suscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Destinatario'
        verbose_name_plural = 'Destinatarios'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} <{self.email}>'


class Envio(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('programado', 'Programado'),
        ('enviando', 'Enviando'),
        ('enviado', 'Enviado'),
        ('fallido', 'Fallido'),
        ('cancelado', 'Cancelado'),
    ]
    TIPO_CHOICES = [
        ('manual', 'Envío manual inmediato'),
        ('programado', 'Envío programado'),
        ('aleatorio', 'Envío aleatorio'),
        ('recurrente', 'Envío recurrente'),
    ]

    nombre_campana = models.CharField(max_length=200,
                                      verbose_name='Nombre de la campaña')
    oferta = models.ForeignKey(Oferta, on_delete=models.PROTECT,
                               related_name='envios', verbose_name='Oferta')
    destinatarios = models.ManyToManyField(Destinatario, blank=True,
                                           related_name='envios',
                                           verbose_name='Destinatarios específicos')
    enviar_a_todos = models.BooleanField(
        default=False, verbose_name='Enviar a todos los suscritos activos')
    tipo_envio = models.CharField(max_length=20, choices=TIPO_CHOICES,
                                  default='manual', verbose_name='Tipo de envío')
    fecha_programada = models.DateTimeField(null=True, blank=True,
                                            verbose_name='Fecha programada')
    intervalo_segundos = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Intervalo recurrente (segundos)')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES,
                              default='borrador', verbose_name='Estado')
    asunto_personalizado = models.CharField(
        max_length=255, blank=True, verbose_name='Asunto personalizado',
        help_text='Si se deja vacío se usa el título de la oferta')
    total_enviados = models.PositiveIntegerField(default=0)
    total_fallidos = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, verbose_name='Notas internas')

    class Meta:
        verbose_name = 'Envío'
        verbose_name_plural = 'Envíos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.nombre_campana} → {self.oferta.titulo}'

    def obtener_destinatarios_finales(self):
        if self.enviar_a_todos:
            return list(
                Destinatario.objects.filter(activo=True)
                .values_list('email', flat=True)
            )
        return list(self.destinatarios.values_list('email', flat=True))