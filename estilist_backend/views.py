from rest_framework import viewsets, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Usuarios, Medidas, Preferencias, Colorimetria, Feedback, Rankings, Recomendaciones, ImagenesRostros, Streak
from .serializers import UsuariosSerializer, MeasuerementsSerializer, ColorimetriaSerializer, StreakSerializer
from django.views import View
from django.utils import timezone
from django.http import JsonResponse
import json, datetime
from django.contrib.auth.hashers import make_password, check_password
from estilist_project import settings
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import os, requests, uuid
from datetime import datetime, timedelta
import logging
from django.db.models import Q
from random import choice
from django.db import transaction
import random

class UsuariosViewSet(viewsets.ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="No está permitido crear nuevas mediciones.")

class MeauserementsViewSet(viewsets.ModelViewSet):
    
    queryset = Medidas.objects.all()
    serializer_class = MeasuerementsSerializer
    lookup_field = 'idusuario'
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="No está permitido crear nuevas mediciones.")   

class ColorimetriaViewSet(viewsets.ModelViewSet):
    serializer_class = ColorimetriaSerializer

    def get_queryset(self):
        idusuario = self.request.query_params.get('idusuario')
        if idusuario:
            return Colorimetria.objects.filter(idusuario=idusuario)
        return Colorimetria.objects.all()
    
class StreakView(viewsets.ModelViewSet):
    queryset = Streak.objects.all()
    serializer_class = StreakSerializer
    lookup_field = 'idusuario'
    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST", detail="No está permitido crear nuevas mediciones.")
    

