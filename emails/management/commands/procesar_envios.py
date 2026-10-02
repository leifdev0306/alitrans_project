from django.core.management.base import BaseCommand
from django.utils import timezone
from emails.models import Envio, Oferta
from emails.tasks import procesar_envio
import random


class Command(BaseCommand):
    help = 'Procesa envíos programados y aleatorios de Alitrans.'

    def add_arguments(self, parser):
        parser.add_argument('--aleatorio', action='store_true',
                            help='Además, envía una oferta aleatoria a todos los suscritos.')

    def handle(self, *args, **options):
        ahora = timezone.now()

        # 1) Envíos programados cuya hora ya llegó
        pendientes = Envio.objects.filter(estado='programado',
                                          fecha_programada__lte=ahora)
        self.stdout.write(f'📨 Envíos programados listos: {pendientes.count()}')
        for envio in pendientes:
            self.stdout.write(f'   → {envio.nombre_campana}...')
            try:
                resultado = procesar_envio(envio.id)
                self.stdout.write(self.style.SUCCESS(f'     ✓ {resultado}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'     ✗ {e}'))

        # 2) Envío aleatorio opcional
        if options['aleatorio']:
            ofertas = list(Oferta.objects.filter(activa=True))
            if ofertas:
                oferta = random.choice(ofertas)
                envio = Envio.objects.create(
                    nombre_campana=f'Aleatorio - {ahora:%Y-%m-%d %H:%M}',
                    oferta=oferta, enviar_a_todos=True, tipo_envio='aleatorio')
                self.stdout.write(f'🎲 Aleatorio: {oferta.titulo}')
                procesar_envio(envio.id)
                self.stdout.write(self.style.SUCCESS('   ✓ Enviado'))
            else:
                self.stdout.write('⚠️  No hay ofertas activas.')

        self.stdout.write(self.style.SUCCESS('✅ Procesamiento completado.'))