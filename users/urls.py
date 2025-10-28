from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
  # Add your URL patterns here
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', views.LoginView.as_view(), name='login'),
]