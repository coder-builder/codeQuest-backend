"""
================================================================================
랭킹 시스템 URL 라우팅
================================================================================
"""

from django.urls import path
from . import views

app_name = 'ranking'

urlpatterns = [
    # 1. 내 리그 랭킹 조회
    path('my-league/', views.get_my_league_ranking, name='my-league-ranking'),
    
    # 2. 전체 랭킹 조회
    path('global/', views.get_global_rankings, name='global-rankings'),
    
    # 3. 내 랭킹 히스토리 조회
    path('my-history/', views.get_my_ranking_history, name='my-ranking-history'),
    
    # 4. 티어별 랭킹 조회
    path('tier/<str:tier>/', views.get_tier_rankings, name='tier-rankings'),
    
    # 5. 내 순위 정보 조회 (간단)
    path('me/', views.get_my_rank_info, name='my-rank-info'),
    
    # 6. EXP 추가 (문제 풀이 후)
    path('add-exp/', views.add_exp, name='add-exp'),
    
    # 7. 티어 설정 정보 조회
    path('tiers/', views.get_tier_configs, name='tier-configs'),
]