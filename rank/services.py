# ================================================================================
# 랭킹 시스템 비즈니스 로직 서비스 파일
# ================================================================================

from django.db import transaction, models
from django.db.models import F, Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import League, LeagueParticipant, UserRankingHistory, TierConfig, GlobalRanking
from users.models import User

# ============================================================================
# RankingService 클래스
# ============================================================================
class RankingService:
  TIER_SYSTEM = {
    'BRONZE': {
      'min_exp': 0,           # 최소 EXP
      'max_exp': 999,         # 최대 EXP
      'icon': '🥉',           # 아이콘
      'color': '#CD7F32',   #HEX 색상 코드 (청동색)
      'order': 1              # 티어 순서 (낮을수록 하위)
    },
    'SILVER': {
      'min_exp': 1000,
      'max_exp': 2499,
      'icon': '🥈',
      'color': '#C0C0C0',
      'order': 2
    },
    'GOLD': {
      'min_exp': 2500,
      'max_exp': 4999,
      'icon': '🥇',
      'color': '#FFD700',
      'order': 3
    },
    'PLATINUM': {
      'min_exp': 5000,
      'max_exp': 9999,
      'icon': '💎',
      'color': '#E5E4E2',
      'order': 4
    },
    'DIAMOND': {
      'min_exp': 10000,
      'max_exp': 19999,
      'icon': '💠',
      'color': '#B9F2FF',
      'order': 5
    },
    'MASTER': {
      'min_exp': 20000,
      'max_exp': 49999,
      'icon': '👑',
      'color': '#FF6B6B',
      'order': 6
    },
    'LEGEND': {
      'min_exp': 50000,
      'max_exp': float('inf'), # 무한대 (상한선 없음)
      'icon': '⚡',
      'color': '#8B5CF6',
      'order': 7
    }
  }

  # ========================================================================
  # 티어 관련 유틸리티 메서드
  # ========================================================================
  @staticmethod
  def get_user_tier(total_exp):
    for tier_name, tier_info in RankingService.TIER_SYSTEM.items():
      if tier_info['min_exp'] <= total_exp <= tier_info['max_exp']:

        return tier_name
      
    return 'BRONZE'
  
  @staticmethod
  def get_tier_info(tier_name):
    return RankingService.TIER_SYSTEM.get(
      tier_name,
      RankingService.TIER_SYSTEM['BRONZE']
    )
  
  # ========================================================================
  # 날짜 관련 유틸리티 메서드
  # ========================================================================
  @staticmethod
  def get_current_week_dates():
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end
  
  # ========================================================================
  # 리그 생성 및 관리 메서드
  # ========================================================================
  @staticmethod
  @transaction.atomic
  def get_or_create_weekly_league(tier):
    week_start, week_end = RankingService.get_current_week_dates()

    # ========================================================================
    # 기존 리그 찾기 (복잡한 쿼리)
    # ========================================================================
    available_league = League.objects.filter(
      # 1단계: 기본 조건으로 필터링
      tier=tier,
      week_start=week_start,
      is_active=True,
      is_finished=False
    ).annotate(
      # 2단계: 계산된 필드 추가
      participant_count=Count('participants')
    ).filter(
      # 3단계: annotate로 계산한 값으로 추가 필터링
      participant_count__lt=F('max_participants')
    ).first()

    # ====================================================================
    # 리그가 없으면 새로 생성
    # ====================================================================
    if not available_league:
      available_league = League.objects.create(
        tier=tier,
        week_start=week_start,
        week_end=week_end,
        max_participants=50,
        current_participants=0
      )
    return available_league
  
  # ========================================================================
  # EXP 추가 및 랭킹 업데이트 (𖤐핵심 메서드𖤐!)
  # ========================================================================
  @staticmethod
  @transaction.atomic
  def add_exp_to_user(user, exp_amount, exp_type='coding'):

    # 1단계: 유저 총 EXP 업데이트
    User.objects.filter(user_id=user.user_id).update(
      exp=F('exp') + exp_amount
    )

    user.refresh_from_db()

    # 2단계: 유저의 현재 티어 확인
    current_tier = RankingService.get_user_tier(user.exp)

    #3단계: 이번 주 리그 참가 확인 또는 생성
    league = RankingService.get_or_create_weekly_league(current_tier)

    # 4단계: 리그 참가자 정보 업데이트
    participant, created = LeagueParticipant.objects.get_or_create(
      league=league,
      user=user,
      defaults={
        'current_rank': 0,
        'previous_rank': 0
      }
    )

    if created:
      league.add_participant()

    # 5단계: 주간 EXP 업데이트 (타입별로)
    if exp_type == 'coding':
      participant.weekly_coding_exp += exp_amount
    elif exp_type == 'certification':
      participant.weekly_cert_exp += exp_amount

    participant.last_activity_at = timezone.now()
    participant.total_activities += 1
    participant.save(update_fields=[
      'weekly_coding_exp',
      'weekly_cert_exp',
      'last_activity_at',
      'total_activities'
    ])

    # 6단계: 리그 내 순위 재계산
    RankingService.update_league_rankings(league)

    # 7단계: 전체 랭킹 업데이트
    RankingService.update_global_ranking(user)

    # 8단계: 결과 딕셔너리 반환
    return {
      # 이 딕셔너리는 API 응답으로 사용됨
      'user_id': str(user.user_id),
      'total_exp': user.exp,
      'tier': current_tier,
      'weekly_exp': participant.weekly_total_exp,
      'league_rank': participant.current_rank,
      'rank_change': participant.rank_change,
      'status': participant.status
    }
  
  # ========================================================================
  # 리그 순위 업데이트 메서드
  # ========================================================================
  @staticmethod
  @transaction.atomic
  def update_league_rankings(league):
    # 참가자 쿼리 (정렬)
    participants = LeagueParticipant.objects.filter(
      league=league
    ).annotate(
      total_weekly_exp=F('weekly_coding_exp') + F('weekly_cert_exp')
    ).order_by('-total_weekly_exp', 'joined_at')

    total_count = participants.count()

    # 순위 부여 및 업데이트
    for rank, participant in enumerate(participants, start=1):
      # 순위 업데이트
      participant.update_rank(rank)

      # 승급/강등 상태 업데이트
      participant.update_status(total_count)

  # ========================================================================
  # 리그 랭킹 조회 메서드
  # ========================================================================
  @staticmethod
  def get_league_rankings(user):
    week_start, week_end = RankingService.get_current_week_dates()

    try:
      # 유저가 속한 리그 찾기
      participant = LeagueParticipant.objects.select_related(
        'league', 'user'
      ).get(
        user=user,
        league__week_start=week_start,
        league__is_active=True
      )

      # 같은 리그의 모든 참가자 가져오기
      league_participants = (
        LeagueParticipant.objects
        .filter(league=participant.league)
        .select_related('user')
        .annotate(
          total_exp=F('weekly_coding_exp') + F('weekly_cert_exp')
        )
        .order_by('-total_exp', 'joined_at')
      )

      # 참가자 리스트를 딕셔너리 리스트로 변환
      participants_data = []

      for p in league_participants:
        participants_data.append({
          'rank': p.current_rank,
          'user_id': str(p.user.user_id),
          'nickname': p.user.nickname,
          'profile_image': p.user.profile_image_url,
          'weekly_exp': p.weekly_total_exp,
          'coding_exp': p.weekly_coding_exp,
          'cert_exp': p.weekly_cert_exp,
          'status': p.status,
          'rank_change': p.rank_change,
          'is_me': p.user.user_id == user.user_id
        })

      tier_info = RankingService.get_tier_info(participant.league.tier)

      # 최종 결과 딕셔너리 반환
      return {
        'success': True,
        'my_rank': participant.current_rank,
        'my_exp': participant.weekly_total_exp,
        'my_status': participant.status,
        'rank_change': participant.rank_change,
        'tier': participant.league.tier,
        'tier_info': tier_info,
        'league_id': str(participant.league.league_id),
        'week_start': str(participant.league.week_start),
        'week_end': str(participant.league.week_end),
        'days_remaining': participant.league.days_remaining,
        'total_participants': participant.league.current_participants,
        'rankings': participants_data
      }
    
    except LeagueParticipant.DoesNotExist:
      # 참가 기록이 없으면 (이번 주 아직 문제 안 풀음)
      
      current_tier = RankingService.get_user_tier(user.exp)
      tier_info = RankingService.get_tier_info(current_tier)
      
      return {
          'success': False,
          'message': '아직 이번 주 리그에 참가하지 않았습니다.',
          'tier': current_tier,
          'tier_info': tier_info
      }
  

  # ========================================================================
  # 전체 랭킹 조회 메서드
  # ========================================================================

  @staticmethod
  def get_global_rankings(limit=100, offset=0):

    rankings = (
      GlobalRanking.objects
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

    return rankings_data
  

  # ========================================================================
  # 전체 랭킹 업데이트 메서드
  # ========================================================================
  
  @staticmethod
  @transaction.atomic
  def update_global_ranking(user):

    current_tier = RankingService.get_user_tier(user.exp)

    # GlobalRanking 업데이트 또는 생성
    global_ranking, created = GlobalRanking.objects.update_or_create(
      user=user,
      defaults={
        'total_exp': user.exp,
        'current_tier': current_tier
      }
    )

    # 전체 순위 재계산
    rank = (
      GlobalRanking.objects
      .filter(total_exp__gt=user.exp)
      .count() + 1
    )

    global_ranking.rank = rank
    global_ranking.save(update_fields=['rank'])

    return global_ranking
  

  # ========================================================================
  # 주간 승급/강등 처리 메서드 (Celery 스케줄러용)
  # ========================================================================

  @staticmethod
  @transaction.atomic
  def process_weekly_promotion_demotion():

    today = timezone.now().date()

    # 일요일 체크
    if today.weekday() != 6:
      return {
        'success': False,
        'message': '일요일에만 실행됩니다.'
      }
    
    # 오늘 종료되는 리그 찾기
    active_leagues = League.objects.filter(
      week_end=today,     # 오늘 종료되는 리그
      is_active=True,     # 활성 상태
      is_finished=False   # 아직 종료 처리 안 됨
    )

    processed_count = 0   # 처리된 리그 수 카운터

    # 각 리그 처리
    for league in active_leagues:

      # 리그 참가자들 가져오기
      participants = (
        LeagueParticipant.objects
        .filter(league=league)
        .order_by('current_rank')
      )

      total_participants = participants.count() # 총 참가자 수

      # 각 참가자의 최종 기록 저장
      for participant in participants:

        # 히스토리 테이블에 기록 저장
        UserRankingHistory.objects.create(
          user=participant.user,
          league=league,
          final_rank=participant.current_rank,
          final_exp=participant.weekly_total_exp,
          final_coding_exp=participant.weekly_coding_exp,
          final_cert_exp=participant.weekly_cert_exp,

          result=(
            'PROMOTED' if participant.status == 'PROMOTION'
            else 'DEMOTED' if participant.status == 'DEMOTION'
            else 'MAINTAINED'
          ),

          reward_coins=RankingService.calculate_reward(
            participant.current_rank,
            league.tier
          )
        )
      
      # 리그 종료 처리
      league.is_active = False  # 비활성화
      league.is_finished = True # 종료 완료

      league.save(update_fields=['is_active', 'is_finished']) # 두 필드만 업데이트

      processed_count += 1      # 카운터 증가

    # 결과 반환
    return {
      'success': True,
      'processed_leagues': processed_count,
      'date': str(today)
    }


  # ========================================================================
  # 보상 계산 메서드
  # ========================================================================

  @staticmethod
  def calculate_reward(rank, tier):

    tier_info = RankingService.get_tier_info(tier)  # 티어 정보 가져오기
    base_reward = 100 # 기본 보상: 100 코인

    # 순위에 따른 보상 배율
    if rank == 1:             # 1등
      rank_multiplier = 5.0   # 5배
    
    elif rank <= 3:           # 2~3등
      rank_multiplier = 3.0   # 3배

    elif rank <= 10:          # 4~10등
      rank_multiplier = 2.0   # 2배

    elif rank <= 20:          # 11~20등
      rank_multiplier = 1.5   # 1.5배

    else:                     # 21등 이하
      rank_multiplier = 1.0   # 1배 (기본)
    

    # 티어에 따른 보상 배율
    tier_multiplier = tier_info['order']

    # 최종 보상 계산
    total_reward = int(base_reward * rank_multiplier * tier_multiplier)

    return total_reward
  

  # ========================================================================
  # 유저 랭킹 히스토리 조회 메서드
  # ========================================================================
  
  @staticmethod
  def get_user_ranking_history(user, limit=10):
    history = (
      UserRankingHistory.objects
      .filter(user=user)
      .select_related('league')
      .order_by('-recorded_at')[:limit]
    )

    history_data = []

    for record in history:
      tier_info = RankingService.get_tier_info(record.league.tier)

      history_data.append({
        'week_start': str(record.league.week_start),
        'week_end': str(record.league.week_end),
        'tier': record.league.tier,
        'tier_icon': tier_info['icon'],
        'final_rank': record.final_rank,
        'final_exp': record.final_exp,
        'result': record.result,
        'reward_coins': record.reward_coins,
        'recorded_at': record.recorded_at.isoformat()
      })
    
    return history_data