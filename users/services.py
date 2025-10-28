from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import User, CustomRefreshToken
from .serializers.user_serializer import UserSerializer


class UserService:
    """
    Spring Service처럼 비즈니스 로직 처리
    """

    @staticmethod
    def register_user(email, password):
        """회원가입"""
        # 중복체크
        if User.objects.filter(email=email).exists():
            raise ValueError("이미 존재하는 이메일입니다.")

        # 사용자 생성
        user = User.objects.create_user(email=email, password=password)

        return user

    @staticmethod
    def login_user(email, password, device_id=None, device_name="Unknown Device", ip_address=None, user_agent=None):

        try:
            # 사용자 인증
            user = authenticate(email=email, password=password)
            if not user:
                raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

            # 의심스러운 활동 감지
            # suspicious_patterns = CustomRefreshToken.detect_suspicious_activity(
            #     user=user,
            #     ip_address=ip_address,
            #     user_agent=user_agent
            # )
            # if suspicious_patterns:
            #     CustomRefreshToken.revoke_user_all_logout(user=user)
            #     raise ValueError("의심스러운 활동이 감지되어 로그아웃되었습니다. 다시 로그인해주세요.")

            # JWT 토큰 생성
            access = AccessToken.for_user(user)
            refresh = RefreshToken.for_user(user)

            # 토큰 저장
            CustomRefreshToken.create_for_user(
                user=user,
                refresh_token_string=str(refresh),
                device_id=device_id,
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 마지막 활동 날짜 업데이트
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])

            return {
                'success': True,
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(access),
            }
        except Exception as e:
            raise ValueError("로그인에 실패했습니다.") from e