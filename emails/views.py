from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.utils import timezone
from .models import Email, Destinatario
from .serializers import EmailSerializer, DestinatarioSerializer
from .tasks import enviar_correo, programar_envio_aleatorio


class EmailViewSet(viewsets.ModelViewSet):
    """API CRUD para correos."""
    queryset = Email.objects.all()
    serializer_class = EmailSerializer

    @action(detail=True, methods=['post'])
    def enviar_ahora(self, request, pk=None):
        """Envía un correo inmediatamente."""
        email = self.get_object()
        if email.estado == 'enviado':
            return Response(
                {'error': 'Este correo ya fue enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        enviar_correo.delay(email.id)
        return Response({'mensaje': 'Correo enviado en cola.'})

    @action(detail=True, methods=['post'])
    def programar(self, request, pk=None):
        """Programa un envío para una fecha específica."""
        email = self.get_object()
        fecha = request.data.get('fecha_programada')
        if not fecha:
            return Response(
                {'error': 'Debes proporcionar fecha_programada.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        email.fecha_programada = fecha
        email.estado = 'programado'
        email.save()
        return Response({'mensaje': 'Correo programado exitosamente.'})

    @action(detail=False, methods=['post'])
    def programar_aleatorio(self, request):
        """Programa el envío de un correo aleatorio cada X tiempo."""
        intervalo = request.data.get('intervalo', 3600)  # segundos
        programar_envio_aleatorio.delay(intervalo)
        return Response({'mensaje': f'Envío aleatorio programado cada {intervalo} segundos.'})


class DestinatarioViewSet(viewsets.ModelViewSet):
    """API CRUD para destinatarios."""
    queryset = Destinatario.objects.all()
    serializer_class = DestinatarioSerializer


@api_view(['POST'])
def recibir_email_api(request):
    """Endpoint para recibir correos desde API externa y guardarlos en BD."""
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)