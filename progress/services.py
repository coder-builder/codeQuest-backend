from django.utils import timezone
from datetime import date
from .models import UserProgress, DailyStudy, LessonProgress, StudySession
from django.db import transaction

class ProgressService:
  """Progress 비즈니스 로직"""

  @staticmethod
  def get_or_create_user_progress(user):
    """사용자 진도 가져오기 또는 생성"""
    progress, created = UserProgress.objects.get_or_create(user=user)
    return progress
  
  @staticmethod
  @transaction.atomic
  def record_lesson_completion(user, world_name, stage_number, lesson_number,
                              problems_solved=0, exp_earned=0, study_time_minutes=0,
                              correct_answers=0, total_attempts=0):
    
    """레슨 완료 기록"""
    today = date.today()

    # 사용자 진도 업데이트
    progress = ProgressService.get_or_create_user_progress(user)
    
    progress.total_lessons_completed += 1
    progress.total_problems_solved += problems_solved
    progress.total_exp_earned += exp_earned
    progress.total_study_time_minutes += study_time_minutes
    
    progress.update_streak()
    progress.update_weekly_goal()
    progress.save()

    # 일일 학습 기록 업데이트
    daily_study, created = DailyStudy.objects.get_or_create(user=user, study_date=today, 
                                                          defaults={
                                                            'lessons_completed': 0,
                                                            'problems_solved': problems_solved,
                                                            'study_time_minutes': study_time_minutes,
                                                            'exp_earned': exp_earned,
                                                            'correct_answers': correct_answers,
                                                            'total_attempts': total_attempts,
                                                          })
    
    if not created:
      daily_study.lessons_completed += 1
      daily_study.problems_solved += problems_solved
      daily_study.exp_earned += exp_earned
      daily_study.study_time_minutes += study_time_minutes
      daily_study.correct_answers += correct_answers
      daily_study.total_attempts += total_attempts
      daily_study.save()

    # 레슨 진도 업데이트
    lesson_progress, created = LessonProgress.objects.get_or_create(
      user=user,
      world_name=world_name,
      stage_number=stage_number,
      lesson_number=lesson_number,
      defaults={
        'status': 'completed',
        'exp_earned': exp_earned,
      }
    )

    if lesson_progress.status != 'completed':
      lesson_progress.status = 'completed'
      lesson_progress.exp_earned = exp_earned
      lesson_progress.first_completed_at = timezone.now()
      lesson_progress.save()

    return progress
  
  @staticmethod
  def get_dashboard_data(user):
    """프론트엔드 대시보드용 데이터"""
    progress =ProgressService.get_or_create_user_progress(user)

    return {
      'user_info': {
        'nickname': user.nickname,
        'totalXP': user.exp,
        'hearts': user.hearts,
        'coins': user.coins,
        'subscriptionType': user.subscription_type,
      },
      'learning_stats': {
        'completedLessons': progress.total_lessons_completed,
        'solvedProblems': progress.total_problems_solved,
        'studyTimeMinutes': progress.total_study_time_minutes,
        'accuracyRate': progress.accuracy_rate,
      },
      'streak': {
        'currentStreak': progress.current_streak,
        'longestStreak': progress.longest_streak,
        'lastStudyDate': progress.last_study_date,
      },
      'weekly_goal': {
        'goalDays': progress.weekly_goal_days,
        'currentWeekDays': progress.current_week_days,
        'achieved': progress.current_week_days >= progress.weekly_goal_days,
        'percentage' : progress.get_weekly_progress_percentage(),
      }
    }