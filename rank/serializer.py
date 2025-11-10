""" 
================================================================================
랭킹 시스템 시리얼라이저 파일
================================================================================
"""

from rest_framework import serializers
from .models import (
  League,
  LeagueParticipant,
  UserRankingHistory,
  TierConfig,
  GlobalRanking
)
from users.models import User


# ============================================================================
# 유저 기본 정보 시리얼라이저 (중첩용)
# ============================================================================

class UserBasicSerializer(serializers.ModelSerializer):
  # 랭킹에서 보여줄 유저 기본 정보
  class Meta:
    model = User
    fields = ['user_id', 'nickname', 'profile_image_url', 'exp']
    read_only_fields = fields


# ============================================================================
# 티어 설정 시리얼라이저
# ============================================================================

class TierConfigSerializer(serializers.ModelSerializer):
  # 티어 설정 정보
  tier_display = serializers.CharField(source='get_tier_display', read_only=True)

  class Meta:
    model = TierConfig
    fields = [
      'tier',
      'tier_display',
      'min_exp',
      'max_exp',
      'icon',
      'color',
      'order',
      'coin_multiplier'
    ]
    read_only_fields = fields


# ============================================================================
# 리그 시리얼라이저
# ============================================================================
class LeagueSerializer(serializers.ModelSerializer):
  # 리그 기본 정보
  tier_display = serializers.CharField(source='get_tier_display', read_only=True)
  is_full = serializers.BooleanField(read_only=True)
  days_remaining = serializers.IntegerField(read_only=True)

  class Meta:
    model = League
    fields = [
      'league_id',
      'tier',
      'tier_display',
      'week_start',
      'week_end',
      'max_participants',
      'current_participants',
      'is_active',
      'is_finished',
      'is_full',
      'days_remaining'
    ]
    read_only_fields = fields


# ============================================================================
# 리그 참가자 시리얼라이저
# ============================================================================

class LeagueParticipantSerializer(serializers.ModelSerializer):
  # 리그 참가자 정보
  user = UserBasicSerializer(read_only=True)
  weekly_total_exp = serializers.IntegerField(read_only=True)
  rank_change = serializers.IntegerField(read_only=True)
  rank_trend = serializers.CharField(read_only=True)
  status_display = serializers.CharField(source='get_status_display', read_only=True)

  class Meta:
    model = LeagueParticipant
    fields = [
      'participant_id',
      'user',
      'weekly_coding_exp',
      'weekly_cert_exp',
      'weekly_total_exp',
      'current_rank',
      'previous_rank',
      'highest_rank',
      'rank_change',
      'rank_trend',
      'status',
      'status_display',
      'last_activity_at',
      'total_activities'
        ]
    read_only_fields = fields


# ============================================================================
# 리그 랭킹 상세 시리얼라이저 (리그 + 참가자들)
# ============================================================================

class LeagueRankingDetailSerializer(serializers.ModelSerializer):
  # 리그 전체 랭킹 정보 (리그 + 참가자 리스트)
  tier_display = serializers.CharField(source='get_tier_display', read_only=True)
  participants = LeagueParticipantSerializer(many=True, read_only=True)
  days_remaining = serializers.IntegerField(read_only=True)

  class Meta:
    model = League
    fields = [
      'league_id',
      'tier',
      'tier_display',
      'week_start',
      'week_end',
      'days_remaining',
      'max_participants',
      'current_participants',
      'participants'
    ]
    read_only_fields = fields


# ============================================================================
# 내 리그 랭킹 정보 시리얼라이저 (응답용)
# ============================================================================

class MyLeagueRankingSerializer(serializers.Serializer):
  # 내가 속한 리그의 랭킹 정보 (응답 전용)
  success = serializers.BooleanField()
  message = serializers.CharField(required=False)

  # 내 정보
  my_rank = serializers.IntegerField(required=False)
  my_exp = serializers.IntegerField(required=False)
  my_status = serializers.CharField(required=False)
  rank_change = serializers.IntegerField(required=False)

  # 티어 정보
  tier = serializers.CharField(required=False)
  tier_info = serializers.DictField(required=False)

  # 리그 정보
  league_id = serializers.UUIDField(required=False)
  week_start = serializers.DateField(required=False)
  week_end = serializers.DateField(required=False)
  days_remaining = serializers.IntegerField(required=False)
  total_participants = serializers.IntegerField(required=False)

  # 랭킹 리스트
  rankings = serializers.ListField(
    child=serializers.DictField(),
    required=False
  )


# ============================================================================
# 전체 랭킹 시리얼라이저
# ============================================================================

class GlobalRankingSerializer(serializers.ModelSerializer):
  # 전체 랭킹 정보
  user = UserBasicSerializer(read_only=True)

  class Meta:
    model = GlobalRanking
    fields = [
      'user',
      'rank',
      'total_exp',
      'current_tier',
      'total_coding_problems',
      'total_cert_problems',
      'last_updated'
    ]
    read_only_fields = fields


# ============================================================================
# 전체 랭킹 리스트 시리얼라이저 (응답용)
# ============================================================================

class GlobalRankingListSerializer(serializers.Serializer):
  # 전체 랭킹 리스트 응답
  rank = serializers.IntegerField()
  user_id = serializers.UUIDField()
  nickname = serializers.CharField()
  profile_image = serializers.URLField(allow_null=True)
  total_exp = serializers.IntegerField()
  tier = serializers.CharField()
  tier_icon = serializers.CharField()
  tier_color = serializers.CharField()


# ============================================================================
# 랭킹 히스토리 시리얼라이저
# ============================================================================

class UserRankingHistorySerializer(serializers.ModelSerializer):
  # 유저 주간 랭킹 히스토리
  league = LeagueSerializer(read_only=True)
  result_display = serializers.CharField(source='get_result_display', read_only=True)

  class Meta:
    model = UserRankingHistory
    fields = [
      'history_id',
      'league',
      'final_rank',
      'final_exp',
      'final_coding_exp',
      'final_cert_exp',
      'result',
      'result_display',
      'reward_coins',
      'reward_items',
      'recorded_at'
    ]
    read_only_fields = fields


# ============================================================================
# 랭킹 히스토리 리스트 시리얼라이저 (응답용)
# ============================================================================

class RankingHistoryListSerializer(serializers.Serializer):
  # 랭킹 히스토리 리스트 응답
  week_start = serializers.DateField()
  week_end = serializers.DateField()
  tier = serializers.CharField()
  tier_icon = serializers.CharField()
  final_rank = serializers.IntegerField()
  final_exp = serializers.IntegerField()
  result = serializers.CharField()
  reward_coins = serializers.IntegerField()
  recorded_at = serializers.DateTimeField()


# ============================================================================
# EXP 추가 요청 시리얼라이저
# ============================================================================

class AddExpRequestSerializer(serializers.Serializer):
  # EXP 추가 요청
  exp_amount = serializers.IntegerField(min_value=1, required=True)
  exp_type = serializers.ChoiceField(
    choices=['coding', 'certification'],
    default='coding'
  )


# ============================================================================
# EXP 추가 응답 시리얼라이저
# ============================================================================

class AddExpResponseSerializer(serializers.Serializer):
  # EXP 추가 응답
  user_id = serializers.UUIDField()
  total_exp = serializers.IntegerField()
  tier = serializers.CharField()
  weekly_exp = serializers.IntegerField()
  league_rank = serializers.IntegerField()
  rank_change = serializers.IntegerField()
  status = serializers.CharField()