class CreateUser(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        password = data.get('contrasena')
        password_hashed = make_password(
        password, salt=None, hasher='pbkdf2_sha256')
        hora_actual = datetime.now()
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
            if usuario.estado == False:
                Colorimetria.objects.filter(idusuario = usuario.idusuario).delete()
                Medidas.objects.filter(idusuario = usuario.idusuario).delete()
                Rankings.objects.filter(idusuario = usuario.idusuario).delete()
                Feedback.objects.filter(idusuario = usuario.idusuario).delete()
                Preferencias.objects.filter(idusuario = usuario.idusuario).delete()
                ImagenesRostros.objects.filter(idusuario = usuario.idusuario).delete()
                Usuarios.objects.filter(idusuario = usuario.idusuario).delete()
                try:
                    usuario = Usuarios.objects.create(
                        correo= data.get('correo'),
                        contrasena= password_hashed,
                        nombre= data.get('nombre'),
                        apellidopaterno= data.get('apellidopaterno'),
                        apellidomaterno= data.get('apellidomaterno'),
                        edad= data.get('edad'),
                        genero= data.get('genero'),
                        fecharegistro= hora_actual,
                        ultimoacceso= hora_actual,
                        pais= data.get('pais'),
                        estado= True
                    )
                except:
                    return JsonResponse({'error': 'Error al habilitar el usuario'}, status=500)
                return JsonResponse({'message': 'Usuario habilitado con éxito',
                                 'idUsuario': usuario.idusuario}, status=200)
            else:
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

        if user.estado == False:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        if  check_password(password, user.contrasena):
            hora_actual = datetime.now()
            user.last_login = hora_actual
            try:
                user.save()
            except Exception:
                return JsonResponse({'error': 'Error al actualizar la fecha de ultimo acceso'}, status=500)
            return JsonResponse({'idUsuario': user.idusuario,
                                 'login': user.last_login}, status=200)
        else:
            return JsonResponse({'error': 'Contraseña incorrecta'}, status=401)

class DeleteUser(View):
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
        
        user.estado = False
        try:
            user.save()
        except:
            return JsonResponse({'error': 'Error al deshabilitar el usuario'}, status=500)
        return JsonResponse({'message': 'Usuario deshabilitado con exito'}, status=200)

class UserMeasurements(View):
    def BodyType(self, sexo, pecho, cadera, cintura):
                    
            proporciones = {
                'male': {
                    'Reloj de Arena': (90, 60, 90),
                    'Rectangular': (90, 85, 90),
                    'Triángulo (Pera)': (80, 80, 90),
                    'Triángulo Invertido': (100, 75, 85),
                    'Ovalado (Manzana)': (95, 105, 95),
                    'Atlético': (100, 85, 95)
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
        
        if user.estado == False:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        try:
            user_medidas, created = Medidas.objects.get_or_create(
                idusuario=user,
                defaults={
                    'altura': data.get('altura'),
                    'peso': data.get('peso'),
                    'hombros': data.get('hombros'),
                    'cintura': data.get('cintura'),
                    'cadera': data.get('cadera'),
                    'fechaactualizacion': datetime.now()
                }
            )
        except:
            return JsonResponse({'error': 'Error al crear las medidas'}, status=500)
        
        if not created:
            user_medidas.altura = data.get('altura')
            user_medidas.peso = data.get('peso')
            user_medidas.hombros = data.get('hombros')
            user_medidas.cintura = data.get('cintura')
            user_medidas.cadera = data.get('cadera')
            user_medidas.fechaactualizacion = datetime.now()
            try:
                user_medidas.save()
            except:
                return JsonResponse({'error': 'Error al actualizar las medidas'}, status=500)
            user.tipocuerpo = self.BodyType(user.genero, user_medidas.hombros, user_medidas.cadera, user_medidas.cintura)
            try:
                user.save()
            except:
                return JsonResponse({'error': 'Error al actualizar el tipo de cuerpo'}, status=500)
            return JsonResponse({'message': 'Medidas actualizadas con exito'}, status=200)
        
        user.tipocuerpo = self.BodyType(user.genero, user_medidas.hombros, user_medidas.cadera, user_medidas.cintura)
        try:
            user.save()
        except:
            return JsonResponse({'error': 'Error al actualizar el tipo de cuerpo'}, status=500)
        return JsonResponse({'message': 'Medidas creadas con exito'}, status=201)

def hex_to_rgb(hex_code):
        hex_code = hex_code.lstrip('#')
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def color_distance(c1, c2):
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

class FacialRecognition(APIView):
    parser_classes = [MultiPartParser, FormParser]  # Permite recibir multipart/form-data y x-www-form-urlencoded

    WARM_TONES = [
    hex_to_rgb('#FFD3AD'),  # Muy claro
    hex_to_rgb('#E6B994'),  # Claro
    hex_to_rgb('#D49A79'),  # Medio
    hex_to_rgb('#B07959'),  # Bronceado
    hex_to_rgb('#87573A')   # Oscuro cálido
    ]

    COLD_TONES = [
        hex_to_rgb('#FFD9CB'),  # Muy claro
        hex_to_rgb('#E0B2AB'),  # Claro
        hex_to_rgb('#B5838D'),  # Medio
        hex_to_rgb('#885B6E'),  # Bronceado frío
        hex_to_rgb('#5A3241')  # Oscuro frío
    ]

    NEUTRAL_TONES = [
        hex_to_rgb('#F0D5C9'),  # Muy claro
        hex_to_rgb('#D9B6A3'),  # Claro
        hex_to_rgb('#C2A185'),  # Medio
        hex_to_rgb('#8C7B6B'),  # Bronceado
        hex_to_rgb('#5D4631')   # Oscuro neutral
    ]
        
    THRESHOLD = 120  # Adjust the threshold as needed
    
    def match_tone(self, subtono_rgb):
        min_distance = float('inf')
        matched_tone = 'Neutro'

        for tone in ['Frio', 'Calido', 'Neutro']:
            if tone == 'Frio':
                tone_list = self.COLD_TONES
            elif tone == 'Calido':
                tone_list = self.WARM_TONES
            else:
                tone_list = self.NEUTRAL_TONES

            for base_color in tone_list:
                distance = color_distance(subtono_rgb, base_color)
                if distance < min_distance and distance <= self.THRESHOLD:
                    min_distance = distance
                    matched_tone = tone

        return matched_tone

    def determine_skin_tone(self, subtono1):
        try:
            subtones = [
                hex_to_rgb(subtono1),
            ]
        except ValueError:
            return 'Neutro'

        tone_counts = {'Frio': 0, 'Calido': 0, 'Neutro': 0}

        for subtone in subtones:
            tone = self.match_tone(subtone)
            tone_counts[tone] += 1

        if tone_counts['Frio'] == 1:
            return 'Frio'
        elif tone_counts['Calido'] == 1:
            return 'Calido'
        else:
            return 'Neutro'
    
    def post(self, request):
        
        img_url = request.data.get('url')
        
        url = 'https://identiface.ambitioussea-007d0918.westus3.azurecontainerapps.io/predict/'
        
        
        id = request.data.get('idusuario')
        try:
            user = Usuarios.objects.get(idusuario= id)
        except:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        if user.estado == False:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        hora_actual = datetime.now()
        try:
            ImagenesRostros.objects.create(idusuario=user, url=img_url, fechasubida=hora_actual)
        except:
            return JsonResponse({'error': 'Error al guardar la imagen'}, status=500)
        
        response = requests.post(url, data={'url': img_url})
        
        attributes = response.json()
        
        user.tiporostro = attributes.get('forma')
        try:
            user.save()
        except:
            return JsonResponse({'error': 'Error al actualizar el tipo de rostro'}, status=500)
        
        tonos_piel = attributes.get('tono_piel', [])
        
        tono = self.determine_skin_tone(tonos_piel[0])
        
        tonos =  ",".join(tonos_piel)
        
        
        try:
            colorimetria, created = Colorimetria.objects.get_or_create(
                idusuario=user,
                tipo='Subtonos',
                defaults={
                    'color': tonos,
                    'tono': tono
                }
            )
        except:
            return JsonResponse({'error': 'Error al crear la colorimetria'}, status=500)
        
        if not created:
            Colorimetria.objects.filter(idusuario = id).delete()
            tono = Colorimetria.objects.create(idusuario=user, tipo='Subtonos', color=tonos, tono=tono)
            if tono.tono == 'Frio':
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFC0CB', tono='Frio')  # Rosado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#E75480', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D2042D', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#990033', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B0E0E6', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#4169E1', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#000080', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#B2A59F', tono='Frio')  # Rubio cenizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#4B4845', tono='Frio')  # Castaño oscuro cenizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#5B2333', tono='Frio')  # Vino
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#1A1C3B', tono='Frio')  # Negro azulado
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E5E4E2', tono='Frio')  # Oro blanco
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#C0C0C0', tono='Frio')  # Plata
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E6E6FA', tono='Frio')  # Platino
            elif tono.tono == 'Calido':
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFFACD', tono='Calido')  # Amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFD700', tono='Calido')  # Dorado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#DAA520', tono='Calido')  # Dorado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFDAB9', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFB07C', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B87333', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#CD7F32', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#D7B27C', tono='Calido')  # Rubio dorado
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#8B5E3C', tono='Calido')  # Castaño claro
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#B35A1F', tono='Calido')  # Cobre
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#5C4033', tono='Calido')  # Castaño oscuro
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#FFD700', tono='Calido')  # Oro amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#B76E79', tono='Calido')  # Oro rosa
            else:
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#F7E7CE', tono='Neutro')  # Beige claro
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D3BFAE', tono='Neutro')  # Beige
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#708090', tono='Neutro')  # Gris azulado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#8B8589', tono='Neutro')  # Gris pardo
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B5A642', tono='Neutro')  # Amarillo oliva
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#E6E6FA', tono='Neutro')  # Lavanda
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D8A9A9', tono='Neutro')  # Rosa palido
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#C8B79E', tono='Neutro')  # Rubio neutro
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#7B3F00', tono='Neutro')  # Castaño chocolate
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#9C5221', tono='Neutro')  # Marrón cobrizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#2D2D2D', tono='Neutro')  # Negro suave
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#FFD700', tono='Neutro')  # Oro amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E5E4E2', tono='Neutro')  # Oro blanco
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#B76E79', tono='Neutro')  # Oro rosa
            return JsonResponse({'msg':'Colorimetria actualizada con exito'})
        if created:
            if colorimetria.tono == 'Frio':
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFC0CB', tono='Frio')  # Rosado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#E75480', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D2042D', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#990033', tono='Frio')  # Rojos
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B0E0E6', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#4169E1', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#000080', tono='Frio')  # Azules
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#B2A59F', tono='Frio')  # Rubio cenizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#4B4845', tono='Frio')  # Castaño oscuro cenizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#5B2333', tono='Frio')  # Vino
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#1A1C3B', tono='Frio')  # Negro azulado
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E5E4E2', tono='Frio')  # Oro blanco
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#C0C0C0', tono='Frio')  # Plata
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E6E6FA', tono='Frio')  # Platino
            elif colorimetria.tono == 'Calido':
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFFACD', tono='Calido')  # Amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFD700', tono='Calido')  # Dorado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#DAA520', tono='Calido')  # Dorado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFDAB9', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#FFB07C', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B87333', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#CD7F32', tono='Calido')  # Melocoton
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#D7B27C', tono='Calido')  # Rubio dorado
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#8B5E3C', tono='Calido')  # Castaño claro
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#B35A1F', tono='Calido')  # Cobre
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#5C4033', tono='Calido')  # Castaño oscuro
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#FFD700', tono='Calido')  # Oro amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#B76E79', tono='Calido')  # Oro rosa
            else:
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#F7E7CE', tono='Neutro')  # Beige claro
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D3BFAE', tono='Neutro')  # Beige
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#708090', tono='Neutro')  # Gris azulado
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#8B8589', tono='Neutro')  # Gris pardo
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#B5A642', tono='Neutro')  # Amarillo oliva
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#E6E6FA', tono='Neutro')  # Lavanda
                Colorimetria.objects.create(idusuario=user, tipo='Ropa', color='#D8A9A9', tono='Neutro')  # Rosa palido
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#C8B79E', tono='Neutro')  # Rubio neutro
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#7B3F00', tono='Neutro')  # Castaño chocolate
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#9C5221', tono='Neutro')  # Marrón cobrizo
                Colorimetria.objects.create(idusuario=user, tipo='Cabello', color='#2D2D2D', tono='Neutro')  # Negro suave
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#FFD700', tono='Neutro')  # Oro amarillo
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#E5E4E2', tono='Neutro')  # Oro blanco
                Colorimetria.objects.create(idusuario=user, tipo='Joyeria', color='#B76E79', tono='Neutro')  # Oro rosa
            return JsonResponse({'msg':'Colorimetria creada con exito'})
                
