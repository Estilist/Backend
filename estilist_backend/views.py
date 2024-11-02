from rest_framework import viewsets
from .models import Usuarios
from .serializers import UsuariosSerializer, AuthUserSerialize
from django.contrib.auth.models import User
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.models import User as auth
import datetime


class UsuariosViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer

class AuthUserViewSet (viewsets.ModelViewSet):
    queryset = auth.objects.all()
    serializer_class = AuthUserSerialize

class CreateUser(View):
    def post(self, request):
        # Leer el JSON del cuerpo de la solicitud
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        password = data.get('contrasena')
        email = data.get('correo')
        username = email
    
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
                pais=data.get('pais'),
                fecharegistro=hora_actual.isoformat(),
                estado=True
            )
        except Exception as e:
                        return JsonResponse({'error' : 'Error al crear el usuario personalizado'}, status=400)

        
        try:
            usuario_personalizado.save()
        except Exception as e:
                        return JsonResponse({'error' : 'Error al guardar el usuario personalizado en la base de datos',
                                             'causa' : 'Valores repetidos'}, status=400)


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

            return JsonResponse({'idUsuario': usuario_personalizado.idusuario}, status=201)
        except Exception as e:
            try:
                usuario_personalizado.delete()  
            except Exception:
                return JsonResponse({'error' : 'Error eliminar usuario personalizado no completa'}, status=500)

        return JsonResponse({'error' : 'Error al crear un usuario'}, status=500)
        
class CheckUser(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        username = data.get('correo')
        password = data.get('contrasena')
        
        try:
            user = auth.objects.get(username=username)
        except auth.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        if user.check_password(password):
            hora_actual = datetime.datetime.now()
            user.last_login = hora_actual.isoformat()
            try:
                user.save()
            except Exception:
                return JsonResponse({'error': 'Error al actualizar la fecha de ultimo acceso'}, status=500)
            try:
                owner = Usuarios.objects.get(idlogin=user)
            except Usuarios.DoesNotExist:
                return JsonResponse({'error': 'Falla de validacion en la creacion del usuario, accedio al registro mas no se registro en la tabla Usuarios'}, status=404)
            return JsonResponse({'idUsuario': owner.idusuario}, status=200)
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
