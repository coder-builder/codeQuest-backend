"""
소셜 로그인 처리 모듈

이 파일은 각 소셜 제공자(Google, Kakao, Naver, Apple)로부터 
사용자 정보를 가져오고 검증하는 역할을 담당합니다.

주요 역할:
1. Access Token 검증
2. 소셜 제공자 API 호출
3. 사용자 정보 추출 및 표준화
4. 에러 처리

사용 예시:
    provider = SocialAuthProvider.get_provider('google')
    user_info = provider.get_user_info(access_token)
"""

import requests
from abc import ABC, abstractmethod
from typing import Dict, Optional
from django.conf import settings


# ========================================
# 소셜 인증 제공자 기본 클래스
# ========================================

class BaseSocialAuthProvider(ABC):
    """
    모든 소셜 인증 제공자의 기본 클래스
    
    각 소셜 제공자(Google, Kakao, Naver)는 이 클래스를 상속받아
    get_user_info() 메서드를 구현해야 합니다.
    
    Why Abstract Class?
    - 각 제공자마다 API 형식이 다르지만, 기본 구조는 동일
    - 새로운 제공자 추가 시 일관된 인터페이스 보장
    """
    
    # 제공자 이름 (하위 클래스에서 반드시 설정)
    provider_name: str = None
    
    # API 엔드포인트 (하위 클래스에서 설정)
    user_info_url: str = None
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict:
        """
        Access Token을 사용하여 사용자 정보를 가져옵니다.
        
        Args:
            access_token (str): 소셜 제공자로부터 받은 Access Token
            
        Returns:
            Dict: 표준화된 사용자 정보
                {
                    'social_id': '소셜 제공자의 고유 ID',
                    'email': '이메일 주소',
                    'name': '이름',
                    'profile_image': '프로필 이미지 URL (선택)',
                }
                
        Raises:
            ValueError: 토큰이 유효하지 않거나 API 호출 실패 시
        """
        pass
    
    def _make_request(self, url: str, headers: Dict, method: str = 'GET') -> Dict:
        """
        HTTP 요청을 보내고 응답을 반환하는 헬퍼 메서드
        
        Args:
            url (str): 요청할 URL
            headers (Dict): 요청 헤더
            method (str): HTTP 메서드 (GET, POST 등)
            
        Returns:
            Dict: JSON 응답 데이터
            
        Raises:
            ValueError: 요청 실패 시
        """
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"지원하지 않는 HTTP 메서드: {method}")
            
            # HTTP 상태 코드 확인
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise ValueError(f"{self.provider_name} 서버 응답 시간 초과")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"{self.provider_name} API 호출 실패: {str(e)}")
        except ValueError as e:
            # JSON 파싱 실패
            raise ValueError(f"{self.provider_name} 응답 형식 오류: {str(e)}")


# ========================================
# Google OAuth2 Provider
# ========================================

