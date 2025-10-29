from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers.user_serializer import UserRegisterSerializer, UserSerializer
from .serializers.socialAccount_serializer import SocialLoginInputSerializer
from .services import UserService

"""
Spring의 Controller처럼 요청과 응답 처리만 담당
비즈니스 로직은 Service에 위임
"""

class RegisterView(APIView):
    """회원가입 뷰"""
    permission_classes = [AllowAny] # 모든 사용자가 접근 가능

    def post(self, request):

        serializer = UserRegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Service 레이어 호출
            user = UserService.register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            )

            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """로그인 컨트롤"""
    permission_classes = [AllowAny] # 모든 사용자가 접근 가능

    def post(self, request):
        debug_request = request.data
        # 기본정보
        email = request.data.get('email')
        password = request.data.get('password')
        device_id = request.data.get('device_id')
        device_name = request.data.get('device_name')

        # 헤더정보
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        if not email or not password:
            return Response(
                {'error': '이메일과 비밀번호를 모두 입력해주세요.'}
            )

        try:
            result = UserService.login_user(email, password, device_id, device_name, ip_address, user_agent)

            return Response(result)

        except ValueError as e:
            return Response({'error': '로그인에 실패했습니다.'})


class SocialLoginView(APIView):
    """
    소셜 로그인 뷰
    
    지원하는 제공자:
    - Google
    - Kakao
    - Naver
    - Apple (구현 예정)
    
    Request Body:
    {
        "provider": "google",
        "access_token": "ya29.a0...",
        "device_id": "device_123",
        "device_name": "iPhone 15"
    }
    
    Response:
    {
        "success": true,
        "is_new_user": false,
        "access_token": "eyJ0eXAi...",
        "refresh_token": "eyJ0eXAi...",
        "user": { ... }
    }
    """
    
    permission_classes = [AllowAny]  # 모든 사용자가 접근 가능
    
    def post(self, request):
        """소셜 로그인 처리"""
        
        # 1. 요청 데이터 검증
        serializer = SocialLoginInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. 검증된 데이터 추출
        provider = serializer.validated_data['provider']
        access_token = serializer.validated_data['access_token']
        device_id = serializer.validated_data.get('device_id')
        device_name = serializer.validated_data.get('device_name', 'Unknown Device')
        
        # 3. 헤더 정보 추출
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # 4. Service 레이어 호출
        try:
            result = UserService.social_login(
                provider_name=provider,
                access_token=access_token,
                device_id=device_id,
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # 예상치 못한 에러
            return Response(
                {'error': '소셜 로그인 처리 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )