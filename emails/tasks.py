from celery import shared_task
from django.core.mail import EmailMessage
from django.utils import timezone
from django.conf import settings
from .models import Email, Destinatario
import random


@shared_task
def enviar_correo(email_id):
    """Tarea Celery para enviar un correo."""
    try:
        email_obj = Email.objects.get(id=email_id)
        destinatarios = [d.strip() for d in email_obj.destinatarios.split(',') if d.strip()]

        if not destinatarios:
            # Si no hay destinatarios específicos, usar los suscritos
            destinatarios = list(
                Destinatario.objects.filter(activo=True).values_list('email', flat=True)
            )

        if not destinatarios:
            email_obj.estado = 'fallido'
            email_obj.save()
            return 'No hay destinatarios.'

        msg = EmailMessage(
            subject=email_obj.asunto,
            body=email_obj.cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        msg.content_subtype = 'html'
        msg.send(fail_silently=False)

        email_obj.estado = 'enviado'
        email_obj.fecha_envio = timezone.now()
        email_obj.save()
        return f'Correo enviado a {len(destinatarios)} destinatarios.'

    except Email.DoesNotExist:
        return 'Correo no encontrado.'
    except Exception as e:
        email_obj.estado = 'fallido'
        email_obj.save()
        return f'Error: {str(e)}'


@shared_task
def programar_envio_aleatorio(intervalo=3600):
    """Envía un correo aleatorio de los existentes."""
    correos = Email.objects.filter(estado__in=['borrador', 'programado'])
    if not correos.exists():
        return 'No hay correos disponibles.'

    correo = random.choice(correos)
    enviar_correo.delay(correo.id)
    return f'Correo aleatorio seleccionado: {correo.asunto}'