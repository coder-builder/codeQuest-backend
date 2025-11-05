# worlds/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone


class World(models.Model):
    """월드 (코딩 언어)"""
    title = models.CharField(
        max_length=100,
        verbose_name="코딩 언어 월드",
        help_text="예: Python, Java, Javascript"
    )
    description = models.TextField(verbose_name="월드 설명")
    icon = models.CharField(
        max_length=50,
        verbose_name="아이콘",
        help_text="이모지"
    )
    is_locked = models.BooleanField(
        default=True,
        verbose_name="잠금 여부"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        ordering = ['title']  # ✅ 수정
        verbose_name = "코딩 언어"
        verbose_name_plural = "코딩 언어 목록"

    def __str__(self):
        return f"{self.title} {self.icon}"


class UserWorld(models.Model):
    """사용자별 언어 공부 테이블"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_worlds",
        verbose_name="사용자"
    )
    world = models.ForeignKey(
        World,
        on_delete=models.CASCADE,
        related_name="user_progresses",
        verbose_name="월드"
    )

    is_unlocked = models.BooleanField(
        default=False,
        verbose_name="잠금 해제 여부"
    )
    completed_stage = models.IntegerField(
        default=0,
        verbose_name="완료한 스테이지 수"
    )

    last_studied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="마지막 공부 시간",
        help_text="레슨을 풀었을때만 업데이트"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="시작 시간"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정 시간"
    )

    class Meta:
        ordering = ['-last_studied_at', '-created_at']
        unique_together = (('user', 'world'),)
        verbose_name = "사용자 코딩 언어 월드"
        verbose_name_plural = "사용자 월드 진행 사항 목록"

    def __str__(self):
        return f"{self.user.username} - {self.world.title}"  # ✅ 수정

    @property
    def total_stage(self):
        """월드 내 총 스테이지 수"""
        return self.world.stages.count()

    @property
    def progress_percentage(self):
        """진행률 퍼센트"""
        if self.total_stage == 0:
            return 0
        return int((self.completed_stage / self.total_stage) * 100)

    @property
    def started_at(self):
        """시작 시간 (created_at 별칭)"""
        return self.created_at

    def update_progress(self):
        """진행률 업데이트"""
        self.completed_stage = UserStageProgress.objects.filter(  # ✅ 수정
            user=self.user,
            stage__world=self.world,
            is_completed=True
        ).count()
        self.save(update_fields=['completed_stage'])

    def touch(self):
        """마지막 공부 시간 업데이트"""
        self.last_studied_at = timezone.now()  # ✅ 수정
        self.save(update_fields=['last_studied_at'])


class Stage(models.Model):
    """스테이지"""
    world = models.ForeignKey(
        World,
        on_delete=models.CASCADE,
        related_name="stages",
        verbose_name="월드"
    )
    title = models.CharField(
        max_length=100,
        verbose_name="스테이지 제목"
    )
    description = models.TextField(
        blank=True,
        verbose_name="스테이지 설명"
    )
    order = models.IntegerField(verbose_name="순서")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        ordering = ['order']
        verbose_name = "스테이지"
        verbose_name_plural = "스테이지 목록"
        unique_together = (('world', 'order'),)

    def __str__(self):
        return f"{self.world.title} - Stage {self.order}: {self.title}"

    def is_unlocked_for_user(self, user):
        """이전 스테이지 완료 확인"""
        # 첫 번째 스테이지는 항상 열림
        if self.order == 1:
            return True

        # 이전 스테이지 가져오기
        prev_stage = Stage.objects.filter(
            world=self.world,
            order=self.order - 1,
        ).first()

        # 이전 스테이지가 없으면 열림 (안전장치)
        if not prev_stage:  # ✅ 수정
            return True

        # 이전 스테이지 완료 여부 확인
        try:
            progress = UserStageProgress.objects.get(
                user=user,
                stage=prev_stage,
            )
            return progress.is_completed
        except UserStageProgress.DoesNotExist:
            return False


class UserStageProgress(models.Model):
    """사용자의 스테이지 진행 상황"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    stage = models.ForeignKey(
        Stage,
        on_delete=models.CASCADE,
        verbose_name="스테이지"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="완료여부"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="완료 일시"
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정시간")  # ✅ 수정

    class Meta:
        unique_together = (('user', 'stage'),)
        verbose_name = "스테이지 진행 상황"
        verbose_name_plural = "스테이지 진행상황 목록"

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{status} {self.user.username} - {self.stage.title}"  # ✅ 수정