class GoogleAuthProvider(BaseSocialAuthProvider):
    """
    Google OAuth2 인증 제공자
    
    Google의 경우 Access Token만으로 사용자 정보를 가져올 수 있습니다.
    
    API 문서: https://developers.google.com/identity/protocols/oauth2
    사용자 정보 엔드포인트: https://www.googleapis.com/oauth2/v2/userinfo
    """
    
    provider_name = 'google'
    user_info_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Google Access Token으로 사용자 정보 가져오기
        
        Google API 응답 예시:
        {
            "id": "1234567890",
            "email": "user@gmail.com",
            "verified_email": true,
            "name": "홍길동",
            "given_name": "길동",
            "family_name": "홍",
            "picture": "https://lh3.googleusercontent.com/...",
            "locale": "ko"
        }
        """
        
        # 1. API 요청 헤더 설정
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        
        # 2. Google API 호출
        user_data = self._make_request(self.user_info_url, headers)
        
        # 3. 필수 정보 확인
        if not user_data.get('id'):
            raise ValueError("Google 사용자 ID를 가져올 수 없습니다.")
        
        if not user_data.get('email'):
            raise ValueError("Google 이메일 정보를 가져올 수 없습니다.")
        
        # 4. 표준 형식으로 변환
        result = {
            'social_id': user_data['id'],
            'email': user_data['email'],
            'name': user_data.get('name', ''),
            'profile_image': user_data.get('picture', ''),
            'extra_data': {
                'verified_email': user_data.get('verified_email', False),
                'locale': user_data.get('locale', ''),
            }
        }
        
        return result


# ========================================
# Kakao OAuth2 Provider
# ========================================

class KakaoAuthProvider(BaseSocialAuthProvider):
    """
    Kakao OAuth2 인증 제공자
    
    Kakao는 카카오계정 정보를 통해 사용자 정보를 제공합니다.
    
    API 문서: https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api
    사용자 정보 엔드포인트: https://kapi.kakao.com/v2/user/me
    """
    
    provider_name = 'kakao'
    user_info_url = 'https://kapi.kakao.com/v2/user/me'
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Kakao Access Token으로 사용자 정보 가져오기
        
        Kakao API 응답 예시:
        {
            "id": 1234567890,
            "connected_at": "2022-04-11T01:45:28Z",
            "kakao_account": {
                "profile_nickname_needs_agreement": false,
                "profile": {
                    "nickname": "홍길동",
                    "thumbnail_image_url": "http://...",
                    "profile_image_url": "http://..."
                },
                "has_email": true,
                "email_needs_agreement": false,
                "is_email_valid": true,
                "is_email_verified": true,
                "email": "user@kakao.com"
            }
        }
        """
        
        # 1. API 요청 헤더 설정
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        
        # 2. Kakao API 호출
        user_data = self._make_request(self.user_info_url, headers)
        
        # 3. 필수 정보 확인
        if not user_data.get('id'):
            raise ValueError("Kakao 사용자 ID를 가져올 수 없습니다.")
        
        # kakao_account에서 정보 추출
        kakao_account = user_data.get('kakao_account', {})
        profile = kakao_account.get('profile', {})
        
        # 이메일 정보 (선택적으로 제공될 수 있음)
        email = kakao_account.get('email', '')
        if not email:
            # 이메일이 없으면 kakao ID로 임시 이메일 생성
            email = f"kakao_{user_data['id']}@codequest.app"
        
        # 4. 표준 형식으로 변환
        return {
            'social_id': str(user_data['id']),  # 숫자를 문자열로 변환
            'email': email,
            'name': profile.get('nickname', ''),
            'profile_image': profile.get('profile_image_url', ''),
            'extra_data': {
                'thumbnail_image': profile.get('thumbnail_image_url', ''),
                'is_email_verified': kakao_account.get('is_email_verified', False),
                'connected_at': user_data.get('connected_at', ''),
            }
        }


# ========================================
# Naver OAuth2 Provider
# ========================================

class NaverAuthProvider(BaseSocialAuthProvider):
    """
    Naver OAuth2 인증 제공자
    
    Naver는 접근 토큰을 사용하여 사용자 프로필 정보를 제공합니다.
    
    API 문서: https://developers.naver.com/docs/login/api/api.md
    사용자 정보 엔드포인트: https://openapi.naver.com/v1/nid/me
    """
    
    provider_name = 'naver'
    user_info_url = 'https://openapi.naver.com/v1/nid/me'
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Naver Access Token으로 사용자 정보 가져오기
        
        Naver API 응답 예시:
        {
            "resultcode": "00",
            "message": "success",
            "response": {
                "id": "1234567890",
                "email": "user@naver.com",
                "name": "홍길동",
                "nickname": "홍길동",
                "profile_image": "https://ssl.pstatic.net/...",
                "age": "30-39",
                "gender": "M",
                "birthday": "05-16",
                "birthyear": "1990"
            }
        }
        """
        
        # 1. API 요청 헤더 설정
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        
        # 2. Naver API 호출
        user_data = self._make_request(self.user_info_url, headers)
        
        # 3. 응답 코드 확인
        if user_data.get('resultcode') != '00':
            raise ValueError(f"Naver API 오류: {user_data.get('message', '알 수 없는 오류')}")
        
        # response 객체에서 실제 사용자 정보 추출
        response = user_data.get('response', {})
        
        if not response.get('id'):
            raise ValueError("Naver 사용자 ID를 가져올 수 없습니다.")
        
        if not response.get('email'):
            raise ValueError("Naver 이메일 정보를 가져올 수 없습니다.")
        
        # 4. 표준 형식으로 변환
        return {
            'social_id': response['id'],
            'email': response['email'],
            'name': response.get('name', response.get('nickname', '')),
            'profile_image': response.get('profile_image', ''),
            'extra_data': {
                'nickname': response.get('nickname', ''),
                'age': response.get('age', ''),
                'gender': response.get('gender', ''),
                'birthday': response.get('birthday', ''),
                'birthyear': response.get('birthyear', ''),
            }
        }


# ========================================
# Apple OAuth2 Provider (선택적)
# ========================================

class AppleAuthProvider(BaseSocialAuthProvider):
    """
    Apple Sign In 인증 제공자
    
    Apple은 다른 제공자와 달리 JWT 토큰을 사용하여 사용자 정보를 제공합니다.
    
    API 문서: https://developer.apple.com/documentation/sign_in_with_apple
    
    Note: Apple은 처음 로그인 시에만 사용자 정보를 제공하므로,
          이후에는 저장된 정보를 사용해야 합니다.
    """
    
    provider_name = 'apple'
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Apple ID Token(JWT)을 검증하고 사용자 정보 추출
        
        Apple의 경우 identity_token을 검증해야 합니다.
        
        TODO: JWT 검증 로직 구현 필요
        - Apple 공개 키 가져오기
        - JWT 서명 검증
        - 클레임 추출
        """
        
        # Apple JWT 검증은 복잡하므로 별도 라이브러리 사용 권장
        # 예: PyJWT, python-jose 등
        
        raise NotImplementedError(
            "Apple Sign In은 아직 구현되지 않았습니다. "
            "JWT 검증 로직이 필요합니다."
        )


