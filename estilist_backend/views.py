from rest_framework import viewsets
from .models import Usuarios, Medidas
from .serializers import UsuariosSerializer, AuthUserSerialize, MeasuerementsSerializer
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

class MeauserementsViewSet(viewsets.ModelViewSet):
    queryset = Medidas.objects.all()
    serializer_class = MeasuerementsSerializer

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
    def BodyType(self, sexo, pecho, cadera, cintura):
                    
            proporciones = {
                'male': {
                    'Rectángulo': (90, 85, 90),
                    'Triángulo Invertido (V)': (105, 80, 90),
                    'Ovalado (Manzana)': (100, 95, 90),
                    'Trapecio (Triangular)': (105, 90, 95),
                    'Mesomorfo': (100, 85, 95)
                },
                'female': {
                    'Reloj de Arena': (90, 60, 90),
                    'Rectangular': (85, 75, 85),
                    'Triángulo (Pera)': (80, 70, 100),
                    'Triángulo Invertido': (100, 75, 85),
                    'Ovalado (Manzana)': (95, 85, 95),
                    'Atlético': (90, 70, 85)
                }
            }
            
            puntuaciones = {}
            
            for tipo, medidas in proporciones[sexo].items():
                ideal_pecho, ideal_cintura, ideal_cadera = medidas
                puntuacion = 0
                
                # Comparar cada medida con la medida ideal
                if pecho:
                    puntuacion += max(0, 100 - abs(pecho - ideal_pecho))
                if cintura:
                    puntuacion += max(0, 100 - abs(cintura - ideal_cintura))
                if cadera:
                    puntuacion += max(0, 100 - abs(cadera - ideal_cadera))
                
                puntuaciones[tipo] = puntuacion
            
            tipo_cuerpo = max(puntuaciones, key=puntuaciones.get)
            
            return tipo_cuerpo    
        
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
            user.tipocuerpo = self.BodyType(user.genero, user_medidas.pecho, user_medidas.cadera, user_medidas.cintura)
            try:
                user.save()
            except:
                return JsonResponse({'error': 'Error al actualizar el tipo de cuerpo'}, status=500)
            return JsonResponse({'message': 'Medidas actualizadas con exito'}, status=200)
        
        user.tipocuerpo = self.BodyType(user.genero, user_medidas.pecho, user_medidas.cadera, user_medidas.cintura)
        try:
            user.save()
        except:
            return JsonResponse({'error': 'Error al actualizar el tipo de cuerpo'}, status=500)
        return JsonResponse({'message': 'Medidas creadas con exito'}, status=201)
        
            
