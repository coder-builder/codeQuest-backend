from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services import ProgressService
from rest_framework import status

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
  """사용자 대시보드 데이터"""
  user_id = str(request.user.id)
  data = ProgressService.get_dashboard_data(user_id)
  return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson(request):
  """레슨 완료 기록"""
  try:
    user = request.user
    data = request.data

    # 레슨 완료 기록
    progress = ProgressService.record_lesson_completion(
      user=user,
      world_name=data.get('world_name'),
      stage_number=data.get('stage_number'),
      lesson_number=data.get('lesson_number'),
      problems_solved=data.get('problems_solved', 0),
      exp_earned=data.get('exp_earned', 0),
      study_time_minutes=data.get('study_time_minutes', 0),
      correct_answers=data.get('correct_answers', 0),
      total_attempts=data.get('total_attempts', 0),
    )

    return Response({
      'success': True,
      'message': '레슨 완료가 기록되었습니다.',
      'result': {
        'streak' : progress.current_streak,
        'totalEXP' : progress.total_exp_earned,
        'weeklyProgress' : progress.get_weekly_progress_percentage(),
      }
    }, status=status.HTTP_200_OK)

  except KeyError as e:
    return Response({
      'success': False,
      'message': f'필수 필드 누락: {str(e)}'
    }, status=status.HTTP_400_BAD_REQUEST)

  except Exception as e:
    return Response({
      'success': False,
      'message': f'레슨 완료 기록 중 오류 발생: {str(e)}'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)