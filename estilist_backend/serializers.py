from rest_framework import serializers
from .models import Usuarios
from django.contrib.auth.models import User as auth

class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = '__all__'
        
class AuthUserSerialize (serializers.ModelSerializer):
    class Meta:
        model = auth
        fields = '__all__'

class RegisterSerializer (serializers.)