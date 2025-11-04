from django.urls import path
from . import views

app_name = "rank"

urlpatterns = [
  # # 전체 랭크 페이지 (예: /rank/)
  # path("", views.home, name="home"),

  # # 리스트 조회 (예: /rank/list/)
  # path("list/", views.RankListView.as_view(), name="list"),

  # # 상세 조회 (예: /rank/1/)
  # path("<int:pk>/", views.RankDetailView.as_view(), name="detail"),
]