from django.urls import path, include
from rest_framework import routers
from estilist_backend.views import CreateUser, UsuariosViewSet, CheckUser, AuthUserViewSet, MeauserementsViewSet, UserMeasurements

router = routers.DefaultRouter()    
router.register(r'users', UsuariosViewSet)
router.register(r'measurements', MeauserementsViewSet)
router.register(r'auth', AuthUserViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('create-user/', CreateUser.as_view(), name='create_user'),
    path('check-user/', CheckUser.as_view(), name='check_user'),
    path('user-measurements/', UserMeasurements.as_view(), name='user_measurements')
    # path('crear-superusuario/', CrearSuperUsuario.as_view(), name='crear_superusuario'),
]