from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import Oferta, ImagenOferta, Destinatario, Envio
from .forms import OfertaForm, ImagenOfertaForm, DestinatarioForm, EnvioForm
from .serializers import (OfertaSerializer, DestinatarioSerializer,
                          EnvioSerializer)
from .tasks import procesar_envio, enviar_oferta_aleatoria


# =====================================================================
#  VISTAS DEL FRONTEND
# =====================================================================

def dashboard(request):
    context = {
        'total_ofertas': Oferta.objects.count(),
        'ofertas_activas': Oferta.objects.filter(activa=True).count(),
        'total_envios': Envio.objects.count(),
        'envios_pendientes': Envio.objects.filter(
            estado__in=['borrador', 'programado']).count(),
        'total_destinatarios': Destinatario.objects.filter(activo=True).count(),
        'ultimos_envios': Envio.objects.select_related('oferta')[:5],
        'ofertas_recientes': Oferta.objects.all()[:4],
    }
    return render(request, 'emails/dashboard.html', context)


# ---------- Ofertas ----------
def lista_ofertas(request):
    filtro = request.GET.get('filtro', 'todas')
    buscar = request.GET.get('q', '').strip()
    ofertas = Oferta.objects.all()
    if filtro == 'activas':
        ofertas = ofertas.filter(activa=True)
    elif filtro == 'inactivas':
        ofertas = ofertas.filter(activa=False)
    if buscar:
        ofertas = ofertas.filter(
            Q(titulo__icontains=buscar) |
            Q(subtitulo__icontains=buscar) |
            Q(descripcion_corta__icontains=buscar)
        )
    context = {
        'ofertas': ofertas, 'filtro': filtro, 'buscar': buscar,
        'contadores': {
            'todas': Oferta.objects.count(),
            'activas': Oferta.objects.filter(activa=True).count(),
            'inactivas': Oferta.objects.filter(activa=False).count(),
        },
    }
    return render(request, 'emails/ofertas_lista.html', context)


def detalle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    return render(request, 'emails/ofertas_detalle.html', {'oferta': oferta})


def crear_oferta(request):
    if request.method == 'POST':
        form = OfertaForm(request.POST, request.FILES)
        if form.is_valid():
            oferta = form.save()
            messages.success(request, f'✅ Oferta "{oferta.titulo}" creada.')
            return redirect('emails:editar_oferta', pk=oferta.pk)
        messages.error(request, '⚠️ Corrige los errores del formulario.')
    else:
        form = OfertaForm()
    return render(request, 'emails/ofertas_form.html', {'form': form, 'modo': 'crear'})


def editar_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    imagen_form = ImagenOfertaForm()

    if request.method == 'POST':
        # Subir nueva imagen adicional
        if 'subir_imagen' in request.POST:
            imagen_form = ImagenOfertaForm(request.POST, request.FILES)
            if imagen_form.is_valid():
                img = imagen_form.save(commit=False)
                img.oferta = oferta
                img.save()
                messages.success(request, '🖼️ Imagen añadida.')
                return redirect('emails:editar_oferta', pk=oferta.pk)
        else:
            form = OfertaForm(request.POST, request.FILES, instance=oferta)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Oferta actualizada.')
                return redirect('emails:lista_ofertas')
        form = OfertaForm(instance=oferta)
    else:
        form = OfertaForm(instance=oferta)

    return render(request, 'emails/ofertas_form.html', {
        'form': form, 'modo': 'editar', 'oferta': oferta,
        'imagen_form': imagen_form,
    })


def eliminar_imagen_oferta(request, pk):
    img = get_object_or_404(ImagenOferta, pk=pk)
    oferta_pk = img.oferta.pk
    img.delete()
    messages.success(request, '🗑️ Imagen eliminada.')
    return redirect('emails:editar_oferta', pk=oferta_pk)


def toggle_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    oferta.activa = not oferta.activa
    oferta.save(update_fields=['activa'])
    estado = 'activada' if oferta.activa else 'desactivada'
    messages.success(request, f'🔔 Oferta "{oferta.titulo}" {estado}.')
    return redirect(request.META.get('HTTP_REFERER', 'emails:lista_ofertas'))


