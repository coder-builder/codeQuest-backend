from rest_framework import serializers
from ..models import SocialAccount
from .user_serializer import UserSerializer


# ========================================
# Social Account Serializers
# ========================================

class SocialAccountSerializer(serializers.ModelSerializer):
    """
    소셜 계정 정보 Serializer
    """
    class Meta:
        model = SocialAccount
        fields = [
            'id',
            'provider',
            'social_id',
            'social_email',
            'social_name',
            'profile_image',
            'created_at',
            'last_login_at',
        ]
        read_only_fields = fields


class SocialLoginInputSerializer(serializers.Serializer):
    """
    소셜 로그인 입력 Serializer
    
    Request:
    {
        "provider": "google",
        "access_token": "ya29.a0...",
        "device_id": "device_123",
        "device_name": "iPhone 15"
    }
    """
    provider = serializers.ChoiceField(
        choices=['google', 'kakao', 'naver', 'apple'],
        required=True,
        help_text='소셜 제공자 (google/kakao/naver/apple)'
    )
    access_token = serializers.CharField(
        required=True,
        min_length=10,
        help_text='소셜 제공자의 Access Token'
    )
    device_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text='디바이스 고유 ID'
    )
    device_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text='디바이스 이름 (예: iPhone 15)'
    )
    
    def validate_provider(self, value):
        """제공자 검증"""
        valid_providers = ['google', 'kakao', 'naver', 'apple']
        if value not in valid_providers:
            raise serializers.ValidationError(
                f'유효하지 않은 제공자입니다. 가능한 값: {", ".join(valid_providers)}'
            )
        return value


class SocialLoginOutputSerializer(serializers.Serializer):
    """
    소셜 로그인 응답 Serializer
    
    Response:
    {
        "success": true,
        "is_new_user": false,
        "access_token": "eyJ0eXAi...",
        "refresh_token": "eyJ0eXAi...",
        "user": {
            "user_id": "uuid",
            "email": "user@example.com",
            ...
        }
    }
    """
    success = serializers.BooleanField()
    is_new_user = serializers.BooleanField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer()