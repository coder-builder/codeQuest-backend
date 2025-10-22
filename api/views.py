from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def test(request):
    return Response({'message': '연습용 api입니다'})

# Create your views here.
