from django.urls import path, include
from rest_framework import routers
from estilist_backend.views import CreateUser, UsuariosViewSet, CheckUser, AuthUserViewSet

router = routers.DefaultRouter()    
router.register(r'usuarios', UsuariosViewSet)
router.register(r'auth', AuthUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('create-user/', CreateUser.as_view(), name='create_user'),
    path('check-user/', CheckUser.as_view(), name='check_user'),
    # path('crear-superusuario/', CrearSuperUsuario.as_view(), name='crear_superusuario'),
]