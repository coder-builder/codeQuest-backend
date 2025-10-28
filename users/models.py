from django.contrib.auth.models import AbstractUser, BaseUserManager # 커스텀 유저 모델과 매니저를 위해 사용
from django.db import models # Django 모델 필드에 사용
import uuid # UUID 필드에 사용
from django.utils import timezone # 타임스탬프 필드에 사용
from datetime import timedelta # 구독 만료일 계산에 사용
import secrets # 임시 비밀번호 생성에 사용

class UserManager(BaseUserManager):
    """
    커스텀 UserManager
    username 대신 email을 사용하도록 설정하기 위함
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        일반 사용자 생성
        OAuth 로그인의 경우 password=None 가능
        """
        if not email:
            raise ValueError('이메일은 필수입니다')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if 'nickname' not in extra_fields or not extra_fields['nickname']:
            # nickname이 없으면 이메일의 앞부분을 사용
            user.nickname = email.split('@')[0]
        else:
            user.nickname = extra_fields['nickname']

        if password:
            user.set_password(password)  # 비밀번호 해싱
        else:
            # OAuth 사용자는 비밀번호 없이 생성 가능
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """관리자 생성"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        # nickname이 없으면 이메일의 앞부분을 사용
        if 'nickname' not in extra_fields or not extra_fields['nickname']:
            extra_fields['nickname'] = email.split('@')[0]

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    CodeQuest 사용자 모델
    """
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    nickname = models.CharField(max_length=50, unique=True)
    profile_image_url = models.TextField(blank=True, null=True)

    # 게임 시스템
    level = models.IntegerField(default=1)
    exp = models.IntegerField(default=0)
    hearts = models.IntegerField(default=5)
    coins = models.IntegerField(default=0)

    # 구독 정보
    SUBSCRIPTION_CHOICES = [
        ('free', 'Free'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('premium', 'Premium'),
    ]
    subscription_type = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default='free'
    )
    subscription_expires_at = models.DateTimeField(blank=True, null=True)

    # 학습 정보
    daily_goal_minutes = models.IntegerField(default=30)
    streak_days = models.IntegerField(default=0)
    last_active_date = models.DateField(blank=True, null=True)

    # 타임스탬프
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # username 필드 제거
    username = None

    # email을 로그인 필드로 사용
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']  # createsuperuser 시 추가로 입력받을 필드

    # 커스텀 Manager 사용
    objects = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nickname} ({self.email})"

    def add_exp(self, amount):
        """EXP 추가 및 레벨업 체크"""
        self.exp += amount
        new_level = int((self.exp / 100) ** 0.5) + 1

        if new_level > self.level:
            self.level = new_level
            return True  # 레벨업 발생

        return False

    def is_premium(self):
        """프리미엄 구독 여부"""
        if self.subscription_type == 'free':
            return False

        if self.subscription_expires_at and self.subscription_expires_at < timezone.now():
            return False

        return True

