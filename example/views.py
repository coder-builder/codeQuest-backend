from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import exampleUser
from .serializers import UserSerializer

@api_view(['GET'])
# urls에서 호출하는 view입니다. 여기에 호출하면 됩니다. 자바스프링의 컨트롤러 같은 개념으로 보시면 됩니다.

def exampleGetAllUser(request):
    users = exampleUser.objects.all()

    serializer = UserSerializer(users, many=True) # serializer는 자바의 DTO같은 개념입니다.

    return Response({
        'success': True,
        'count': users.count(),
        'users': serializer.data
    })


@api_view(['GET'])
def exampleGetUserById(request, user_id):
    """특정 사용자 상세 조회 (DB)"""
    try:
        # DB에서 특정 user 조회
        user = exampleUser.objects.get(id=user_id)

        # Serializer로 변환
        serializer = UserSerializer(user)

        return Response({
            'success': True,
            'user': serializer.data
        })

    except exampleUser.DoesNotExist:
        return Response({
            'success': False,
            'message': f'ID {user_id} 사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def createUser(request):
    """사용자 생성"""
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': '사용자가 생성되었습니다.',
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)
