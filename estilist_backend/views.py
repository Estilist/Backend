from rest_framework import viewsets, status
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from PIL import Image
from .models import Usuarios, Medidas, Preferencias
from .serializers import UsuariosSerializer, MeasuerementsSerializer
from django.views import View
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
import json, datetime
from estilist_project import settings
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
import os, requests, uuid
from datetime import datetime, timedelta
import logging

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
        
        try:
            user_medidas, created = Medidas.objects.get_or_create(
                idusuario=user.idusuario,
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

class FacialRecognition(APIView):
    parser_classes = [MultiPartParser, FormParser]  # Permite recibir multipart/form-data y x-www-form-urlencoded
    def post(self, request):
        image_file = request.data.get('file')
        if image_file is None:
            return JsonResponse({'error': 'No se ha enviado ninguna imagen'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            img = Image.open(image_file)
            img.verify()
        except (IOError, SyntaxError) as e:
            return JsonResponse({'error': 'El archivo no es una imagen válida'}, status=status.HTTP_400_BAD_REQUEST)
        
        save_dir = os.path.join(settings.BASE_DIR, 'estilist_backend', 'Images')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, image_file.name)
        
        with open(file_path, 'wb+') as destination: 
            for chunk in image_file.chunks():
                destination.write(chunk)
                
        url = 'https://identiface.ambitioussea-007d0918.westus3.azurecontainerapps.io/predict/'
        with open(file_path, 'rb') as img_file:
                files = {'file': img_file}
                response = requests.post(url, files=files)
        
        attributes = response.json()
        
        id = request.data.get('idusuario')
        
        try:
            user = Usuarios.objects.get(idusuario= id)
        except:
            return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
        
        user.tiporostro = attributes.get('forma')
        try:
            user.save()
        except:
            return JsonResponse({'error': 'Error al actualizar el tipo de rostro'}, status=500)
        
        return JsonResponse(response.json(), status=200)
        
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