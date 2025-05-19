from django.urls import path, include
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name="register"),
    path('api/auth', include('auth_api.urls'))
]