# JWT Refresh Token 관리 모델
class CustomRefreshToken(models.Model):
    """
    JWT Refresh Token 관리 모델
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='refresh_tokens'
    )
    refresh_token = models.TextField(unique=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True) # 토큰 활성 상태

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    device_id = models.CharField(max_length=255, null=True, blank=True)
    device_name = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True) # 사용자 에이전트 정보
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'refresh_tokens'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['refresh_token']),
            models.Index(fields=['expires_at']),
        ]

    def __str__(self):
        return f"RefreshToken(user={self.user.email}, expires_at={self.expires_at}, is_active={self.is_active})"

    # 기본 메서드
    def is_valid(self):
        """토큰 유효성 검사"""
        return self.is_active and self.expires_at > timezone.now()

    def deactivate(self):
        """토큰 비활성화"""
        self.is_active = False
        self.save(update_fields=['is_active'])

    def update_last_used(self):
        """마지막 사용 시간 업데이트"""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])


    #### 토큰 생성 ####
    @classmethod  # 어노테이션 : 클래스 메서드임을 나타냄
    def create_for_user(cls, user, refresh_token_string, request=None, **kwargs):
        """토큰 생성 - 로테이션 포함"""
        device_id = kwargs.get('device_id')

        # 같은 디바이스의 기존 토큰들 무효화 (로테이션)
        if device_id:
            cls.objects.filter(
                user=user,
                device_id=device_id,
                is_active=True
            ).update(is_active=False)


        # 디바이스 제한: 최대 5개
        active_devices = cls.objects.filter(
            user=user,
            is_active=True
        ).values('device_id').distinct().count()

        if device_id and active_devices >= 5:
            # 가장 오래 사용하지 않은 디바이스 토큰 무효화
            oldest_token = cls.objects.filter(
                user=user,
                is_active=True
            ).exclude(device_id=device_id).order_by('last_used_at').first()

            if oldest_token:
                oldest_token.deactivate()

        # 최종적으로 새 토큰 생성
        return cls.objects.create(
            user=user,
            refresh_token=refresh_token_string,
            device_id=device_id,
            device_name=kwargs.get('device_name'),
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent'),
            expires_at=timezone.now() + timedelta(days=7),  # 7일 후 만료
        )

    # 디바이스 및 토큰 관리
    @classmethod
    def cleanup_expired_tokens(cls, days_old=30):
        """오래된 만료된 토큰 정리"""
        cutoff_data = timezone.now() - timedelta(days=days_old)
        expired_tokens = cls.objects.filter(
            models.Q(expires_at__lt=timezone.now()) & # 만료된 토큰
            models.Q(is_active=False, created_at=cutoff_data) # 비활성화된지 오래된 토큰
        )
        count = expired_tokens.count()
        expired_tokens.delete()
        return count


    @classmethod
    def revoke_device_tokens(cls, user, device_id):
        """특정 디바이스의 모든 토큰 무효화"""
        return cls.objects.filter(
            user=user,
            device_id=device_id,
            is_active=True
        ).update(is_active=False)

    @classmethod
    def revoke_user_all_logout(cls, user, except_token=None):
        """사용자의 모든 토큰 무효화 (로그아웃 시)"""
        tokens_user = cls.objects.filter(
            user=user,
            is_active=True
        )
        if except_token:
            tokens_user = tokens_user.exclude(user_id=except_token.user_id)

        return tokens_user.update(is_active=False)

    @classmethod
    def get_user_active_sessions(cls, user):
        """사용자의 활성화된 세션(디바이스) 조회"""
        return cls.objects.filter(
            user=user,
            is_active=True
        ).values(
            'device_id',
            'device_name',
            'ip_address',
            'user_agent',
            'last_used_at',
            'expires_at'
        ).order_by('-last_used_at')

    # 의심스러운 활동 감지
    # Todo : 코드 점검 및 수정 필요.
    # @classmethod
    # def detect_suspicious_activity(cls, user, ip_address=None, user_agent=None):
    #     """의심스러운 활동 감지"""
    #     suspicious_patterns = []

    #     # 최근 24시간 내 활동 조회
    #     recent_tokens = cls.objects.filter(
    #         user=user,
    #         created_at__gte=timezone.now() - timedelta(hours=24)
    #     )

    #     # 너무 많은 서로 다른 IP에서의 접근
    #     if ip_address:
    #         recent_ips = recent_tokens.values('ip_address').distinct().count()
    #         if recent_ips > 5:
    #             suspicious_patterns.append('다양한 IP에서의 접근 감지')

    #     # 새로운 브라우저/디바이스에서의 접근
    #     if user_agent:
    #         known_agents = cls.objects.filter(
    #             user=user,
    #             is_active=True
    #         ).values_list('user_agent', flat=True)

    #         if user_agent not in known_agents:
    #             suspicious_patterns.append('새로운 브라우저/디바이스에서의 접근 감지')

    #     return suspicious_patterns