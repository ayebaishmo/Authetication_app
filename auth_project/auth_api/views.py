from rest_framework import generics
from rest_framework.permissions import IsAuthenticated # Import IsAuthenticated
from .models import User
from .serializers import UserSerializer, UserRegistrationSerializer # Add UserRegistrationSerializer

class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Add permission_classes

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    # No permission_classes, so it's open for registration
