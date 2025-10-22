from django.urls import path   # 장고프레임워크에서 urls를 임포트해서 path메서드 사용
from . import views            # 같은 폴더 내에서 views를 임포트

urlpatterns = [
    #테스트용
    path('test/', views.test, name='test'),      #url 설정하는 곳으로 컨트롤러의 RequestMapping


    #유저 urls
]

