from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, date
import uuid

# Create your models here.

class UserProgress(models.Model):
  """사용자 전체 학습 진도"""
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='progress'
  )

  # 전체 학습 통계
  total_lessons_completed = models.IntegerField(default=0)
  total_problems_solved = models.IntegerField(default=0)
  total_study_time_minutes = models.IntegerField(default=0)  # in minutes
  total_exp_earned = models.IntegerField(default=0)

  # 현재 학습 상태
  current_world = models.CharField(max_length=50, blank=True)
  current_stage = models.IntegerField(default=1)
  current_lesson = models.IntegerField(default=1)

  # 연속 학습 (Streak)
  current_streak = models.IntegerField(default=0)
  longest_streak = models.IntegerField(default=0)
  last_study_date = models.DateField(null=True, blank=True)

  # 주간 목표
  weekly_goal_days = models.IntegerField(default=5)  # 주간 목표 일수
  current_week_days = models.IntegerField(default=0)  # 이번 주 달성 일수
  week_start_date = models.DateField(null=True, blank=True)  # 주간 목표 시작일

  # 성취도
  accuracy_rate = models.FloatField(default=0.0)  # 정답률
  average_completion_time = models.FloatField(default=0.0)  # 평균 완료 시간 (분 단위)

  # 타임스탬프
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    db_table = 'user_progress'
    verbose_name = '사용자 진도'
  
  def __str__(self):
    return f"{self.user.nickname} - {self.current_streak}일 연속 학습"
  
  def update_streak(self):
    """연속 학습일 업데이트"""
    today = date.today()

    if self.last_study_date == today:
      return self.current_streak  # 이미 오늘 학습함
    
    if self.last_study_date == today - timedelta(days=1):
      # 연속 학습일 증가
      self.current_streak += 1
      if self.current_streak > self.longest_streak:
        self.longest_streak = self.current_streak

    else:
      # 연속 학습일 초기화
      self.current_streak = 1

    self.last_study_date = today
    self.save(update_fields=['current_streak', 'longest_streak', 'last_study_date'])
    return self.current_streak
  
  def update_weekly_goal(self):
    """주간 목표 달성 일수 업데이트"""
    today = date.today()
    week_start = today = timedelta(days=today.weekday())

    if self.week_start_date != week_start:
      # 새로운 주 시작
      self.current_week_days = 0
      self.week_start_date = week_start

    # 오늘 학습했는지 체크
    if not self.daily_studies.filter(study_date=today).exists():
      self.current_week_days += 1

    self.save(update_fields=['current_week_days', 'week_start_date'])

  def get_weekly_progress_percentage(self):
    """주간 목표 달성률"""
    if self.weekly_goal_days == 0:
      return 0.0
    
    return min((self.current_week_days / self.weekly_goal_days) * 100, 100.0)
  

class WorldProgress(models.Model):
  """월드별 진도 (Python, JavaScript 등)"""
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
  )
  world_name = models.CharField(max_length=50)

  # 진행률
  total_stages = models.IntegerField(default=0)
  completed_stages = models.IntegerField(default=0)
  current_stage = models.IntegerField(default=1)

  total_lessons = models.IntegerField(default=0)
  completed_lessons = models.IntegerField(default=0)

  # 통계
  exp_earned = models.IntegerField(default=0)
  time_spent_minutes = models.IntegerField(default=0)
  accuracy_rate = models.FloatField(default=0.0) # 정답률

  # 상태
  is_unlocked = models.BooleanField(default=False)
  is_completed = models.BooleanField(default=False)
  started_at = models.DateTimeField(null=True, blank=True)
  completed_at = models.DateTimeField(null=True, blank=True)

  # 타임스탬프
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    db_table = 'world_progress'
    verbose_name = '월드 진도'
    unique_together = ['user', 'world_name']

  def __str__(self):
    return f"{self.user.nickname} - {self.world_name} ({self.completed_lessons}/{self.total_lessons})"
  
  @property # @property 데코레이터를 사용하여 메서드를 속성처럼 접근 가능하게 함
  def completion_percentage(self):
    """월드 완료 퍼센티지 계산"""
    if self.total_lessons == 0:
      return 0.0
    return (self.completed_lessons / self.total_lessons) * 100
  

