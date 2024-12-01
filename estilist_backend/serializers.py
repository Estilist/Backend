from rest_framework import serializers
from .models import Usuarios, Medidas, Colorimetria, Streak
from django.contrib.auth.models import User as auth

class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = '__all__'
        
class MeasuerementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medidas
        fields = '__all__'
        
class AuthUserSerialize (serializers.ModelSerializer):
    class Meta:
        model = auth
        fields = '__all__'
class ColorimetriaSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Colorimetria
        fields = '__all__'

class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = '__all__'