from rest_framework import serializers
from .models import exampleUser

class UserSerializer(serializers.ModelSerializer):
    """사용자 시리얼라이저 자바로 치면 DTO입니다."""

    class Meta:
        model = exampleUser
        fields = ['id', 'name', 'email', 'age', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']