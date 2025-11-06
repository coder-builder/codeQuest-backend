# problems/models.py

from django.db import models
from django.utils import timezone
from worlds.models import Stage


class Lesson(models.Model):
    """레슨 (4-5개 문제로 구성)"""
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name="스테이지"
    )
    title = models.CharField(
        max_length=200,
        verbose_name="레슨 제목"
    )
    description = models.TextField(
        blank=True,
        verbose_name="레슨 설명"
    )
    order = models.IntegerField(verbose_name="순서")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        ordering = ['stage__world__title', 'stage__order', 'order']
        verbose_name = "레슨"
        verbose_name_plural = "레슨 목록"
        unique_together = (('stage', 'order'),)

    def __str__(self):
        return f"{self.stage.title} - Lesson {self.order}: {self.title}"

    def get_status_for_user(self, user):
        """
        사용자에게 이 레슨의 상태 반환

        Returns:
            'locked': 잠김 (이전 레슨 미완료)
            'available': 시작 가능
            'in_progress': 진행 중
            'completed': 완료 (복습 가능)
        """
        # 1. 이전 레슨 완료 확인
        if not self.is_unlocked_for_user(user):
            return 'locked'

        # 2. 진행 상황 확인
        try:
            progress = UserLessonProgress.objects.get(
                user=user,
                lesson=self
            )

            # 완료됨
            if progress.is_completed:
                return 'completed'

            # 진행 중
            if progress.is_in_progress:
                return 'in_progress'

            # 시작 가능 (기록은 있지만 진행 안 함)
            return 'available'

        except UserLessonProgress.DoesNotExist:
            # 기록 없음 = 시작 가능
            return 'available'

    def is_unlocked_for_user(self, user):
        """이전 레슨 완료 확인"""
        # 첫 번째 레슨은 항상 열림
        if self.order == 1:
            return True

        # 이전 레슨 가져오기
        prev_lesson = Lesson.objects.filter(
            stage=self.stage,
            order=self.order - 1
        ).first()

        if not prev_lesson:
            return True

        # 이전 레슨 완료 여부 확인
        try:
            progress = UserLessonProgress.objects.get(
                user=user,
                lesson=prev_lesson
            )
            return progress.is_completed
        except UserLessonProgress.DoesNotExist:
            return False

    def can_restart(self, user):
        """
        레슨을 다시 시작할 수 있는지 확인
        (완료한 레슨만 복습 가능)
        """
        try:
            progress = UserLessonProgress.objects.get(
                user=user,
                lesson=self
            )
            return progress.is_completed
        except UserLessonProgress.DoesNotExist:
            return False

    def get_progress_info(self, user):
        """레슨 진행 정보 반환"""
        status = self.get_status_for_user(user)

        result = {
            'lesson_id': self.id,
            'title': self.title,
            'description': self.description,
            'order': self.order,
            'status': status,
            'is_locked': status == 'locked',
            'can_start': status in ['available', 'completed'],
            'can_continue': status == 'in_progress',
            'can_restart': status == 'completed',
        }

        # 진행 중이거나 완료된 경우 상세 정보 추가
        if status in ['in_progress', 'completed']:
            try:
                progress = UserLessonProgress.objects.get(
                    user=user,
                    lesson=self
                )
                result.update({
                    'current_round': progress.current_round,
                    'completed_problems': progress.completed_problems_count,
                    'total_problems': progress.total_problems,
                    'progress_percentage': int(
                        (progress.completed_problems_count / progress.total_problems * 100)
                        if progress.total_problems > 0 else 0
                    ),
                    'started_at': progress.started_at,
                    'completed_at': progress.completed_at if status == 'completed' else None,
                    'abandon_count': progress.abandon_count,
                })
            except UserLessonProgress.DoesNotExist:
                pass

        return result


