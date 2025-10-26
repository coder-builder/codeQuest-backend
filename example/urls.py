from django.urls import path   # 장고프레임워크에서 urls를 임포트해서 path메서드 사용
from . import views            # 같은 폴더 내에서 views를 임포트

urlpatterns = [
    #테스트용 URL을 매핑한다는 개념으로 보시면될듯합니다.
    # 이곳을 보기전에 views를 봐주세요

    # path(1번 매개변수 - url호출 경로 앞에 context가 붙음, 2번 매개변수 - views.py에서 호출할 이름, 3번 매개변수 - path이름설정)
    path('users/', views.exampleGetAllUser, name='get-all-user'),
    path('users/<int:user_id>/', views.exampleGetUserById, name='get-user-by-id'),
    path('users/create/', views.createUser, name='create-user'),

]
