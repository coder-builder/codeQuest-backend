from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from .models import User, CustomRefreshToken, SocialAccount
from .serializers.user_serializer import UserSerializer
from .social_auth import SocialAuthProvider


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

    @staticmethod
    def social_login(provider_name, access_token, device_id=None, device_name="Unknown Device", ip_address=None, user_agent=None):
        """
        소셜 로그인 처리
        
        Args:
            provider_name (str): 소셜 제공자 ('google', 'kakao', 'naver', 'apple')
            access_token (str): 소셜 제공자로부터 받은 Access Token
            device_id (str): 디바이스 고유 ID
            device_name (str): 디바이스 이름
            ip_address (str): 사용자 IP 주소
            user_agent (str): 사용자 에이전트 정보
            
        Returns:
            dict: {
                'success': True,
                'is_new_user': False,  # 신규 가입 여부
                'user': UserSerializer(user).data,
                'refresh': 'refresh_token',
                'access': 'access_token',
            }
            
        Raises:
            ValueError: 인증 실패 또는 API 호출 실패 시
        """
        
        try:
            # 1. 소셜 제공자로부터 사용자 정보 가져오기
            provider = SocialAuthProvider.get_provider(provider_name)
            user_info = provider.get_user_info(access_token)
            
            # 2. SocialAccount 모델을 통해 사용자 찾기 또는 생성
            user, is_new_user, social_account = SocialAccount.find_or_create_user(
                provider=provider_name,
                social_id=user_info['social_id'],
                email=user_info['email'],
                name=user_info.get('name', ''),
                profile_image=user_info.get('profile_image', ''),
                extra_data=user_info.get('extra_data', {})
            )
            
            # 3. JWT 토큰 생성
            access_jwt = AccessToken.for_user(user)
            refresh_jwt = RefreshToken.for_user(user)
            
            # 4. Refresh Token 저장
            CustomRefreshToken.create_for_user(
                user=user,
                refresh_token_string=str(refresh_jwt),
                device_id=device_id,
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # 5. 마지막 로그인 시간 업데이트
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # 6. 응답 반환
            return {
                'success': True,
                'is_new_user': is_new_user,
                'user': UserSerializer(user).data,
                'refresh': str(refresh_jwt),
                'access': str(access_jwt),
            }
            
        except ValueError as e:
            # 소셜 인증 과정에서 발생한 에러
            raise ValueError(f"소셜 로그인 실패: {str(e)}") from e
        except Exception as e:
            # 예상치 못한 에러
            raise ValueError(f"소셜 로그인 처리 중 오류 발생: {str(e)}") from e