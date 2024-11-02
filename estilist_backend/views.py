from rest_framework import viewsets
from .models import Usuarios
from .serializers import UsuariosSerializer, AuthUserSerialize
from django.contrib.auth.models import User
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


class CrearSuperUsuario(View):
    def post(self, request):
        # Leer el JSON del cuerpo de la solicitud
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not username:
            return JsonResponse({'error': 'The given username must be set'}, status=400)

        # Crea el usuario
        usuario_auth = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )

        # Crea el objeto de Usuarios y relaciona
        usuario_personalizado = Usuarios.objects.create(
            idlogin=usuario_auth,
            nombre=data.get('nombre'),
            apellidopaterno=data.get('apellidopaterno'),
            apellidomaterno=data.get('apellidomaterno'),
            correo=email,
            edad=data.get('edad'),
            genero=data.get('genero'),
            tiporostro=data.get('tiporostro'),
            tipocuerpo=data.get('tipocuerpo'),
            fecharegistro=data.get('fecharegistro'),
            estado=True
        )

        return JsonResponse({'message': 'Usuario creado con éxito'}, status=201)
