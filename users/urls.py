from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
  # 일반 로그인/회원가입
  path('register/', views.RegisterView.as_view(), name='register'),
  path('login/', views.LoginView.as_view(), name='login'),
  
  # 소셜 로그인
  path('social/login/', views.SocialLoginView.as_view(), name='social-login'),
]