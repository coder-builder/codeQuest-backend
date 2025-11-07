""" 
================================================================================
랭킹 시스템 데이터베이스 모델 파일
================================================================================
"""

from django.db import models # Django의 모델(ORM) 기능을 사용하기 위한 기본 모듈
from django.utils import timezone # timezone-aware한 시간/날짜 처리를 위해 사용
from datetime import timedelta, datetime # 파이썬 표준 라이브러리의 날짜/시간 도구들
import uuid # UUID를 생성하기 위한 파이썬 표준 라이브러리


# ============================================================================
# League 모델 (리그 테이블)
# ============================================================================
class League(models.Model):
  """
  주간 리그 모델 - 듀오링고 스타일
  각 티어별로 매주 새로운 리그가 생성됨
  """
  TIER_CHOICES = [
    ('BRONZE', 'Bronze'),         # 0 ~ 999 XP
    ('SILVER', 'Silver'),         # 1,000 ~ 2,499 XP
    ('GOLD', 'Gold'),             # 2,500 ~ 4,999 XP
    ('PLATINUM', 'Platinum'),     # 5,000 ~ 9,999 XP
    ('DIAMOND', 'Diamond'),       # 10,000 ~ 19,999 XP
    ('MASTER', 'Master'),         # 20,000 ~ 49,999 XP
    ('LEGEND', 'Legend')          # 50,000+ XP
  ]

  league_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  tier = models.CharField(max_length=20, choices=TIER_CHOICES, db_index=True)

  # 기간
  week_start = models.DateField(db_index=True, verbose_name='리그 시작일')
  week_end = models.DateField(verbose_name='리그 종료일')

  # 리그 정원 관련 필드
  max_participants = models.IntegerField(default=50, verbose_name='최대 참가자 수')
  current_participants = models.IntegerField(default=0, verbose_name='현재 참가자 수')

  # 리그 상태 필드
  is_active = models.BooleanField(default=True, db_index=True, verbose_name='활성 상태')
  is_finished = models.BooleanField(default=False, verbose_name='종료 여부')

  # 타임스탬프 필드 (생성/수정 시간 자동 기록)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  # Meta 클래스 (테이블 메타데이터 설정)
  class Meta:
    db_table = 'leagues'
    ordering = ['-week_start', 'tier']
    unique_together = [('tier', 'week_start', 'league_id')]
    indexes = [
      models.Index(fields=['tier', 'week_start', 'is_active']),
      models.Index(fields=['is_active', 'is_finished']),
    ]
    verbose_name = '리그'
    verbose_name_plural = '리그 목록'

  # __str__ 메서드
  def __str__(self):
    return f"{self.get_tier_display()} League - Week {self.week_start}"
  
  # @property 데코레이터
  @property
  def is_full(self):
    return self.current_participants >= self.max_participants
  
  @property
  def days_remaining(self):
    today = timezone.now().date()
    if today > self.week_end:
      return 0
    return (self.week_end - today).days + 1
  
  # 인스턴스 메서드 (객체의 동작 정의)
  def add_participant(self):
    if not self.is_full:
      self.current_participants += 1
      self.save(update_fields=['current_participants'])
      return True
    return False
  
  def remove_participant(self):
    if self.current_participants > 0:
      self.current_participants -= 1
      self.save(update_fields=['current_participants'])


