from django.contrib.auth.models import AbstractUser, BaseUserManager # 커스텀 유저 모델과 매니저를 위해 사용
from django.db import models # Django 모델 필드에 사용
import uuid # UUID 필드에 사용
from django.utils import timezone # 타임스탬프 필드에 사용
from datetime import timedelta # 구독 만료일 계산에 사용
from django.core.exceptions import ValidationError

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
        
        # nickname 자동 생성 (extra_fields에 없거나 빈 값인 경우)
        if 'nickname' not in extra_fields or not extra_fields.get('nickname'):
            base_nickname = email.split('@')[0]
            nickname = base_nickname
            counter = 1
            
            # 중복 방지
            while self.model.objects.filter(nickname=nickname).exists():
                nickname = f"{base_nickname}_{counter}"
                counter += 1
            
            # extra_fields에 설정
            extra_fields['nickname'] = nickname
        
        # User 객체 생성 (이제 extra_fields에 nickname이 확실히 포함됨)
        user = self.model(email=email, **extra_fields)

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
    # 커스텀 Manager 사용
    objects = UserManager()

    # username 필드 제거
    username = None

    # 기본 정보
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

    # 계정 상태
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='삭제 여부',
        help_text='소프트 삭제용'
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='삭제 시간'
    )

    # 타임스탬프
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # 충돌 방지
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        verbose_name='그룹'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        verbose_name='권한'
    )

    # email을 로그인 필드로 사용
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nickname']  # createsuperuser 시 추가로 입력받을 필드

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['nickname']),
            models.Index(fields=['is_deleted', 'created_at']),
        ]

    def __str__(self):
        return f"{self.nickname} ({self.email})"


    # ========== 게임 관련 메서드 ==========
    def add_exp(self, amount):
        """EXP 추가 및 레벨업 체크"""
        self.exp += amount
        new_level = int((self.exp / 100) ** 0.5) + 1

        if new_level > self.level:
            self.level = new_level
            return True  # 레벨업 발생

        self.save(update_fields=['exp'])
        return False
    
    def use_heart(self):
        """하트 사용"""
        if self.hearts > 0:
            self.hearts -= 1
            self.save(update_fields=['hearts'])
            return True
        return False
    
    def add_hearts(self, amount):
        """하트 추가"""
        self.hearts += amount
        self.save(update_fields=['hearts'])
    
    def add_coins(self, amount):
        """코인 추가"""
        self.coins += amount
        self.save(update_fields=['coins'])
    
    def use_coins(self, amount):
        """코인 사용"""
        if self.coins >= amount:
            self.coins -= amount
            self.save(update_fields=['coins'])
            return True
        return False

    # ========== 구독 관련 메서드 ==========
    def is_premium(self):
        """프리미엄 구독 여부"""
        if self.subscription_type == 'free':
            return False

        if self.subscription_expires_at and self.subscription_expires_at < timezone.now():
            return False

        return True
    
    def activate_subscription(self, subscription_type, duration_days):
        """구독 활성화"""
        self.subscription_type = subscription_type
        self.subscription_expires_at = timezone.now() + timedelta(days=duration_days)
        self.save(update_fields=['subscription_type', 'subscription_expires_at'])

    # ========== 학습 관련 메서드 ==========
    def update_streak(self):
        """연속 학습 일수 업데이트"""
        today = timezone.now().date()
        
        if not self.last_active_date:
            self.streak_days = 1
        elif self.last_active_date == today - timedelta(days=1):
            self.streak_days += 1
        elif self.last_active_date != today:
            self.streak_days = 1
        
        self.last_active_date = today
        self.save(update_fields=['streak_days', 'last_active_date'])

    # ========== 계정 관련 메서드 ==========
    def delete_account(self):
        """계정 삭제"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])

    def restore_account(self):
        """계정 복원"""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=['is_deleted', 'deleted_at', 'is_active'])

# SocialAccount 모델
class SocialAccount(models.Model):
    """
    소셜 로그인 계정 관리
    - User : SocialAccount = 1 : 1 (독립 계정)
    - 각 소셜 계정은 고유한 User를 가짐
    """

    PROVIDER_CHOICES = [
        ('google', 'Google'),
        ('kakao', 'Kakao'),
        ('naver', 'Naver'),
        ('apple', 'Apple'),
    ]

    # User 연결 (1:1 - 한 User가 하나의 소셜 계정만 가질 수 있음)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='social_account',
        verbose_name='사용자'
    )

    # 소셜 제공자 정보
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        verbose_name='소셜 제공자',
        db_index=True
    )
    social_id = models.CharField(
        max_length=255,
        verbose_name='소셜 ID',
        help_text='제공자에서 부여한 고유 ID',
        db_index=True
    )

    # 소셜 계정 정보
    social_email = models.EmailField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='소셜 이메일',
        help_text='소셜 계정의 원본 이메일'
    )
    social_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='소셜 이름'
    )

    # 토큰 정보 (선택적 저장)
    access_token = models.TextField(
        null=True,
        blank=True,
        verbose_name='Access Token'
    )
    refresh_token = models.TextField(
        null=True,
        blank=True,
        verbose_name='Refresh Token'
    )
    token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='토큰 만료 시간'
    )

    # 추가 정보
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='추가 데이터',
        help_text='제공자별 추가 정보 저장'
    )

    # 상태
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성 상태'
    )

    # 타임스탬프
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='연결 시간'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='수정 시간'
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 로그인'
    )

    class Meta:
        db_table = 'social_accounts'
        verbose_name = 'Social Account'
        verbose_name_plural = 'Social Accounts'
        # provider + social_id 조합은 유일
        unique_together = [['provider', 'social_id']]
        indexes = [
            models.Index(fields=['provider', 'social_id']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['social_email']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.provider} ({self.social_id})"
    
    def clean(self):
        """유효성 검사"""
        # 같은 provider + social_id는 하나만 존재해야 함
        if SocialAccount.objects.filter(
            provider=self.provider,
            social_id=self.social_id
        ).exclude(id=self.id).exists():
            raise ValidationError(
                f'{self.provider} 계정 {self.social_id}는 이미 존재합니다.'
            )
        

    # ========== 인스턴스 메서드 ==========
    def update_profile(self, name=None, email=None, profile_image=None, extra_data=None):
        """프로필 정보 업데이트"""
        updated = False
        
        if name and self.social_name != name:
            self.social_name = name
            updated = True
        
        if email and self.social_email != email:
            self.social_email = email
            updated = True
        
        if extra_data:
            self.extra_data.update(extra_data)
            updated = True
        
        if updated:
            self.save()
    
    def update_tokens(self, access_token=None, refresh_token=None, expires_in=None):
        """토큰 정보 업데이트"""
        if access_token:
            self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_in:
            self.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        self.save(update_fields=['access_token', 'refresh_token', 'token_expires_at'])
    
    def update_last_login(self):
        """마지막 로그인 시간 업데이트"""
        self.last_login_at = timezone.now()
        self.save(update_fields=['last_login_at'])
    
    def deactivate(self):
        """계정 비활성화"""
        self.is_active = False
        self.save(update_fields=['is_active'])
    
    def reactivate(self):
        """계정 재활성화"""
        self.is_active = True
        self.save(update_fields=['is_active'])

    
    # ========== 클래스 메서드 ==========
    @classmethod
    def find_or_create_user(cls, provider, social_id, **user_data):
        """
        소셜 계정으로 User 찾기 또는 생성
        - 독립적인 User 생성
        
        Args:
            provider: 'google', 'kakao', 'naver', 'apple'
            social_id: 소셜 제공자의 고유 ID
            **user_data: 사용자 정보
                - email: 이메일
                - nickname: 닉네임 (선택)
                - name: 이름
                - profile_image: 프로필 이미지 URL
                - extra_data: 추가 데이터 (dict)
        
        Returns:
            tuple: (user, created, social_account)
                - user: User 인스턴스
                - created: 신규 생성 여부
                - social_account: SocialAccount 인스턴스
        """
        try:
            # 1. 기존 소셜 계정 찾기 (provider + social_id로 검색)
            social_account = cls.objects.select_related('user').get(
                provider=provider,
                social_id=social_id,
                is_active=True
            )
            
            # 프로필 정보 업데이트
            social_account.update_profile(
                name=user_data.get('name'),
                email=user_data.get('email'),
                extra_data=user_data.get('extra_data')
            )
            
            # 마지막 로그인 업데이트
            social_account.update_last_login()
            
            return social_account.user, False, social_account
        
        except cls.DoesNotExist:
            
            # 2. 동일한 이메일을 가진 기존 User가 있는지 확인
            email = user_data.get('email')
            nickname = user_data.get('nickname')
            
            # 이메일 기반 닉네임 생성
            if not nickname:
                nickname = email.split('@')[0] if email else f"{provider}_user"
            
            user = None
            is_new_user = False
            
            try:
                # 2-1. 이메일로 기존 User 찾기
                user = User.objects.get(email=email)
                is_new_user = False
                
            except User.DoesNotExist:
                # 2-2. 기존 User가 없으면 새로 생성
                user = User.objects.create_user(
                    email=email,
                    password=None,  # OAuth 사용자는 비밀번호 없음
                    nickname=nickname,
                )
                is_new_user = True
            
            # 3. SocialAccount 생성 (기존 유저든 신규 유저든 소셜 계정 연결)
            try:
                social_account = cls.objects.create(
                    user=user,
                    provider=provider,
                    social_id=social_id,
                    social_email=user_data.get('email'),
                    social_name=user_data.get('name'),
                    extra_data=user_data.get('extra_data', {}),
                    last_login_at=timezone.now()
                )
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise
            
            return user, is_new_user, social_account
    
    @classmethod
    def find_user_by_social(cls, provider, social_id):
        """
        소셜 계정으로 사용자 찾기
        
        Returns:
            User 인스턴스 또는 None
        """
        try:
            social_account = cls.objects.select_related('user').get(
                provider=provider,
                social_id=social_id,
                is_active=True
            )
            return social_account.user
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_by_provider_and_user(cls, provider, user):
        """특정 제공자의 사용자 소셜 계정 조회"""
        try:
            return cls.objects.get(
                provider=provider,
                user=user,
                is_active=True
            )
        except cls.DoesNotExist:
            return None

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