from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
import re
from ..models import User

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