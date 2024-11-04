from rest_framework import viewsets
from .models import Usuarios, Medidas
from .serializers import UsuariosSerializer, AuthUserSerialize
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.models import User as auth
import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError

class UsuariosViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer


class AuthUserViewSet (viewsets.ModelViewSet):
    queryset = auth.objects.all()
    serializer_class = AuthUserSerialize


class CreateUser(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        password = data.get('contrasena')
        password_hashed = make_password(
        password, salt=None, hasher='pbkdf2_sha256')
        hora_actual = datetime.datetime.now()
        try:
            usuario, created = Usuarios.objects.get_or_create(
                correo=data.get('correo'),
                defaults={
                    'contrasena': password_hashed,
                    'nombre': data.get('nombre'),
                    'apellidopaterno': data.get('apellidopaterno'),
                    'apellidomaterno': data.get('apellidomaterno'),
                    'edad': data.get('edad'),
                    'genero': data.get('genero'),
                    'fecharegistro': hora_actual,
                    'ultimoacceso': hora_actual,
                    'pais': data.get('pais'),
                    'estado': True
                }
            )
        except Exception:
            return JsonResponse({'error': 'Error al crear el usuario'}, status=500)
        
        if not created:
            return JsonResponse({'error': 'El usuario ya existe',
                                 'idUsuario': Usuarios.objects.get(correo=data.get('correo')).idusuario}, status=400)
        return JsonResponse({'message': 'Usuario creado con éxito',
                                'idUsuario': usuario.idusuario}, status=201)   

class CheckUser(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        username = data.get('correo')
        password = data.get('contrasena')

        try:
            user = Usuarios.objects.get(correo=username)
        except:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)

        if  check_password(password, user.contrasena):
            hora_actual = datetime.datetime.now()
            user.last_login = hora_actual
            try:
                user.save()
            except Exception:
                return JsonResponse({'error': 'Error al actualizar la fecha de ultimo acceso'}, status=500)
            return JsonResponse({'idUsuario': user.idusuario,
                                 'login': user.last_login}, status=200)
        else:
            return JsonResponse({'error': 'Contraseña incorrecta'}, status=401)

class UserMeasurements(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        id = data.get('idusuario')
        try:
            user = Usuarios.objects.get(idusuario= id)
        except:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        try:
            user_medidas, created = Medidas.objects.get_or_create(
                idusuario=user,
                defaults={
                    'altura': data.get('altura'),
                    'peso': data.get('peso'),
                    'pecho': data.get('pecho'),
                    'cintura': data.get('cintura'),
                    'cadera': data.get('cadera'),
                    'entrepierna': data.get('entrepierna'),
                    'fechaactualizacion': datetime.datetime.now()
                }
            )
        except:
            return JsonResponse({'error': 'Error al crear las medidas'}, status=500)
        
        if not created:
            user_medidas.altura = data.get('altura')
            user_medidas.peso = data.get('peso')
            user_medidas.pecho = data.get('pecho')
            user_medidas.cintura = data.get('cintura')
            user_medidas.cadera = data.get('cadera')
            user_medidas.entrepierna = data.get('entrepierna')
            user_medidas.fechaactualizacion = datetime.datetime.now()
            try:
                user_medidas.save()
            except:
                return JsonResponse({'error': 'Error al actualizar las medidas'}, status=500)
            return JsonResponse({'message': 'Medidas actualizadas con exito'}, status=200)
        
        return JsonResponse({'message': 'Medidas creadas con exito'}, status=201)
            
       