# ========================================
# 소셜 인증 제공자 팩토리
# ========================================

class SocialAuthProvider:
    """
    소셜 인증 제공자 팩토리 클래스
    
    제공자 이름에 따라 적절한 Provider 인스턴스를 반환합니다.
    
    사용 예시:
        # Google 제공자 가져오기
        provider = SocialAuthProvider.get_provider('google')
        user_info = provider.get_user_info(access_token)
        
        # Kakao 제공자 가져오기
        provider = SocialAuthProvider.get_provider('kakao')
        user_info = provider.get_user_info(access_token)
    """
    
    # 지원하는 제공자 매핑
    _providers = {
        'google': GoogleAuthProvider,
        'kakao': KakaoAuthProvider,
        'naver': NaverAuthProvider,
        'apple': AppleAuthProvider,
    }
    
    @classmethod
    def get_provider(cls, provider_name: str) -> BaseSocialAuthProvider:
        """
        제공자 이름으로 Provider 인스턴스 가져오기
        
        Args:
            provider_name (str): 제공자 이름 ('google', 'kakao', 'naver', 'apple')
            
        Returns:
            BaseSocialAuthProvider: 해당 제공자의 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 제공자인 경우
            
        Example:
            provider = SocialAuthProvider.get_provider('google')
            user_info = provider.get_user_info('ya29.a0...')
        """
        
        provider_name = provider_name.lower()
        
        if provider_name not in cls._providers:
            valid_providers = ', '.join(cls._providers.keys())
            raise ValueError(
                f"지원하지 않는 소셜 제공자입니다: {provider_name}. "
                f"사용 가능한 제공자: {valid_providers}"
            )
        
        # Provider 클래스의 인스턴스 생성 후 반환
        provider_class = cls._providers[provider_name]
        return provider_class()
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """
        지원하는 모든 제공자 이름 목록 반환
        
        Returns:
            list: ['google', 'kakao', 'naver', 'apple']
        """
        return list(cls._providers.keys())


# ========================================
# 사용 예시 및 테스트 코드
# ========================================

if __name__ == '__main__':
    """
    이 파일을 직접 실행하면 테스트 코드가 실행됩니다.
    
    실제 사용 시에는 views.py나 services.py에서 import하여 사용합니다.
    """
    
    # 예시 1: Google 사용자 정보 가져오기
    try:
        google_provider = SocialAuthProvider.get_provider('google')
        # user_info = google_provider.get_user_info('실제_액세스_토큰')
        # print(user_info)
    except ValueError as e:
        print(f"Google 인증 실패: {e}")
    
    # 예시 2: Kakao 사용자 정보 가져오기
    try:
        kakao_provider = SocialAuthProvider.get_provider('kakao')
        # user_info = kakao_provider.get_user_info('실제_액세스_토큰')
        # print(user_info)
    except ValueError as e:
        print(f"Kakao 인증 실패: {e}")
    
    # 예시 3: 지원하는 모든 제공자 확인
    print("지원하는 소셜 제공자:")
    print(SocialAuthProvider.get_supported_providers())
