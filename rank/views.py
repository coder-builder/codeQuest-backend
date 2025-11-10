"""
================================================================================
랭킹 시스템 뷰 파일 (API 엔드포인트)
================================================================================
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from django.db import transaction
from django.utils import timezone

from .models import League, LeagueParticipant, GlobalRanking, UserRankingHistory
from .services import RankingService
from .serializer import (
  LeagueSerializer,
  LeagueParticipantSerializer,
  MyLeagueRankingSerializer,
  GlobalRankingListSerializer,
  UserRankingHistorySerializer,
  RankingHistoryListSerializer,
  AddExpRequestSerializer,
  AddExpResponseSerializer,
  TierConfigSerializer
)


# ============================================================================
# 페이지네이션 클래스
# ============================================================================
class RankingPagination(PageNumberPagination):
  page_size = 50
  page_size_query_param = 'page_size'
  max_page_size = 100


# ============================================================================
# 1. 내 리그 랭킹 조회 API
# ============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_league_ranking(request):
  # 내가 속한 이번 주 리그의 랭킹을 조회
  try:
    user = request.user
    result = RankingService.get_league_rankings(user)

    serializer = MyLeagueRankingSerializer(data=result)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status.HTTP_200_OK)
  
  except Exception as e:
    return Response(
      {'error': str(e)},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
  

# ============================================================================
# 2. 전체 랭킹 조회 API
# ============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_global_rankings(request):
  try:
    limit = int(request.GET.get('limit', 100))
    offset = int(request.GET.get('offset', 0))

    rankings_data = RankingService.get_global_rankings(limit, offset)

    serializer = GlobalRankingListSerializer(data=rankings_data, many=True)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)
  
  except Exception as e:
    return Response(
      {'error': str(e)},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# 3. 내 랭킹 히스토리 조회 API
# ============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_ranking_history(request):
  # 내 주간 랭킹 히스토리를 조회
  try:
    user = request.user
    limit = int(request.GET.get('limit', 10))
    
    history_data = RankingService.get_user_ranking_history(user, limit)

    serializer = RankingHistoryListSerializer(data=history_data, many=True)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)
  
  except Exception as e:
    return Response(
      {'error': str(e)},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# 4. 티어별 랭킹 조회 API
# ============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tier_rankings(request, tier):
  # 특정 티어의 전체 유저 랭킹을 조회
  try:
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))

    # 티어별 전체 랭킹 조회
    rankings = (
      GlobalRanking.objects
      .filter(current_tier=tier.upper())
      .select_related('user')
      .order_by('rank')[offset:offset+limit]
    )

    rankings_data = []
    for ranking in rankings:
      tier_info = RankingService.get_tier_info(ranking.current_tier)
      rankings_data.append({
        'rank': ranking.rank,
        'user_id': str(ranking.user.user_id),
        'nickname': ranking.user.nickname,
        'profile_image': ranking.user.profile_image_url,
        'total_exp': ranking.total_exp,
        'tier': ranking.current_tier,
        'tier_icon': tier_info['icon'],
        'tier_color': tier_info['color']
      })

    serializer = GlobalRankingListSerializer(data=rankings_data, many=True)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.validated_data, status=status.HTTP_200_OK)
  
  except Exception as e:
    return Response(
      {'error': str(e)},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# 5. 내 순위 정보 조회 API (간단 버전)
# ============================================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_rank_info(request):
  try:
    user = request.user

    # 전체 랭킹 정보
    global_ranking = GlobalRanking.objects.get(user=user)
    tier_info = RankingService.get_tier_info(global_ranking.current_tier)

    # 주간 랭킹 정보
    week_start, week_end = RankingService.get_current_week_dates()
    try:
        participant = LeagueParticipant.objects.get(
            user=user,
            league__week_start=week_start,
            league__is_active=True
        )
        weekly_rank = participant.current_rank
        weekly_exp = participant.weekly_total_exp
    except LeagueParticipant.DoesNotExist:
        weekly_rank = 0
        weekly_exp = 0

    data = {
      'user_id': str(user.user_id),
      'nickname': user.nickname,
      'total_exp': user.exp,
      'global_rank': global_ranking.rank,
      'current_tier': global_ranking.current_tier,
      'tier_info': tier_info,
      'weekly_rank': weekly_rank,
      'weekly_exp': weekly_exp
    }

    return Response(data, status=status.HTTP_200_OK)
  
  except GlobalRanking.DoesNotExist:
    # 랭킹 정보가 없으면 생성
    RankingService.update_global_ranking(user)
    return get_my_rank_info(request)
  
  except Exception as e:
    return Response(
      {'error': str(e)},
      status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


# ============================================================================
# 6. EXP 추가 API (테스트용)
# ============================================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_exp(request):
  try:
    serializer = AddExpRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    exp_amount = serializer.validated_data['exp_amount']
    exp_type = serializer.validated_data['exp_type']
    
    result = RankingService.add_exp_to_user(user, exp_amount, exp_type)
    
    response_serializer = AddExpResponseSerializer(data=result)
    response_serializer.is_valid(raise_exception=True)

    return Response(
        response_serializer.validated_data,
        status=status.HTTP_200_OK
    )
  
  except Exception as e:
    return Response(
        {'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
    )


# ============================================================================
# 7. 티어 정보 조회 API
# ============================================================================
@api_view(['GET'])
def get_tier_configs(request):
  # 모든 티어 설정 정보를 조회
  tier_configs = []
  for tier_name, tier_info in RankingService.TIER_SYSTEM.items():
    tier_configs.append({
      'tier': tier_name,
      'tier_display': tier_name.capitalize(),
      'min_exp': tier_info['min_exp'],
      'max_exp': tier_info['max_exp'] if tier_info['max_exp'] != float('inf') else 999999,
      'icon': tier_info['icon'],
      'color': tier_info['color'],
      'order': tier_info['order'],
      'coin_multiplier': 1.0
    })

  # order로 정렬
  tier_configs.sort(key=lambda x: x['order'])

  return Response(tier_configs, status=status.HTTP_200_OK)