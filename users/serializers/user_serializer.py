from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from ..models import User, SocialAccount
import re

"""사용자 회원가입용"""
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'}, label='비밀번호 확인')

    class Meta:
        model = User
        fields = ['email', 'password', 'password2']


    def validate_email(self, value):
        """이메일 형식 검증"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise serializers.ValidationError("유효한 이메일 주소를 입력해주세요.")
        return value

    def validate_nickname(self, value):
        """닉네임 형식 검증"""
        nickname_regex = r'^[a-zA-Z0-9가-힣]{2,20}$'
        if not re.match(nickname_regex, value):
            raise serializers.ValidationError("닉네임은 2~20자의 한글, 영문, 숫자만 사용할 수 있습니다.")
        return value

    def validate_password(self, value):
        """비밀번호 강도 검증"""
        if len(value) < 8:
            raise serializers.ValidationError("비밀번호는 최소 8자 이상이어야 합니다.")
        if not re.search(r'[A-Za-z]', value):
            raise serializers.ValidationError("비밀번호에는 최소 하나의 영문자가 포함되어야 합니다.")
        if not re.search(r'\d', value):
            raise serializers.ValidationError("비밀번호에는 최소 하나의 숫자가 포함되어야 합니다.")

        return value


    def validate(self, data):
        """비밀번호 일치 검증"""
        if data['password'] != data['password2']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data

    def create(self, validated_data):
        """새 사용자 생성"""
        validated_data.pop('password2')  # password2는 제거
        user = User.objects.create_user(**validated_data)
        return user


""" 사용자 기본 정보 조회용 Serializer """
class UserSerializer(serializers.ModelSerializer):
    
    is_premium = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ['user_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }

""" 사용자 상세 정보 조회용 Serializer"""
class UserDetailSerializer(serializers.ModelSerializer):
    """프로필 조회용"""
    is_premium = serializers.SerializerMethodField()
    social_accounts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = [
            'user_id',
            'email',
            'nickname',
            'profile_image_url',
            'level',
            'exp',
            'hearts',
            'coins',
            'subscription_type',
            'subscription_expires_at',
            'is_premium',
            'daily_goal_minutes',
            'streak_days',
            'last_active_date',
            'social_accounts',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_is_premium(self, obj):
        """구독 여부"""
        return obj.is_premium
    
    def get_social_accounts(self, obj):
        """연결된 소셜 계정 목록"""
        try:
            social_account = obj.social_account
            return {
                'provider': social_account.provider,
                'social_email': social_account.social_email,
                'connected_at': social_account.created_at,
            }
        except SocialAccount.DoesNotExist:
            return None 
        
class UserUpdateSerializer(serializers.ModelSerializer):
    """사용자 정보 수정용 Serializer"""
    class Meta:
        model = User
        fields = ['nickname', 'profile_image_url', 'daily_goal_minutes']

    def validate_nickname(self, value):
        """닉네임 유효성 검사"""
        user = self.instance
        
        # 다른 사용자가 사용 중인지 확인
        if User.objects.filter(nickname=value).exclude(user_id=user.user_id).exists():
            raise serializers.ValidationError('이미 사용 중인 닉네임입니다.')
        
        # 길이 검사
        if len(value) < 2:
            raise serializers.ValidationError('닉네임은 2자 이상이어야 합니다.')
        if len(value) > 50:
            raise serializers.ValidationError('닉네임은 50자 이하여야 합니다.')
        
        return value
    
    def validate_daily_goal_minutes(self, value):
        """일일 목표 시간 검사"""
        if value < 1:
            raise serializers.ValidationError('일일 목표는 1분 이상이어야 합니다.')
        if value > 1440:  # 24시간
            raise serializers.ValidationError('일일 목표는 24시간을 초과할 수 없습니다.')
        
        return value
    

# ========================================
# Email Serializers (이메일 로그인용)
# ========================================

class LoginSerializer(serializers.Serializer):
    """
    이메일 로그인 Serializer
    
    Request:
    {
        "email": "user@example.com",
        "password": "password123!",
        "device_id": "device_123",
        "device_name": "iPhone 15"
    }
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    device_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255
    )
    device_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255
    )


class LoginOutputSerializer(serializers.Serializer):
    """
    로그인 응답 Serializer
    """
    success = serializers.BooleanField()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer()


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    비밀번호 재설정 요청 Serializer
    
    Request:
    {
        "email": "user@example.com"
    }
    """
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    비밀번호 재설정 확인 Serializer
    
    Request:
    {
        "token": "reset_token",
        "new_password": "newpassword123!",
        "new_password_confirm": "newpassword123!"
    }
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """비밀번호 일치 검사"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '비밀번호가 일치하지 않습니다.'
            })
        
        # Django 비밀번호 검증
        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """
    비밀번호 변경 Serializer (로그인 상태)
    
    Request:
    {
        "old_password": "oldpassword123!",
        "new_password": "newpassword123!",
        "new_password_confirm": "newpassword123!"
    }
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """기존 비밀번호 확인"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('기존 비밀번호가 올바르지 않습니다.')
        return value
    
    def validate(self, attrs):
        """비밀번호 일치 검사"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '비밀번호가 일치하지 않습니다.'
            })
        
        # 기존 비밀번호와 동일한지 확인
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': '새 비밀번호는 기존 비밀번호와 달라야 합니다.'
            })
        
        # Django 비밀번호 검증
        try:
            validate_password(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })
        
        return attrs
