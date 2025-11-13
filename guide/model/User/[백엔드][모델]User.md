# Users Models 문서

CodeQuest 프로젝트의 사용자 관련 모델들에 대한 상세 가이드입니다.

---

## 목차
1. [UserManager](#usermanager)
2. [User 모델](#user-모델)
3. [SocialAccount 모델](#socialaccount-모델)
4. [CustomRefreshToken 모델](#customrefreshtoken-모델)

---

## UserManager

**위치**: `users/models.py:8-64`

### 개요
Django의 `BaseUserManager`를 상속받은 커스텀 사용자 관리자입니다. 기본 `username` 대신 `email`을 사용자 식별자로 사용하도록 구현되었습니다.

### 메서드

#### `create_user(email, password=None, **extra_fields)`
일반 사용자를 생성하는 메서드입니다.

**파라미터**:
- `email` (필수): 사용자 이메일 (로그인 ID로 사용)
- `password` (선택): 비밀번호. OAuth 로그인의 경우 `None` 가능
- `**extra_fields`: 추가 필드 (nickname, profile_image_url 등)

**동작**:
1. 이메일 필수 검증
2. 이메일 정규화 (소문자 변환 등)
3. nickname 자동 생성
   - extra_fields에 nickname이 없으면 이메일의 `@` 앞부분을 사용
   - 중복 시 `nickname_1`, `nickname_2` 형태로 자동 증가
4. 비밀번호가 있으면 해싱, 없으면 사용 불가능한 비밀번호로 설정

**사용 예시**:
```python
# 일반 회원가입
user = User.objects.create_user(
    email='user@example.com',
    password='secure_password123',
    nickname='myNickname'  # 선택사항
)

# OAuth 로그인
user = User.objects.create_user(
    email='oauth@example.com',
    password=None  # 비밀번호 없음
)
```

#### `create_superuser(email, password=None, **extra_fields)`
관리자(슈퍼유저)를 생성하는 메서드입니다.

**파라미터**:
- `email` (필수): 관리자 이메일
- `password` (선택): 비밀번호
- `**extra_fields`: 추가 필드

**동작**:
- `is_staff=True`, `is_superuser=True`, `is_active=True` 자동 설정
- nickname 없으면 이메일 앞부분을 자동 사용

**사용 예시**:
```python
# 커맨드라인에서
python manage.py createsuperuser

# 코드에서
admin = User.objects.create_superuser(
    email='admin@codequest.com',
    password='admin_password',
    nickname='AdminUser'
)
```

---

## User 모델

**위치**: `users/models.py:67-239`

### 개요
CodeQuest의 메인 사용자 모델입니다. Django의 `AbstractUser`를 상속받아 확장했으며, 게임 시스템, 구독 관리, 학습 추적 기능을 포함합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 | 기본값 | 특징 |
|--------|------|------|--------|------|
| `user_id` | UUIDField | 사용자 고유 ID (PK) | 자동생성 UUID | 편집 불가 |
| `email` | EmailField | 이메일 (로그인 ID) | - | 유니크, 최대 255자 |
| `nickname` | CharField | 닉네임 | 자동생성 | 유니크, 최대 50자 |
| `profile_image_url` | TextField | 프로필 이미지 URL | null | 선택사항 |

**참고**: `username` 필드는 사용하지 않습니다 (None으로 설정됨).

#### 게임 시스템
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `exp` | IntegerField | 경험치 | 0 |
| `hearts` | IntegerField | 하트 (생명) | 5 |
| `coins` | IntegerField | 코인 (재화) | 0 |

#### 구독 정보
| 필드명 | 타입 | 설명 | 기본값 | 선택지 |
|--------|------|------|--------|--------|
| `subscription_type` | CharField | 구독 타입 | 'free' | 'free', 'monthly', 'yearly', 'premium' |
| `subscription_expires_at` | DateTimeField | 구독 만료일 | null | 선택사항 |

#### 학습 정보
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `daily_goal_minutes` | IntegerField | 일일 목표 학습 시간(분) | 30 |
| `streak_days` | IntegerField | 연속 학습 일수 | 0 |
| `last_active_date` | DateField | 마지막 활동 날짜 | null |

#### 계정 상태
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `is_deleted` | BooleanField | 소프트 삭제 여부 | False |
| `deleted_at` | DateTimeField | 삭제 시간 | null |
| `is_active` | BooleanField | 활성 상태 (AbstractUser 상속) | True |

#### 타임스탬프
| 필드명 | 타입 | 설명 | 자동 갱신 |
|--------|------|------|----------|
| `created_at` | DateTimeField | 생성 시간 | ❌ |
| `updated_at` | DateTimeField | 수정 시간 | ✅ |

### 메서드

#### 게임 관련 메서드

##### `add_exp(amount)`
경험치를 추가하고 레벨업을 체크합니다.

**파라미터**:
- `amount` (int): 추가할 경험치

**반환값**:
- `True`: 레벨업 발생
- `False`: 레벨업 없음

**레벨 계산 공식**: `level = int((exp / 100) ** 0.5) + 1`

**사용 예시**:
```python
user = User.objects.get(email='user@example.com')
leveled_up = user.add_exp(50)
if leveled_up:
    print(f'축하합니다! 레벨 {user.level}이 되었습니다!')
```

**참고**: 코드에서 `self.level`을 참조하지만, User 모델에 `level` 필드가 정의되어 있지 않습니다. 이는 버그일 가능성이 있습니다.

##### `use_heart()`
하트를 1개 사용합니다.

**반환값**:
- `True`: 하트 사용 성공
- `False`: 하트가 부족하여 실패

**사용 예시**:
```python
if user.use_heart():
    print('문제 도전 시작!')
else:
    print('하트가 부족합니다.')
```

##### `add_hearts(amount)`
하트를 추가합니다.

**파라미터**:
- `amount` (int): 추가할 하트 수

**사용 예시**:
```python
user.add_hearts(3)  # 하트 3개 추가
```

##### `add_coins(amount)`
코인을 추가합니다.

**파라미터**:
- `amount` (int): 추가할 코인

**사용 예시**:
```python
user.add_coins(100)  # 100코인 추가
```

##### `use_coins(amount)`
코인을 사용합니다.

**파라미터**:
- `amount` (int): 사용할 코인

**반환값**:
- `True`: 코인 사용 성공
- `False`: 코인이 부족하여 실패

**사용 예시**:
```python
if user.use_coins(50):
    print('아이템 구매 완료!')
else:
    print('코인이 부족합니다.')
```

#### 구독 관련 메서드

##### `is_premium()`
사용자가 프리미엄 구독 중인지 확인합니다.

**반환값**:
- `True`: 프리미엄 구독 활성
- `False`: 무료 사용자 또는 구독 만료

**체크 로직**:
1. `subscription_type`이 'free'면 False
2. `subscription_expires_at`이 현재 시간 이전이면 False
3. 그 외 True

**사용 예시**:
```python
if user.is_premium():
    # 프리미엄 기능 제공
    print('프리미엄 콘텐츠에 접근할 수 있습니다.')
else:
    print('프리미엄 구독이 필요합니다.')
```

##### `activate_subscription(subscription_type, duration_days)`
구독을 활성화합니다.

**파라미터**:
- `subscription_type` (str): 구독 타입 ('monthly', 'yearly', 'premium')
- `duration_days` (int): 구독 기간(일)

**사용 예시**:
```python
# 월간 구독 활성화 (30일)
user.activate_subscription('monthly', 30)

# 연간 구독 활성화 (365일)
user.activate_subscription('yearly', 365)
```

#### 학습 관련 메서드

##### `update_streak()`
연속 학습 일수를 업데이트합니다.

**로직**:
1. 마지막 활동이 없으면 → streak_days = 1
2. 마지막 활동이 어제면 → streak_days += 1 (연속 학습)
3. 마지막 활동이 오늘이 아니고 어제도 아니면 → streak_days = 1 (리셋)
4. 오늘이면 변경 없음

**사용 예시**:
```python
# 사용자가 문제를 풀거나 학습을 완료했을 때
user.update_streak()
print(f'{user.streak_days}일 연속 학습 중!')
```

#### 계정 관련 메서드

##### `delete_account()`
계정을 소프트 삭제합니다.

**동작**:
- `is_deleted = True`
- `deleted_at = 현재 시간`
- `is_active = False`

**사용 예시**:
```python
user.delete_account()
print('계정이 삭제되었습니다.')
```

**참고**: 실제로 데이터베이스에서 삭제되지 않으며, 복구가 가능합니다.

##### `restore_account()`
삭제된 계정을 복원합니다.

**동작**:
- `is_deleted = False`
- `deleted_at = None`
- `is_active = True`

**사용 예시**:
```python
user.restore_account()
print('계정이 복원되었습니다.')
```

### Meta 정보

- **DB 테이블명**: `users`
- **기본 정렬**: 생성일 내림차순 (`-created_at`)
- **인덱스**:
  - `email` (로그인 조회 최적화)
  - `nickname` (검색 최적화)
  - `is_deleted, created_at` (복합 인덱스, 활성 사용자 조회 최적화)

---

## SocialAccount 모델

**위치**: `users/models.py:241-411`

### 개요
소셜 로그인(Google, Kakao, Naver, Apple) 계정을 관리하는 모델입니다. User와 1:1 관계를 가지며, 한 명의 사용자는 하나의 소셜 계정만 연결할 수 있습니다.

### 필드 설명

#### 관계 필드
| 필드명 | 타입 | 설명 | 관계 |
|--------|------|------|------|
| `user` | OneToOneField | 연결된 사용자 | User 1:1 |

#### 소셜 제공자 정보
| 필드명 | 타입 | 설명 | 선택지 |
|--------|------|------|--------|
| `provider` | CharField | 소셜 제공자 | 'google', 'kakao', 'naver', 'apple' |
| `social_id` | CharField | 제공자가 부여한 고유 ID | - |
| `social_email` | EmailField | 소셜 계정의 이메일 | 선택사항 |
| `social_name` | CharField | 소셜 계정의 이름 | 선택사항 |

#### 토큰 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `access_token` | TextField | Access Token |
| `refresh_token` | TextField | Refresh Token |
| `token_expires_at` | DateTimeField | 토큰 만료 시간 |

#### 추가 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `extra_data` | JSONField | 제공자별 추가 정보 (dict) |
| `is_active` | BooleanField | 활성 상태 |

#### 타임스탬프
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `created_at` | DateTimeField | 연결 시간 |
| `updated_at` | DateTimeField | 수정 시간 |
| `last_login_at` | DateTimeField | 마지막 로그인 |

### 인스턴스 메서드

#### `update_profile(name=None, email=None, profile_image=None, extra_data=None)`
소셜 계정의 프로필 정보를 업데이트합니다.

**파라미터**:
- `name` (str): 이름
- `email` (str): 이메일
- `profile_image` (str): 프로필 이미지 URL
- `extra_data` (dict): 추가 데이터

**사용 예시**:
```python
social_account.update_profile(
    name='홍길동',
    email='updated@example.com',
    extra_data={'phone': '010-1234-5678'}
)
```

#### `update_tokens(access_token=None, refresh_token=None, expires_in=None)`
토큰 정보를 업데이트합니다.

**파라미터**:
- `access_token` (str): Access Token
- `refresh_token` (str): Refresh Token
- `expires_in` (int): 만료 시간(초)

**사용 예시**:
```python
social_account.update_tokens(
    access_token='new_access_token',
    refresh_token='new_refresh_token',
    expires_in=3600  # 1시간
)
```

#### `update_last_login()`
마지막 로그인 시간을 현재 시간으로 업데이트합니다.

**사용 예시**:
```python
social_account.update_last_login()
```

#### `deactivate()`
소셜 계정을 비활성화합니다.

**사용 예시**:
```python
social_account.deactivate()
```

#### `reactivate()`
소셜 계정을 재활성화합니다.

**사용 예시**:
```python
social_account.reactivate()
```

### 클래스 메서드

#### `find_or_create_user(provider, social_id, **user_data)`
소셜 계정으로 User를 찾거나 새로 생성합니다. **OAuth 로그인의 핵심 메서드**입니다.

**파라미터**:
- `provider` (str): 'google', 'kakao', 'naver', 'apple'
- `social_id` (str): 소셜 제공자의 고유 ID
- `**user_data` (dict):
  - `email` (str): 이메일
  - `nickname` (str): 닉네임 (선택)
  - `name` (str): 이름
  - `profile_image` (str): 프로필 이미지 URL
  - `extra_data` (dict): 추가 데이터

**반환값**: `(user, created, social_account)` 튜플
- `user`: User 인스턴스
- `created` (bool): 신규 사용자 생성 여부
- `social_account`: SocialAccount 인스턴스

**로직**:
1. 기존 소셜 계정 검색 (`provider` + `social_id`)
   - 있으면: 프로필 정보 업데이트 후 반환
2. 없으면: 이메일로 기존 User 검색
   - 있으면: 해당 User에 소셜 계정 연결
   - 없으면: 새 User 생성 후 소셜 계정 연결

**사용 예시**:
```python
# Google 로그인
user, is_new, social_account = SocialAccount.find_or_create_user(
    provider='google',
    social_id='google_user_12345',
    email='user@gmail.com',
    name='홍길동',
    extra_data={'locale': 'ko'}
)

if is_new:
    print('신규 회원가입 완료!')
else:
    print('기존 회원 로그인!')
```

#### `find_user_by_social(provider, social_id)`
소셜 계정으로 사용자를 찾습니다.

**파라미터**:
- `provider` (str): 소셜 제공자
- `social_id` (str): 소셜 ID

**반환값**: User 인스턴스 또는 None

**사용 예시**:
```python
user = SocialAccount.find_user_by_social('kakao', 'kakao_user_67890')
if user:
    print(f'찾은 사용자: {user.email}')
else:
    print('사용자를 찾을 수 없습니다.')
```

#### `get_by_provider_and_user(provider, user)`
특정 제공자의 사용자 소셜 계정을 조회합니다.

**파라미터**:
- `provider` (str): 소셜 제공자
- `user` (User): User 인스턴스

**반환값**: SocialAccount 인스턴스 또는 None

**사용 예시**:
```python
social_account = SocialAccount.get_by_provider_and_user('naver', user)
if social_account:
    print(f'네이버 계정 연결됨: {social_account.social_email}')
```

### Meta 정보

- **DB 테이블명**: `social_accounts`
- **유니크 제약**: `provider` + `social_id` (같은 소셜 계정 중복 방지)
- **기본 정렬**: 생성일 내림차순 (`-created_at`)
- **인덱스**:
  - `provider, social_id` (복합 인덱스, 로그인 조회 최적화)
  - `user, is_active` (복합 인덱스)
  - `social_email`

---

## CustomRefreshToken 모델

**위치**: `users/models.py:533-704`

### 개요
JWT Refresh Token을 관리하는 모델입니다. 토큰 로테이션, 디바이스 제한, 세션 관리 기능을 제공합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `user` | ForeignKey | 토큰 소유자 (User) |
| `refresh_token` | TextField | Refresh Token 문자열 (유니크) |
| `expires_at` | DateTimeField | 만료 시간 |
| `is_active` | BooleanField | 활성 상태 |

#### 디바이스 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `device_id` | CharField | 디바이스 고유 ID |
| `device_name` | CharField | 디바이스 이름 (예: 'iPhone 13') |
| `ip_address` | GenericIPAddressField | IP 주소 |
| `user_agent` | TextField | User Agent 정보 |

#### 타임스탬프
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `created_at` | DateTimeField | 생성 시간 |
| `updated_at` | DateTimeField | 수정 시간 |
| `last_used_at` | DateTimeField | 마지막 사용 시간 |

### 인스턴스 메서드

#### `is_valid()`
토큰의 유효성을 검사합니다.

**반환값**:
- `True`: 토큰이 활성 상태이고 만료되지 않음
- `False`: 비활성 상태이거나 만료됨

**사용 예시**:
```python
if token.is_valid():
    # 토큰으로 인증 처리
    print('유효한 토큰입니다.')
else:
    print('토큰이 만료되었거나 비활성 상태입니다.')
```

#### `deactivate()`
토큰을 비활성화합니다.

**사용 예시**:
```python
token.deactivate()
```

#### `update_last_used()`
마지막 사용 시간을 현재 시간으로 업데이트합니다.

**사용 예시**:
```python
token.update_last_used()
```

### 클래스 메서드

#### `create_for_user(user, refresh_token_string, request=None, **kwargs)`
사용자를 위한 Refresh Token을 생성합니다. **토큰 로테이션**과 **디바이스 제한**을 포함합니다.

**파라미터**:
- `user` (User): 사용자 인스턴스
- `refresh_token_string` (str): Refresh Token 문자열
- `request` (HttpRequest): HTTP 요청 객체 (선택)
- `**kwargs`:
  - `device_id` (str): 디바이스 ID
  - `device_name` (str): 디바이스 이름
  - `ip_address` (str): IP 주소
  - `user_agent` (str): User Agent

**로직**:
1. **토큰 로테이션**: 같은 디바이스의 기존 토큰들 무효화
2. **디바이스 제한**: 최대 5개 디바이스까지만 허용
   - 초과 시 가장 오래 사용하지 않은 디바이스 토큰 무효화
3. 새 토큰 생성 (만료: 7일)

**사용 예시**:
```python
token = CustomRefreshToken.create_for_user(
    user=user,
    refresh_token_string='eyJ0eXAiOiJKV1QiLCJhbGc...',
    device_id='device_12345',
    device_name='iPhone 13',
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...'
)
```

#### `cleanup_expired_tokens(days_old=30)`
오래된 만료된 토큰을 정리합니다.

**파라미터**:
- `days_old` (int): 며칠 이전의 토큰을 삭제할지 (기본: 30일)

**반환값**: 삭제된 토큰 개수

**삭제 대상**:
- 만료된 토큰
- 비활성화된 지 `days_old`일 이상 지난 토큰

**사용 예시**:
```python
# 정기 작업(Celery Task 등)에서 실행
deleted_count = CustomRefreshToken.cleanup_expired_tokens(days_old=30)
print(f'{deleted_count}개의 토큰이 삭제되었습니다.')
```

#### `revoke_device_tokens(user, device_id)`
특정 디바이스의 모든 토큰을 무효화합니다.

**파라미터**:
- `user` (User): 사용자
- `device_id` (str): 디바이스 ID

**반환값**: 무효화된 토큰 개수

**사용 예시**:
```python
# 사용자가 특정 디바이스에서 로그아웃
count = CustomRefreshToken.revoke_device_tokens(user, 'device_12345')
print(f'{count}개의 토큰이 무효화되었습니다.')
```

#### `revoke_user_all_logout(user, except_token=None)`
사용자의 모든 토큰을 무효화합니다 (전체 로그아웃).

**파라미터**:
- `user` (User): 사용자
- `except_token` (CustomRefreshToken): 예외로 둘 토큰 (선택)

**반환값**: 무효화된 토큰 개수

**사용 예시**:
```python
# 모든 디바이스에서 로그아웃
count = CustomRefreshToken.revoke_user_all_logout(user)

# 현재 디바이스를 제외하고 로그아웃
count = CustomRefreshToken.revoke_user_all_logout(user, except_token=current_token)
```

#### `get_user_active_sessions(user)`
사용자의 활성화된 세션(디바이스) 목록을 조회합니다.

**파라미터**:
- `user` (User): 사용자

**반환값**: QuerySet (dict 형태)
- `device_id`: 디바이스 ID
- `device_name`: 디바이스 이름
- `ip_address`: IP 주소
- `user_agent`: User Agent
- `last_used_at`: 마지막 사용 시간
- `expires_at`: 만료 시간

**사용 예시**:
```python
sessions = CustomRefreshToken.get_user_active_sessions(user)
for session in sessions:
    print(f"디바이스: {session['device_name']}")
    print(f"IP: {session['ip_address']}")
    print(f"마지막 사용: {session['last_used_at']}")
```

### Meta 정보

- **DB 테이블명**: `refresh_tokens`
- **인덱스**:
  - `user, is_active` (사용자별 활성 토큰 조회)
  - `refresh_token` (토큰 검증)
  - `expires_at` (만료 토큰 정리)

---

## 일반적인 사용 시나리오

### 1. 회원가입 (이메일/비밀번호)
```python
user = User.objects.create_user(
    email='newuser@example.com',
    password='secure_password123',
    nickname='MyNickname'
)
```

### 2. 소셜 로그인 (Google)
```python
user, is_new, social_account = SocialAccount.find_or_create_user(
    provider='google',
    social_id='google_12345',
    email='user@gmail.com',
    name='홍길동'
)

# JWT 토큰 생성
refresh_token = CustomRefreshToken.create_for_user(
    user=user,
    refresh_token_string='jwt_refresh_token...',
    device_id='device_xyz'
)
```

### 3. 문제 풀이 후 보상
```python
# 하트 사용
if user.use_heart():
    # 문제 풀이
    correct = solve_problem()

    if correct:
        # 경험치 및 코인 보상
        user.add_exp(10)
        user.add_coins(5)

        # 연속 학습 업데이트
        user.update_streak()
```

### 4. 구독 활성화
```python
# 월간 구독 결제 후
user.activate_subscription('monthly', 30)

# 프리미엄 기능 사용 시
if user.is_premium():
    # 프리미엄 콘텐츠 제공
    pass
```

### 5. 계정 삭제 및 복원
```python
# 사용자가 탈퇴 요청
user.delete_account()

# 30일 이내 복구 요청
user.restore_account()
```

---

## 주의사항 및 개선 제안

### 버그 가능성
1. **User.add_exp()**: `self.level` 필드가 User 모델에 정의되어 있지 않음
   - 해결: `level` 필드를 추가하거나 메서드 수정 필요

### 보안 권장사항
1. **토큰 저장**: `access_token`과 `refresh_token`을 평문으로 저장 중
   - 고려: 암호화 또는 해시 처리
2. **의심스러운 활동 감지**: `detect_suspicious_activity()` 메서드가 주석 처리됨
   - 고려: 구현 및 활성화

### 성능 최적화
1. **인덱스 활용**: 자주 조회되는 필드들에 인덱스가 잘 설정되어 있음
2. **select_related 사용**: SocialAccount 조회 시 `select_related('user')` 사용으로 N+1 쿼리 방지

---

## 관련 파일
- 모델 정의: `users/models.py`
- 시리얼라이저: `users/serializers.py`
- 뷰: `users/views.py`
- URL 설정: `users/urls.py`

---

**문서 최종 업데이트**: 2025-11-13