# ============================================================================
# LeagueParticipant 모델 (리그 참가자 테이블)
# ============================================================================
class LeagueParticipant(models.Model):

  # 승급/강등 상태 선택지
  PROMOTION_STATUS_CHOICES = [
    ('SAFE', 'Safe'),           # 안전권 (11~40위)
    ('PROMOTION', 'Promotion'),  # 승급권 (1~10위)
    ('DEMOTION', 'Demotion')    # 강등권 (41~50위)
  ]

  participant_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='participants', db_index=True)
  user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='league_participations')

  # 주간 EXP 필드 (코딩 + 자격증 분리 추적)
  weekly_coding_exp = models.IntegerField(default=0, verbose_name='주간 코딩 EXP')
  weekly_cert_exp = models.IntegerField(default=0, verbose_name='주간 자격증 EXP')

  # 순위 정보 필드
  current_rank = models.IntegerField(default=0, db_index=True, verbose_name='현재 순위')
  previous_rank = models.IntegerField(default=0, verbose_name='이전 순위')
  highest_rank = models.IntegerField(default=0, verbose_name='최고 순위')

  # 승급/강등 상태 필드
  status = models.CharField(max_length=20, choices=PROMOTION_STATUS_CHOICES, default='SAFE', verbose_name='승급/강등 상태')

  # 활동 추적 필드
  last_activity_at = models.DateTimeField(null=True, blank=True, verbose_name='마지막 활동 시간')
  total_activities = models.IntegerField(default=0, verbose_name='총 활동 횟수')

  # 타임스탬프 필드
  joined_at = models.DateTimeField(auto_now_add=True, verbose_name='참가 시간')
  updated_at = models.DateTimeField(auto_now=True, verbose_name='업데이트 시간')

  # Meta 클래스
  class Meta:
    db_table = 'league_participants'

    ordering = ['current_rank', 'joined_at']
    unique_together = [('league', 'user')]
    indexes = [
      models.Index(fields=['league', 'current_rank']),
      models.Index(fields=['user', 'league']),
      models.Index(fields=['-weekly_coding_exp', '-weekly_cert_exp'])
    ]

    verbose_name = '리그 참가자'
    verbose_name_plural = '리그 참가자 목록'

  # __str__ 메서드
  def __str__(self):
    return f"{self.user.nickname} - Rank #{self.current_rank} ({self.weekly_total_exp} XP)"
  
  # @property (계산된 속성)
  @property
  def weekly_total_exp(self):
    return self.weekly_coding_exp + self.weekly_cert_exp
  
  @property
  def rank_change(self):
    if self.previous_rank == 0:
      return 0
    
    return self.previous_rank - self.current_rank
  
  @property
  def rank_trend(self):
    change = self.rank_change
    if change > 0:      # 양수 -> 순위 상승
      return 'UP'
    elif change < 0:    # 음수 -> 순위 하락
      return 'DOWN'
    
    return 'SAME'       # 0 -> 순위 유지
  
  # 인스턴스 메서드
  def add_exp(self, exp_amount, exp_type='coding'):
    if exp_type == 'coding':
      self.weekly_coding_exp += exp_amount      # 코딩 문제 EXP
    elif exp_type == 'certification':
      self.weekly_cert_exp += exp_amount        # 자격증 문제 EXP

    self.last_activity_at = timezone.now()      # 현재 시간으로 마지막 활동 시간 갱신
    self.total_activities += 1                  # 활동 횟수 1 증가

    self.save(update_fields=[
      'weekly_coding_exp',
      'weekly_cert_exp',
      'last_activity_at',
      'total_activities'
    ])

  def update_rank(self, new_rank):
    self.previous_rank = self.current_rank  # 현재 순위를 이전 순위로 백업
    self.current_rank = new_rank            # 새로운 순위 설정
    
    # 최고 순위 갱신 체크
    # 조건 1: 최고 순위가 0이면 (첫 순위)
    # 조건 2: 새 순위가 기존 최고 순위보다 높으면 (작은 숫자)
    if self.highest_rank == 0 or new_rank < self.highest_rank:
      self.highest_rank = new_rank

    self.save(update_fields=['previous_rank', 'current_rank', 'highest_rank'])
  
  def update_status(self, total_participants):      # total_participants: 리그 내 총 참가자 수
    if self.current_rank <= 10:
      self.status = 'PROMOTION'     # 1위 ~ 10위
    elif self.current_rank > total_participants - 10:
      self.status = 'DEMOTION'      # ex) 50명이면 41위 ~50위 / current_rank > 50 - 10 = 40 / 즉, 41위 이상
    else:
      self.status = 'SAFE'          # 11위 ~ 40위

    self.save(update_fields=['status'])