class Problem(models.Model):
    """문제"""
    DIFFICULTY_CHOICES = [
        ('easy', '쉬움'),
        ('medium', '보통'),
        ('hard', '어려움'),
    ]

    PROBLEM_TYPE_CHOICES = [
        ('multiple_choice', '객관식'),
        ('word_bank', '단어 선택'),
        ('arrange_blocks', '블록 순서 배열'),
        ('matching', '연결하기'),
        ('copy_code', '코드 따라쓰기'),
        ('coding', '코딩 문제'),
        ('fill_code', '코드 빈칸 채우기'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='problems',
        verbose_name="레슨"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="문제 제목"
    )
    description = models.TextField(
        verbose_name="문제 설명"
    )

    problem_type = models.CharField(
        max_length=20,
        choices=PROBLEM_TYPE_CHOICES,
        default='coding',
        verbose_name="문제 타입"
    )

    # 문제 데이터 (JSON)
    problem_data = models.JSONField(
        default=dict,
        verbose_name="문제 데이터",
        help_text="""
        문제 타입별 데이터 구조:

        1. multiple_choice (객관식):
        {
            "question": "Python의 주석 기호는?",
            "choices": ["//", "#", "/*", "<!--"],
            "correct_answer": "#"
        }

        2. word_bank (단어 선택):
        {
            "template": "for i ___ range(___): print(i)",
            "blanks": [
                {"index": 0, "options": ["in", "at"], "correct": "in"},
                {"index": 1, "options": ["3", "5"], "correct": "5"}
            ]
        }

        3. arrange_blocks (블록 순서 배열):
        {
            "blocks": ["x = 10", "y = 20", "result = x + y", "print(result)"],
            "dependencies": [[0, 2], [1, 2], [2, 3]]
        }

        4. matching (연결하기):
        {
            "left_items": ["print()", "input()"],
            "right_items": ["출력", "입력"],
            "correct_pairs": {"print()": "출력", "input()": "입력"}
        }

        5. copy_code (코드 따라쓰기):
        {
            "code_to_copy": "for i in range(5):\\n    print(i)",
            "case_sensitive": true,
            "whitespace_sensitive": true
        }
        """
    )

    # 정답 (간단한 문제용)
    correct_answer = models.TextField(
        blank=True,
        verbose_name="정답"
    )

    # 정답 해설
    correct_explanation = models.TextField(
        blank=True,
        verbose_name="정답 해설"
    )

    # 오답 시 단계별 힌트
    first_hint = models.TextField(
        blank=True,
        verbose_name="1차 힌트",
        help_text="첫 번째 오답 시"
    )
    second_hint = models.TextField(
        blank=True,
        verbose_name="2차 힌트",
        help_text="두 번째 오답 시"
    )
    third_hint = models.TextField(
        blank=True,
        verbose_name="3차 힌트",
        help_text="세 번째 오답 시"
    )

    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy',
        verbose_name="난이도"
    )

    is_boss_problem = models.BooleanField(
        default=False,
        verbose_name="보스 문제"
    )

    order = models.IntegerField(verbose_name="순서")

    # 코딩 문제용
    initial_code = models.TextField(
        blank=True,
        verbose_name="초기 코드"
    )
    solution_code = models.TextField(
        blank=True,
        verbose_name="정답 코드"
    )

    time_limit = models.IntegerField(
        default=2,
        verbose_name="시간 제한(초)"
    )
    memory_limit = models.IntegerField(
        default=128,
        verbose_name="메모리 제한(MB)"
    )

    # 보상
    exp_reward = models.IntegerField(
        default=10,
        verbose_name="EXP 보상"
    )
    coin_reward = models.IntegerField(
        default=5,
        verbose_name="코인 보상"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['lesson__stage__order', 'lesson__order', 'order']
        verbose_name = "문제"
        verbose_name_plural = "문제 목록"
        unique_together = (('lesson', 'order'),)

    def __str__(self):
        type_icons = {
            'multiple_choice': '📝',
            'word_bank': '🔤',
            'arrange_blocks': '🧩',
            'matching': '🔗',
            'copy_code': '✍️',
            'coding': '💻',
            'fill_code': '📋'
        }
        icon = type_icons.get(self.problem_type, '❓')
        boss = " 👑" if self.is_boss_problem else ""
        return f"{icon} {self.lesson.title} - {self.order}. {self.title}{boss}"

    def needs_judge0(self):
        """Judge0 실행 필요 여부"""
        return self.problem_type in ['coding', 'fill_code']

    def is_trial_problem(self):
        """트라이얼 방식 (틀려도 다음으로)"""
        return self.problem_type in ['multiple_choice', 'word_bank', 'matching']

    def is_immediate_retry(self):
        """즉시 재시도 (맞을 때까지)"""
        return self.problem_type in ['arrange_blocks', 'copy_code', 'coding', 'fill_code']


class TestCase(models.Model):
    """테스트 케이스 (코딩 문제용)"""
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name='test_cases',
        verbose_name="문제"
    )

    input_data = models.TextField(
        blank=True,
        verbose_name="입력 데이터",
        help_text="표준 입력(stdin)으로 들어갈 데이터"
    )
    expected_output = models.TextField(
        verbose_name="예상 출력",
        help_text="정답으로 나와야 하는 출력"
    )

    is_hidden = models.BooleanField(
        default=False,
        verbose_name="숨겨진 테스트"
    )

    order = models.IntegerField(verbose_name="순서")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['problem', 'order']
        verbose_name = "테스트 케이스"
        verbose_name_plural = "테스트 케이스 목록"

    def __str__(self):
        hidden = " [숨김]" if self.is_hidden else ""
        return f"{self.problem.title} - 테스트 {self.order}{hidden}"


