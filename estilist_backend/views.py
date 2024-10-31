from rest_framework import viewsets
from .models import Usuarios
from .serializers import UsuariosSerializer
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.views import View
from django.http import JsonResponse
import json
import datetime

class  UsuariosViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer

from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from .models import Usuarios

class CrearUsuario(View):
    def post(self, request):
        # Leer el JSON del cuerpo de la solicitud
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
    
        # Intenta crear el objeto de Usuarios
        try:
            hora_actual = datetime.datetime.now()
            usuario_personalizado = Usuarios(
                nombre=data.get('nombre'),
                apellidopaterno=data.get('apellidopaterno'),
                apellidomaterno=data.get('apellidomaterno'),
                correo=email,
                edad=data.get('edad'),
                genero=data.get('genero'),
                tiporostro=data.get('tiporostro'),
                tipocuerpo=data.get('tipocuerpo'),
                fecharegistro=hora_actual.isoformat(),
                estado=True
            )
        except Exception as e:
            return HttpResponse(f'Error al crear el objeto Usuarios: {str(e)}', status=400)
        
        try:
            usuario_personalizado.save()
        except Exception as e:
            return HttpResponse(f'Error al crear el usuario personalizado: {str(e)}', status=400)

        try:
            usuario_auth = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                last_name=data.get('apellidopaterno'),
                first_name=data.get('nombre'),  
                date_joined=hora_actual.isoformat()
            )
            usuario_personalizado.idlogin = usuario_auth
            usuario_personalizado.save()  
            return HttpResponse('Usuario creado con éxito')
        except Exception as e:
            try:
                usuario_personalizado.delete()  
            except Exception as delete_exception:
                return HttpResponse(f'Error al eliminar el usuario personalizado: {str(delete_exception)}', status=500)

            return HttpResponse(f'Error al crear el usuario de autenticación: {str(e)} {username}', status=400)
        
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