class LessonProgress(models.Model):
  """레슨별 진도"""
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
  )

  # 레슨 식별
  world_name = models.CharField(max_length=50)
  stage_number = models.IntegerField()
  lesson_number = models.IntegerField()

  # 진행 상태
  STATUS_CHOICES = [
    ('locked', '잠김'),
    ('unlocked', '해제됨'),
    ('in_progress', '진행 중'),
    ('completed', '완료됨'),
    ('mastered', '마스터'),
  ]

  status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default='locked'
  )

  # 성과
  total_problems = models.IntegerField(default=0)
  solved_problems = models.IntegerField(default=0)
  correct_answers = models.IntegerField(default=0)
  total_attempts = models.IntegerField(default=0)

  # 점수/시간
  best_score = models.IntegerField(default=0)
  total_time_seconds = models.IntegerField(default=0)  # in seconds
  exp_earned = models.IntegerField(default=0)

  # 타임스탬프
  first_started_at = models.DateTimeField(null=True, blank=True)
  first_completed_at = models.DateTimeField(null=True, blank=True)
  last_attempt_at = models.DateTimeField(null=True, blank=True)

  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    db_table = 'lesson_progress'
    verbose_name = '레슨 진도'
    unique_together = ['user', 'world_name', 'stage_number', 'lesson_number']
    indexes = [
      models.Index(fields=['user', 'status']),
      models.Index(fields=['world_name', 'stage_number']),
    ]

  def __str__(self):
    return f"{self.user.nickname} - {self.world_name} S{self.stage_number}-L{self.lesson_number} ({self.status})"
  
  @property
  def accuracy_rate(self):
    """정확도 계산"""
    if self.total_attempts == 0:
      return 0.0
    return (self.correct_answers / self.total_attempts) * 100
  

class DailyStudy(models.Model):
  """일일 학습 기록"""
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name='daily_studies'
  )
  study_date = models.DateField()

  # 학습량
  lessons_completed = models.IntegerField(default=0)
  problems_solved = models.IntegerField(default=0)
  exp_earned = models.IntegerField(default=0)
  study_time_minutes = models.IntegerField(default=0)

  # 성과
  correct_answers = models.IntegerField(default=0)
  total_attempts = models.IntegerField(default=0)

  # 목표 달성 여부
  goal_achieved = models.BooleanField(default=False)

  # 타임스탬프
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    db_table = 'daily_studies'
    verbose_name = '일일 학습 기록'
    unique_together = ['user', 'study_date']
    ordering = ['-study_date']
    indexes = [
      models.Index(fields=['user', 'study_date']),
      models.Index(fields=['study_date']),
    ]

  def __str__(self):
    return f"{self.user.nickname} - {self.study_date} ({self.lessons_completed} 레슨 완료)"
  
  @property
  def accuracy_rate(self):
    """정확도 계산"""
    if self.total_attempts == 0:
      return 0.0
    return (self.correct_answers / self.total_attempts) * 100
  

  class StudySession(models.Model):
    """학습 세션"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
      settings.AUTH_USER_MODEL,
      on_delete=models.CASCADE,
      related_name='study_sessions'
    )

    # 세션 정보
    session_start = models.DateTimeField(default=timezone.now)
    session_end = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)  # in seconds

    # 학습 내용
    world_name = models.CharField(max_length=50)
    stage_number = models.IntegerField()
    lesson_number = models.IntegerField()

    # 세션 성과
    problems_attempted = models.IntegerField(default=0)
    problems_solved = models.IntegerField(default=0)
    exp_gained = models.IntegerField(default=0)

    # 상태
    is_active = models.BooleanField(default=True)
    completed_successfully = models.BooleanField(default=False)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
      db_table = 'study_sessions'
      verbose_name = '학습 세션'
      ordering = ['-session_start']
      indexes = [
        models.Index(fields=['user', 'is_active']),
        models.Index(fields=['session_start']),
      ]

    def __str__(self):
      return f"{self.user.nickname} - {self.session_start.strftime('%Y-%m-%d %H:%M')}"

    def end_session(self):
      """세션 종료"""
      if self.session_end is None:
        self.session_end = timezone.now()
        self.duration_seconds = int((self.session_end - self.session_start).total_seconds())
        self.is_active = False
        self.completed_successfully = True
        self.save()