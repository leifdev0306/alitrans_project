from rest_framework import serializers
from .models import Oferta, ImagenOferta, Destinatario, Envio


class ImagenOfertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenOferta
        fields = '__all__'


class OfertaSerializer(serializers.ModelSerializer):
    esta_vigente = serializers.ReadOnlyField()
    total_envios = serializers.ReadOnlyField()
    imagenes = ImagenOfertaSerializer(many=True, read_only=True)

    class Meta:
        model = Oferta
        fields = '__all__'


class DestinatarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinatario
        fields = '__all__'


class EnvioSerializer(serializers.ModelSerializer):
    oferta_titulo = serializers.CharField(source='oferta.titulo', read_only=True)

    class Meta:
        model = Envio
        fields = '__all__'
        read_only_fields = [
            'estado', 'total_enviados', 'total_fallidos',
            'fecha_creacion', 'fecha_envio',
        ]