class UserLessonProgress(models.Model):
    """사용자의 레슨 진행 상황"""
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        verbose_name="레슨"
    )

    # 완료 여부
    is_completed = models.BooleanField(
        default=False,
        verbose_name="완료 여부"
    )

    # 진행 중 여부
    is_in_progress = models.BooleanField(
        default=False,
        verbose_name="진행 중"
    )

    # 중도 이탈 추적
    abandon_count = models.IntegerField(
        default=0,
        verbose_name="중도 이탈 횟수"
    )
    last_abandon_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="마지막 이탈 시간"
    )

    # 현재 라운드 정보
    current_round = models.IntegerField(
        default=1,
        verbose_name="현재 라운드",
        help_text="1라운드: 모든 문제, 2라운드+: 틀린 문제만"
    )

    current_problem_index = models.IntegerField(
        default=0,
        verbose_name="현재 문제 인덱스"
    )

    # 문제 목록 관리
    current_round_problems = models.JSONField(
        default=list,
        verbose_name="현재 라운드 문제 ID 목록"
    )

    failed_problems_this_round = models.JSONField(
        default=list,
        verbose_name="이번 라운드 틀린 문제 ID"
    )

    # 완료한 문제
    completed_problem_ids = models.JSONField(
        default=list,
        verbose_name="완료한 문제 ID"
    )

    # 전체 진행률
    total_problems = models.IntegerField(
        default=0,
        verbose_name="총 문제 수"
    )

    completed_problems_count = models.IntegerField(
        default=0,
        verbose_name="완료한 문제 수"
    )

    # 시간
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="시작 시간"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="완료 시간"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user', 'lesson'),)
        verbose_name = "레슨 진행 상황"
        verbose_name_plural = "레슨 진행 상황 목록"

    def __str__(self):
        if self.is_completed:
            status = "완료 ✅"
        elif self.is_in_progress:
            status = f"진행중 R{self.current_round} ({self.completed_problems_count}/{self.total_problems})"
        else:
            status = "미시작"
        return f"{self.user.username} - {self.lesson.title} [{status}]"

    def initialize_round_one(self):
        """1라운드 초기화 (모든 문제)"""
        all_problems = list(
            self.lesson.problems.all()
            .order_by('order')
            .values_list('id', flat=True)
        )
        self.current_round = 1
        self.current_problem_index = 0
        self.current_round_problems = all_problems
        self.failed_problems_this_round = []
        self.completed_problem_ids = []
        self.completed_problems_count = 0
        self.total_problems = len(all_problems)
        self.is_in_progress = True
        self.save()

    def reset_progress(self):
        """진행 상황 초기화 (중도 이탈 시)"""
        self.current_round = 1
        self.current_problem_index = 0
        self.failed_problems_this_round = []
        self.completed_problem_ids = []
        self.completed_problems_count = 0
        self.is_in_progress = False
        self.abandon_count += 1
        self.last_abandon_at = timezone.now()
        self.save()

    def start_next_round(self):
        """다음 라운드 시작 (틀린 문제만)"""
        if not self.failed_problems_this_round:
            return False

        self.current_round += 1
        self.current_problem_index = 0
        self.current_round_problems = self.failed_problems_this_round.copy()
        self.failed_problems_this_round = []
        self.save()
        return True

    def get_current_problem(self):
        """현재 풀어야 할 문제 가져오기"""
        if self.current_problem_index >= len(self.current_round_problems):
            return None

        problem_id = self.current_round_problems[self.current_problem_index]
        return Problem.objects.get(id=problem_id)

    def move_to_next_problem(self):
        """다음 문제로 이동"""
        self.current_problem_index += 1
        self.save()

        if self.current_problem_index >= len(self.current_round_problems):
            return 'round_complete'
        return 'next_problem'

    def mark_problem_failed(self, problem_id):
        """문제 틀림 처리 (트라이얼 문제용)"""
        if problem_id not in self.failed_problems_this_round:
            self.failed_problems_this_round.append(problem_id)
            self.save()

    def mark_problem_completed(self, problem_id):
        """문제 완료 처리"""
        if problem_id not in self.completed_problem_ids:
            self.completed_problem_ids.append(problem_id)
            self.completed_problems_count += 1
            self.save()


