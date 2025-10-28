from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer

from ..models import User
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
    
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ['user_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        

"""커스텀 JWT 토큰 발급 Serializer"""
class CustomTokenObtainPairSerializer(TokenObtainSerializer):
    
    def validate(self, attrs):
        data = super().validate(attrs)

        # 추가 사용자 정보 포함
        data['user'] = {
            'user_id': self.user.user_id,
            'email': self.user.email,
            'nickname': self.user.nickname,
            'level': self.user.level,
            'exp': self.user.exp,
            'hearts': self.user.hearts,
            'coins': self.user.coins,
            'is_premium': self.user.is_premium,
        }

        return data