class UserPreferences(View):
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
        
        if user.estado ==  False:
            return JsonResponse({"error" : "Usuario deshabilitado"}, status=401)
        
        try:
            user_preferences, created = Preferencias.objects.get_or_create(
                idusuario=user,
                defaults={
                    'ajusteropa': data.get('ajusteropa'),
                    'tintecabello': data.get('tintecabello'),
                    'cortecabello': data.get('cortecabello'),
                    'accesorios': data.get('accesorios'),
                    'joyeria': data.get('joyeria'),
                    'ropa': data.get('ropa'),
                    'maquillaje': data.get('maquillaje'),
                    'recomendaciones': data.get('recomendaciones')
                }
            )
        except:
            return JsonResponse({'error': 'Error al crear las preferencias'}, status=500)
        
        if not created:
            user_preferences.ajusteropa = data.get('ajusteropa')
            user_preferences.tintecabello = data.get('tintecabello')
            user_preferences.cortecabello = data.get('cortecabello')
            user_preferences.accesorios = data.get('accesorios')
            user_preferences.joyeria = data.get('joyeria')
            user_preferences.ropa = data.get('ropa')
            user_preferences.maquillaje = data.get('maquillaje')
            user_preferences.recomendaciones = data.get('recomendaciones')
            try:
                user_preferences.save()
            except:
                return JsonResponse({'error': 'Error al actualizar las preferencias'}, status=500)
            return JsonResponse({'message': 'Preferencias actualizadas con exito'}, status=200)
        
        return JsonResponse({'message': 'Preferencias creadas con exito'}, status=201)