class ProblemAttempt(models.Model):
    """문제 시도 기록"""
    FAILED_STATUS_CHOICES = [
        ('not_failed', '실패 안 함'),
        ('failed_once', '1차 실패'),
        ('failed_twice', '2차 실패'),
        ('failed_three_times', '3차 이상 실패'),
        ('forced_pass', '강제 통과'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        verbose_name="문제"
    )

    # 시도 횟수
    attempt_count = models.IntegerField(
        default=0,
        verbose_name="시도 횟수"
    )

    # 실패 상태 (복습용)
    failed_status = models.CharField(
        max_length=20,
        choices=FAILED_STATUS_CHOICES,
        default='not_failed',
        verbose_name="실패 상태"
    )

    # 마지막 제출 내용
    last_code = models.TextField(
        blank=True,
        verbose_name="마지막 제출 코드/답안"
    )

    # 해결 여부
    is_solved = models.BooleanField(
        default=False,
        verbose_name="해결 여부"
    )

    is_forced_pass = models.BooleanField(
        default=False,
        verbose_name="강제 통과"
    )

    # 시간 기록
    first_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="첫 시도"
    )
    solved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="해결 시간"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user', 'problem'),)
        verbose_name = "문제 시도 기록"
        verbose_name_plural = "문제 시도 기록 목록"

    def __str__(self):
        if self.is_solved:
            status = "✅"
        elif self.is_forced_pass:
            status = "⏭️"
        else:
            status = f"❌ {self.attempt_count}회"
        return f"{status} {self.user.username} - {self.problem.title}"


class UserReviewList(models.Model):
    """사용자 복습 리스트"""
    REVIEW_CATEGORY_CHOICES = [
        ('failed_once', '1차 틀린 문제'),
        ('failed_twice', '2차 틀린 문제'),
        ('failed_three_times', '3차 이상 틀린 문제'),
        ('forced_pass', '강제 통과한 문제'),
    ]

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        verbose_name="문제"
    )

    category = models.CharField(
        max_length=20,
        choices=REVIEW_CATEGORY_CHOICES,
        verbose_name="복습 카테고리"
    )

    # 복습 완료 여부
    is_reviewed = models.BooleanField(
        default=False,
        verbose_name="복습 완료"
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="복습 완료 시간"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('user', 'problem', 'category'),)
        verbose_name = "복습 리스트"
        verbose_name_plural = "복습 리스트 목록"

    def __str__(self):
        status = "✅" if self.is_reviewed else "📚"
        return f"{status} {self.user.username} - {self.problem.title} ({self.get_category_display()})"