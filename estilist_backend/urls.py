from django.urls import path, include
from rest_framework import routers
from estilist_backend.views import CreateUser, UsuariosViewSet, CheckUser, MeauserementsViewSet, UserMeasurements, FacialRecognition, UserPreferences, GetUploadUrlView, ColorimetriaViewSet

router = routers.DefaultRouter()    
router.register(r'users', UsuariosViewSet)
router.register(r'measurements', MeauserementsViewSet)
router.register(r'colorimetry', ColorimetriaViewSet, basename='colorimetry')


urlpatterns = [
    path('', include(router.urls)),
    path('create-user/', CreateUser.as_view(), name='create_user'),
    path('check-user/', CheckUser.as_view(), name='check_user'),
    path('user-measurements/', UserMeasurements.as_view(), name='user_measurements'),
    path('facial-recognition/', FacialRecognition.as_view(), name='facial_recognition'),
    path('user-preferences/', UserPreferences.as_view(), name='user_preferences'),
    path('upload-url/', GetUploadUrlView.as_view(), name='upload_url'),
]