class GetUploadUrlView(APIView):
    def get(self, request, format=None):
        filename = request.query_params.get('filename')
        filetype = request.query_params.get('filetype')

        if not filename or not filetype:
            return JsonResponse({'error': 'Faltan parametros: filename y filetype son requeridos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Verificar configuraciones
        logging.debug(f"AZURE_STORAGE_ACCOUNT_NAME: {settings.AZURE_STORAGE_ACCOUNT_NAME}")
        logging.debug(f"AZURE_STORAGE_ACCOUNT_ENDPOINT: {settings.AZURE_STORAGE_ACCOUNT_ENDPOINT}")

        if not settings.AZURE_STORAGE_ACCOUNT_NAME or not settings.AZURE_STORAGE_ACCOUNT_KEY:
            return JsonResponse({'error': 'Configuraciones de Azure faltantes.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generar un nombre único para el blob
        blob_name = f"{uuid.uuid4()}_{filename}"

        # Crear el cliente de Blob Storage
        try:
            blob_service_client = BlobServiceClient(
                account_url=settings.AZURE_STORAGE_ACCOUNT_ENDPOINT,
                credential=settings.AZURE_STORAGE_ACCOUNT_KEY
            )
        except ValueError as e:
            logging.error(f"Error al crear BlobServiceClient: {e}")
            return JsonResponse({'error': 'Configuración de Azure inválida.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)

        if not container_client.exists():
            return JsonResponse({'error': 'El contenedor especificado no existe.'},
                            status=status.HTTP_400_BAD_REQUEST)

        sas_token = generate_blob_sas(
            account_name=settings.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=settings.AZURE_STORAGE_CONTAINER_NAME,
            blob_name=blob_name,
            account_key=settings.AZURE_STORAGE_ACCOUNT_KEY,
            permission=BlobSasPermissions(write=True),
            expiry=datetime.utcnow() + timedelta(hours=1)  # La SAS expira en 1 hora
        )

        upload_url = f"{settings.AZURE_STORAGE_ACCOUNT_ENDPOINT}/{settings.AZURE_STORAGE_CONTAINER_NAME}/{blob_name}?{sas_token}"
        file_url = f"{settings.AZURE_STORAGE_ACCOUNT_ENDPOINT}/{settings.AZURE_STORAGE_CONTAINER_NAME}/{blob_name}"

        return JsonResponse({
            'uploadUrl': upload_url,
            'fileUrl': file_url
        }, status=status.HTTP_200_OK)
        
class ClothesRecomendation(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        id = data.get('idusuario')
        evento = data.get('evento')
        try:
            user = Usuarios.objects.get(idusuario= id)
        except:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        if user.estado == False:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        try:
            color = Colorimetria.objects.get(
                Q(idusuario=user),
                Q(tipo='Subtonos')
            )
        except:
            return JsonResponse({'error': 'Colorimetria no encontrada'}, status=404)
        
        try:
            style = Preferencias.objects.get(
                idusuario=user
            )
        except:
            return JsonResponse({'error': 'Preferencias no encontradas'}, status=404)

        colors = []
        if color.tono == 'Frio':
            colors = ["Rosado", "Rojo fucsia", "Rojo carmín", "Rojo vino oscuro", "Azul pálido", "Azul real", "Azul marino"]
            jewels = ["Oro blanco", "Plata", "Platino", style.joyeria]
        elif color.tono == 'Calido':
            colors = ["Amarillo claro", "Dorado brillante", "Dorado oscuro", "Melocotón pálido", "Melocotón vibrante", "Cobre rojizo", "Bronce"]
            jewels = ["Oro amarillo", "Oro rosa", style.joyeria]
        else:
            colors = ["Beige claro", "Beige suave", "Gris azulado", "Gris pardo", "Amarillo oliva", "Lavanda", "Rosa pálido"]
            jewels = ["Oro amarillo", "Oro blanco", "Oro rosa", style.joyeria]   
        
        ropa = 0.75
        calzado = 0.835
        accesorios = 0.916
        prob = random.random()
        # ******************* USING EVENT ***********************
        if evento != None:
            if evento != "Streak": 
                if evento == "accesorios":
                    if prob < 0.50:
                        color_queries = Q()
                        for color_item in colors:
                            color_queries |= Q(etiquetas__Color__contains=[color_item])
                        ids = list(Recomendaciones.objects.filter(
                            color_queries,
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Accesorio", 
                            rankings__isnull=True,
                            etiquetas__Estilo__contains=style.accesorios,
                        ).values_list('idrecomendacion', flat=True))
                    else:
                        jewels_queries = Q()
                        for jewel in jewels:
                            jewels_queries |= Q(tipo__icontains="Joyería") & Q(etiquetas__Color__contains=[jewel])
                        ids = list(Recomendaciones.objects.filter(
                            jewels_queries,
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Joyería", 
                            rankings__isnull=True,
                        ).values_list('idrecomendacion', flat=True))
                else:
                    color_queries = Q()
                    for color_item in colors:
                        color_queries |= Q(etiquetas__Color__contains=[color_item])
                    ids = list(Recomendaciones.objects.filter(
                        color_queries,
                        (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                        tipo__icontains="Ropa", 
                        rankings__isnull=True,
                        etiquetas__Evento__contains=evento,
                    ).values_list('idrecomendacion', flat=True))
            else: # ******************* STREAK FUNCTION ***********************
                streak_type = data.get('streak_type')
                if streak_type == "Mi estilo":
                    color_queries = Q()
                    for color_item in colors:
                        color_queries |= Q(etiquetas__Color__contains=[color_item])
                    ids = list(Recomendaciones.objects.filter(
                            color_queries,
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Ropa", 
                            rankings__isnull=True,
                            etiquetas__Estilo__contains=style.ropa,
                        ).values_list('idrecomendacion', flat=True))
                elif streak_type == "Experimentar":
                    ids = list(Recomendaciones.objects.filter(
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Ropa", 
                            rankings__isnull=True,
                        ).values_list('idrecomendacion', flat=True))
        else: # ******************* USING STYLE ***********************
            if prob < ropa: # ***** ROPA *****
                color_queries = Q()
                for color_item in colors:
                    color_queries |= Q(etiquetas__Color__contains=[color_item])
                if prob < 0.375:
                    ids = list(Recomendaciones.objects.filter(
                        color_queries,
                        (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                        tipo__icontains="Ropa", 
                        rankings__isnull=True,
                        etiquetas__Estilo__contains=style.ropa,
                    ).values_list('idrecomendacion', flat=True))
                    if len(ids) == 0: # ************************** IF LEN OF IDS IS 0 THEN GET ALL CLOTHES ************************
                        ids = list(Recomendaciones.objects.filter(
                        color_queries,
                        (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                        tipo__icontains="Ropa", 
                        rankings__isnull=True,
                        ).values_list('idrecomendacion', flat=True))
                else:
                    if prob < 0.45:
                        ids = list(Recomendaciones.objects.filter(
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Ropa", 
                            rankings__isnull=True,
                        ).values_list('idrecomendacion', flat=True))
                    else:
                        ids = list(Recomendaciones.objects.filter(
                            color_queries,
                            (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                            tipo__icontains="Ropa", 
                            rankings__isnull=True,
                        ).values_list('idrecomendacion', flat=True))
            elif prob < calzado: # ***** CALZADO *****
                color_queries = Q()
                for color_item in colors:
                    color_queries |= Q(etiquetas__Color__contains=[color_item])
                ids = list(Recomendaciones.objects.filter(
                    color_queries,
                    (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                    tipo__icontains="Calzado", 
                    rankings__isnull=True,
                    etiquetas__Estilo__contains=style.ropa,
                ).values_list('idrecomendacion', flat=True))
            elif prob < accesorios: # ***** ACCESORIOS *****
                color_queries = Q()
                for color_item in colors:
                    color_queries |= Q(etiquetas__Color__contains=[color_item])
                ids = list(Recomendaciones.objects.filter(
                    color_queries,
                    (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                    tipo__icontains="Accesorio", 
                    rankings__isnull=True,
                    etiquetas__Estilo__contains=style.accesorios,
                ).values_list('idrecomendacion', flat=True))
            else: # ***** JOYERIA *****
                jewels_queries = Q()
                for jewel in jewels:
                    jewels_queries |= Q(tipo__icontains="Joyería") & Q(etiquetas__Color__contains=[jewel])
                ids = list(Recomendaciones.objects.filter(
                    jewels_queries,
                    (Q(genero__contains=style.recomendaciones) | Q(genero__contains="Unisex")), 
                    tipo__icontains="Joyería", 
                    rankings__isnull=True,
                ).values_list('idrecomendacion', flat=True))

        recomendation = Recomendaciones.objects.get(idrecomendacion=choice(ids)) if ids else None

        return JsonResponse({'img': recomendation.urlimagen,
                                'id': recomendation.idrecomendacion,
                                'etiquetas' : recomendation.etiquetas}, status=200)

class RankRecomendation(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        id = data.get('idusuario')
        
        try:
            user = Usuarios.objects.get(idusuario=id)
        except Usuarios.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        if not user.estado:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        try:
            recomendation = Recomendaciones.objects.get(idrecomendacion=data.get('idrecomendacion'))
        except Recomendaciones.DoesNotExist:
            return JsonResponse({'error': 'Recomendacion no encontrada'}, status=404)
        
        ranking, created = Rankings.objects.get_or_create(
            idusuario=user,
            idrecomendacion=recomendation,
            defaults = {
                'ranking': data.get('ranking'),
                'fecha': datetime.now()
            }
        )
        
        if not created:
            ranking.ranking = data.get('ranking')
            ranking.fecha = datetime.now()
            try:
                ranking.save()
            except:
                return JsonResponse({'error': 'Error al actualizar el ranking'}, status=500)
        
        nuevo_ranking = data.get('ranking')
        if nuevo_ranking is None:
            return JsonResponse({'error': 'Ranking no proporcionado'}, status=400)

        try:
            nuevo_ranking = int(nuevo_ranking)
        except ValueError:
            return JsonResponse({'error': 'Ranking debe ser un número'}, status=400)

        try:
            with transaction.atomic():
                if recomendation.cont_ranking == 0:
                    recomendation.ranking = nuevo_ranking
                    recomendation.cont_ranking = 1
                else:
                    recomendation.ranking = (
                        (recomendation.ranking * recomendation.cont_ranking + nuevo_ranking) /
                        (recomendation.cont_ranking + 1)
                    )
                    recomendation.cont_ranking += 1

                recomendation.save()
        except Exception as e:
            return JsonResponse({'error': f'Error al guardar la recomendación: {str(e)}'}, status=500)

        return JsonResponse({'message': 'Recomendacion calificada con exito'}, status=201)
    
class PostFeedback(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        id = data.get('idusuario')
        
        try:
            user = Usuarios.objects.get(idusuario=id)
        except Usuarios.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        if not user.estado:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        Feedback.objects.create(
            idusuario=user,
            ranking=data.get('ranking'),
            comentarios=data.get('comentarios'),
            fecha=datetime.now()
        )
        
        return JsonResponse({'message': 'Feedback enviado con exito'}, status=201)
    
class GetRankings(APIView):
    def get(self, request):
        id = request.query_params.get('idusuario')
        temporada = request.query_params.get('temporada')

        try:
            user = Usuarios.objects.get(idusuario=id)
        except Usuarios.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        if not user.estado:
            return JsonResponse({'error': 'Usuario deshabilitado'}, status=401)
        
        if not ('favoritos' in request.query_params):
            rankings = Rankings.objects.filter(idusuario=user).values_list('idrecomendacion')
            
            filtered = Recomendaciones.objects.filter(
                Q(idrecomendacion__in=[ranking[0] for ranking in rankings]),
                etiquetas__Temporada__icontains=temporada,
            ).values_list("urlimagen", "idrecomendacion")
        else:
            rankings = Rankings.objects.filter(idusuario=user, ranking__gte=4).values_list('idrecomendacion')
            filtered = Recomendaciones.objects.filter(
                Q(idrecomendacion__in=[ranking[0] for ranking in rankings]),
            ).values_list("urlimagen", "idrecomendacion")

        
        return JsonResponse({'rankings': [list(filtered)]}, status=200)
        
class StreakView(APIView):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        id = data.get('idusuario') 
        
        try:
            user = Usuarios.objects.get(idusuario=id)
        except Usuarios.DoesNotExist:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
       
        streak, created = Streak.objects.get_or_create(
                idusuario=user,
                    defaults = {
                    'ultimasesion': timezone.now(),
                    'dias': '1'
                }
            )
        
        if not created:
            with transaction.atomic():
                if (timezone.now() - streak.ultimasesion).days == 1:
                    streak.dias += 1
                    streak.ultimasesion = timezone.now()
                    streak.save()
                    return JsonResponse({'message': '¡Haz aumentado la racha a '+ str(streak.dias) + ' dias!',
                                        'dias': streak.dias}, status=200)
                elif (timezone.now() - streak.ultimasesion).days == 0:
                    return JsonResponse({'message': 'Ya utilizaste tu aumento de racha hoy.',
                                        'dias': streak.dias}, status=200)
                else:
                    streak.dias = 1
                    streak.ultimasesion = timezone.now()
                    streak.save()
                    return JsonResponse({'message': 'Tu racha se ha reiniciado a 1 dia.',
                                        'dias': streak.dias}, status=200)
        else:
            return JsonResponse({'message': 'Tu racha ha comenzado!',
                                     'dias': streak.dias}, status=200)