"""
Envío de correos con imágenes incrustadas (CID).
Sin Celery: se invoca desde las vistas o desde el management command.
"""
import random
from email.mime.image import MIMEImage
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from django.conf import settings
from .models import Envio, Oferta


def _construir_html(oferta, cids_imagenes):
    bloque_imgs = ''
    for cid in cids_imagenes:
        bloque_imgs += (
            f'<div style="margin:20px 0;text-align:center;">'
            f'<img src="cid:{cid}" alt="Imagen de la oferta" '
            f'style="max-width:100%;height:auto;border-radius:10px;" />'
            f'</div>'
        )

    bloque_portada = ''
    if oferta.imagen_principal:
        bloque_portada = (
            f'<div style="text-align:center;margin-bottom:20px;">'
            f'<img src="cid:portada" alt="{oferta.titulo}" '
            f'style="max-width:100%;height:auto;border-radius:10px;" />'
            f'</div>'
        )

    bloque_desc = ''
    if oferta.descuento_porcentaje and float(oferta.descuento_porcentaje) > 0:
        bloque_desc = (
            f'<div style="background:#e7f3ff;border-left:4px solid #00A8E8;'
            f'padding:14px;margin:20px 0;border-radius:6px;">'
            f'<strong style="color:#0B3D91;">💰 Descuento: '
            f'{oferta.descuento_porcentaje}%</strong></div>'
        )

    bloque_precio = ''
    if oferta.precio_desde:
        bloque_precio = (
            f'<p style="color:#0B3D91;font-size:16px;">'
            f'<strong>Precio desde:</strong> {oferta.precio_desde} CUP</p>'
        )

    bloque_vigencia = ''
    if oferta.valida_hasta:
        bloque_vigencia = (
            f'<p style="color:#888;font-size:13px;">'
            f'Válida hasta: {oferta.valida_hasta:%d/%m/%Y}</p>'
        )

    subtitulo_html = ''
    if oferta.subtitulo:
        subtitulo_html = (
            f'<p style="color:#666;font-size:14px;margin-top:-8px;">'
            f'{oferta.subtitulo}</p>'
        )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F4F7FC;font-family:Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;background:#ffffff;">
    <div style="background:linear-gradient(135deg,#0B3D91,#1E5AA8);padding:30px;text-align:center;">
      <h1 style="color:#ffffff;margin:0;font-size:26px;">🚚 ALITRANS</h1>
      <p style="color:#cfe2ff;margin:6px 0 0 0;font-size:13px;">Transporte &amp; Logística</p>
    </div>
    <div style="padding:30px;">
      <h2 style="color:#0B3D91;margin-top:0;">{oferta.titulo}</h2>
      {subtitulo_html}
      {bloque_portada}
      <div style="color:#333;line-height:1.6;">{oferta.contenido_html}</div>
      {bloque_imgs}
      {bloque_desc}
      {bloque_precio}
      {bloque_vigencia}
    </div>
    <div style="background:#1A1A2E;padding:20px;text-align:center;color:#aaa;font-size:12px;">
      <p style="margin:0;">© Alitrans - Servicios de transporte y logística</p>
      <p style="margin:6px 0 0 0;">Recibes este correo porque estás suscrito a nuestras ofertas.</p>
    </div>
  </div>
</body>
</html>"""


def _adjuntar_imagenes(msg, oferta):
    cids = []
    if oferta.imagen_principal:
        try:
            with oferta.imagen_principal.open('rb') as f:
                img = MIMEImage(f.read())
            img.add_header('Content-ID', '<portada>')
            img.add_header('Content-Disposition', 'inline')
            msg.attach(img)
        except Exception:
            pass

    for idx, img_obj in enumerate(oferta.imagenes.all()):
        try:
            with img_obj.imagen.open('rb') as f:
                img = MIMEImage(f.read())
            cid = f'img_{idx}'
            img.add_header('Content-ID', f'<{cid}>')
            img.add_header('Content-Disposition', 'inline')
            msg.attach(img)
            cids.append(cid)
        except Exception:
            continue
    return cids


def procesar_envio(envio_id):
    """Envía una campaña a todos sus destinatarios."""
    try:
        envio = Envio.objects.get(id=envio_id)
    except Envio.DoesNotExist:
        return 'Envío no encontrado.'

    if envio.estado in ('enviando', 'enviado'):
        return 'Envío ya procesado.'

    envio.estado = 'enviando'
    envio.save(update_fields=['estado'])

    oferta = envio.oferta
    destinatarios = envio.obtener_destinatarios_finales()

    if not destinatarios:
        envio.estado = 'fallido'
        envio.notas += '\n[ERROR] No hay destinatarios válidos.'
        envio.save(update_fields=['estado', 'notas'])
        return 'Sin destinatarios.'

    asunto = envio.asunto_personalizado or oferta.titulo
    enviados, fallidos = 0, 0

    for correo in destinatarios:
        try:
            msg = EmailMultiAlternatives(
                subject=asunto,
                body='Tu cliente de correo no soporta HTML. Visita nuestra web para ver la oferta.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[correo],
            )
            cids = _adjuntar_imagenes(msg, oferta)
            html = _construir_html(oferta, cids)
            msg.attach_alternative(html, 'text/html')
            msg.send(fail_silently=False)
            enviados += 1
        except Exception as e:
            fallidos += 1
            envio.notas += f'\n[ERROR {correo}] {e}'

    envio.total_enviados = enviados
    envio.total_fallidos = fallidos
    envio.fecha_envio = timezone.now()
    envio.estado = 'enviado' if enviados > 0 else 'fallido'
    envio.save()
    return f'Enviados: {enviados}, Fallidos: {fallidos}'


def enviar_oferta_aleatoria():
    """Crea y lanza un envío con una oferta activa al azar."""
    ofertas = list(Oferta.objects.filter(activa=True))
    if not ofertas:
        return 'No hay ofertas activas.'

    oferta = random.choice(ofertas)
    envio = Envio.objects.create(
        nombre_campana=f'Aleatorio - {timezone.now():%Y-%m-%d %H:%M}',
        oferta=oferta,
        enviar_a_todos=True,
        tipo_envio='aleatorio',
    )
    return procesar_envio(envio.id)