def eliminar_oferta(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    if request.method == 'POST':
        titulo = oferta.titulo
        oferta.delete()
        messages.success(request, f'🗑️ Oferta "{titulo}" eliminada.')
        return redirect('emails:lista_ofertas')
    return render(request, 'emails/ofertas_eliminar.html', {'oferta': oferta})


# ---------- Destinatarios ----------
def lista_destinatarios(request):
    destinatarios = Destinatario.objects.all()
    return render(request, 'emails/destinatarios_lista.html', {
        'destinatarios': destinatarios,
        'total_activos': destinatarios.filter(activo=True).count(),
    })


def crear_destinatario(request):
    if request.method == 'POST':
        form = DestinatarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Destinatario añadido.')
            return redirect('emails:lista_destinatarios')
    else:
        form = DestinatarioForm()
    return render(request, 'emails/destinatarios_form.html',
                  {'form': form, 'modo': 'crear'})


def editar_destinatario(request, pk):
    d = get_object_or_404(Destinatario, pk=pk)
    if request.method == 'POST':
        form = DestinatarioForm(request.POST, instance=d)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Destinatario actualizado.')
            return redirect('emails:lista_destinatarios')
    else:
        form = DestinatarioForm(instance=d)
    return render(request, 'emails/destinatarios_form.html',
                  {'form': form, 'modo': 'editar', 'destinatario': d})


# ---------- Envíos ----------
def lista_envios(request):
    filtro = request.GET.get('filtro', 'todos')
    envios = Envio.objects.select_related('oferta').prefetch_related('destinatarios')
    if filtro != 'todos':
        envios = envios.filter(estado=filtro)
    context = {
        'envios': envios, 'filtro': filtro,
        'contadores': {
            'todos': Envio.objects.count(),
            'borrador': Envio.objects.filter(estado='borrador').count(),
            'programado': Envio.objects.filter(estado='programado').count(),
            'enviado': Envio.objects.filter(estado='enviado').count(),
            'fallido': Envio.objects.filter(estado='fallido').count(),
        },
    }
    return render(request, 'emails/envios_lista.html', context)


def detalle_envio(request, pk):
    envio = get_object_or_404(Envio, pk=pk)
    return render(request, 'emails/envios_detalle.html', {'envio': envio})


def crear_envio(request):
    initial = {}
    oferta_id = request.GET.get('oferta')
    if oferta_id:
        initial['oferta'] = oferta_id

    if request.method == 'POST':
        form = EnvioForm(request.POST)
        if form.is_valid():
            envio = form.save()
            messages.success(request, f'✅ Campaña "{envio.nombre_campana}" creada.')
            return redirect('emails:detalle_envio', pk=envio.pk)
        messages.error(request, '⚠️ Corrige los errores del formulario.')
    else:
        form = EnvioForm(initial=initial)
    return render(request, 'emails/envios_form.html', {'form': form, 'modo': 'crear'})


def editar_envio(request, pk):
    envio = get_object_or_404(Envio, pk=pk)
    if envio.estado in ('enviado', 'enviando'):
        messages.error(request, 'No se puede editar un envío ya procesado.')
        return redirect('emails:detalle_envio', pk=envio.pk)
    if request.method == 'POST':
        form = EnvioForm(request.POST, instance=envio)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Envío actualizado.')
            return redirect('emails:detalle_envio', pk=envio.pk)
    else:
        form = EnvioForm(instance=envio)
    return render(request, 'emails/envios_form.html',
                  {'form': form, 'modo': 'editar', 'envio': envio})


def lanzar_envio(request, pk):
    envio = get_object_or_404(Envio, pk=pk)
    if envio.estado in ('enviando', 'enviado'):
        messages.warning(request, 'Este envío ya fue procesado.')
        return redirect('emails:detalle_envio', pk=envio.pk)

    if envio.tipo_envio == 'programado' and envio.fecha_programada:
        envio.estado = 'programado'
        envio.save(update_fields=['estado'])
        messages.success(request,
                         f'⏰ Programado para {envio.fecha_programada:%d/%m/%Y %H:%M}.')
    else:
        resultado = procesar_envio(envio.id)
        messages.success(request, f'🚀 Envío procesado. {resultado}')
    return redirect('emails:detalle_envio', pk=envio.pk)


def cancelar_envio(request, pk):
    envio = get_object_or_404(Envio, pk=pk)
    if envio.estado in ('borrador', 'programado'):
        envio.estado = 'cancelado'
        envio.save(update_fields=['estado'])
        messages.success(request, '🛑 Envío cancelado.')
    return redirect('emails:detalle_envio', pk=envio.pk)


# =====================================================================
#  API REST
# =====================================================================

class OfertaViewSet(viewsets.ModelViewSet):
    queryset = Oferta.objects.all()
    serializer_class = OfertaSerializer

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        oferta = self.get_object()
        oferta.activa = not oferta.activa
        oferta.save()
        return Response({'activa': oferta.activa})


class DestinatarioViewSet(viewsets.ModelViewSet):
    queryset = Destinatario.objects.all()
    serializer_class = DestinatarioSerializer


class EnvioViewSet(viewsets.ModelViewSet):
    queryset = Envio.objects.select_related('oferta')
    serializer_class = EnvioSerializer

    @action(detail=True, methods=['post'])
    def lanzar(self, request, pk=None):
        envio = self.get_object()
        resultado = procesar_envio(envio.id)
        return Response({'mensaje': resultado})

    @action(detail=False, methods=['post'])
    def aleatorio(self, request):
        resultado = enviar_oferta_aleatoria()
        return Response({'mensaje': resultado})


@api_view(['POST'])
def recibir_oferta_api(request):
    """Endpoint para crear ofertas desde sistemas externos."""
    serializer = OfertaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)