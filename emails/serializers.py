from rest_framework import serializers
from .models import Email, Destinatario


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_envio', 'estado']


class DestinatarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destinatario
        fields = '__all__'