# ============================================================================
# UserRankingHistory 모델 (유저 랭킹 히스토리 테이블)
# ============================================================================
class UserRankingHistory(models.Model):
  history_id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False
  )

  user = models.ForeignKey(
    'users.User',
    on_delete=models.CASCADE,         # 유저 탈퇴 시 히스토리도 삭제 (또는 PROTECT로 변경하여 히스토리 보존 가능)
    related_name='ranking_history'    # user.ranking_history.all() → 이 유저의 모든 주간 랭킹 히스토리
  )

  league = models.ForeignKey(
    League,
    on_delete=models.CASCADE,
    related_name='history_records'
  )

  # 최종 기록 필드
  final_rank = models.IntegerField(verbose_name='최종 순위')
  final_exp = models.IntegerField(verbose_name='최종 EXP')
  final_coding_exp = models.IntegerField(verbose_name='최종 코딩 EXP')
  final_cert_exp = models.IntegerField(verbose_name='최종 자격증 EXP')

  # 승급/강등 결과 필드
  RESULT_CHOICES = [
    ('PROMOTED', 'Promoted'),       # 승급됨
    ('DEMOTED', 'Demoted'),         # 강등됨
    ('MAINTAINED', 'Maintained'),   # 티어 유지
  ]

  result = models.CharField(
    max_length=20,
    choices=RESULT_CHOICES,
    verbose_name='결과'
  )

  # 보상 필드
  reward_coins = models.IntegerField(
    default=0,
    verbose_name='획득 코인'
  )

  reward_items = models.JSONField(
    default=dict,
    blank=True,
    verbose_name='획득 아이템'
  )

  # 타임스탬프
  recorded_at = models.DateTimeField(
    auto_now_add=True,
    verbose_name='기록 시간'
  )

  # Meta 클래스
  class Meta:
    db_table = 'user_ranking_history'

    ordering = ['-recorded_at']   # 최신순 정렬 (최근 주부터)

    indexes = [
      models.Index(fields=['user', '-recorded_at']),  # "이 유저의 최근 랭킹 히스토리" 쿼리 최적화
      models.Index(fields=['league', 'final_rank']),  # "이 리그의 순위별 기록" 쿼리 최적화
    ]

    verbose_name = '랭킹 히스토리'
    verbose_name_plural = '랭킹 히스토리 목록'

  def __str__(self):
    return f"{self.user.nickname} - {self.league} - Rank #{self.final_rank}"
  

# ============================================================================
# TierConfig 모델 (티어 설정 테이블)
# ============================================================================
class TierConfig(models.Model):
  TIER_CHOICES = [
    ('BRONZE', 'Bronze'),
    ('SILVER', 'Silver'),
    ('GOLD', 'Gold'),
    ('PLATINUM', 'Platinum'),
    ('DIAMOND', 'Diamond'),
    ('MASTER', 'Master'),
    ('LEGEND', 'Legend')
  ]

  tier = models.CharField(
    max_length=20,
    choices=TIER_CHOICES,
    unique=True,
    primary_key=True
  )

  # EXP 범위 필드
  min_exp = models.IntegerField(verbose_name='최소 EXP')
  max_exp = models.IntegerField(verbose_name='최대 EXP')

  # 티어 표시 정보
  icon = models.CharField(
    max_length=10,
    verbose_name='아이콘'
  )

  color = models.CharField(
    max_length=7,
    verbose_name='색상 코드'
  )

  order = models.IntegerField(
    unique=True,
    verbose_name='순서'
  )

  # 보상 배율
  coin_multiplier = models.FloatField(
    default=1.0,
    verbose_name='코인 배율'
  )

  # Meta 클래스
  class Meta:
    db_table = 'tier_configs'

    ordering = ['order']

    verbose_name = '티어 설정'
    verbose_name_plural = '티어 설정 목록'

  def __str__(self):
    return f"{self.get_tier_display()} ({self.min_exp}-{self.max_exp} XP)"
  

# ============================================================================
# GlobalRanking 모델 (전체 랭킹 테이블)
# ============================================================================
class GlobalRanking(models.Model):
  user = models.OneToOneField(
    'users.User',
    on_delete=models.CASCADE,
    primary_key=True,
    related_name='global_ranking'
  )

  # 순위 필드
  rank = models.IntegerField(
    db_index=True,
    verbose_name='전체 순위'
  )

  # EXP 정보
  total_exp = models.IntegerField(
    default=0,
    verbose_name='총 EXP'
  )

  # 티어 필드
  current_tier = models.CharField(
    max_length=20,
    db_index=True,
    verbose_name='현재 티어'
  )

  # 통계 필드
  total_coding_problems = models.IntegerField(
    default=0,
    verbose_name='총 코딩 문제 수'
  )

  total_cert_problems = models.IntegerField(
    default=0,
    verbose_name='총 자격증 문제 수'
  )

  # 타임스탬프
  last_updated = models.DateTimeField(
    auto_now=True,
    verbose_name='마지막 업데이트'
  )

  # Meta 클래스
  class Meta:
    db_table = 'global_rankings'

    ordering = ['rank']   # rank 기준 오름차순 (1위부터)

    indexes =[
      models.Index(fields=['rank']),                    # 순위로 조회 (TOP 100 등)
      models.Index(fields=['current_tier', 'rank']),    # 티어별 순위 조회 / "GOLD 티어 중 상위 10명"
    ]

    verbose_name = '전체 랭킹'
    verbose_name_plural = '전체 랭킹 목록'

  def __str__(self):
    return f"#{self.rank} - {self.user.nickname} ({self.total_exp} XP)"     # 예: "#126 - 호빵맨 (15,430 XP)"