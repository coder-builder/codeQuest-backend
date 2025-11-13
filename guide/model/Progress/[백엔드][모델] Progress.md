# Progress Models 문서

CodeQuest 프로젝트의 학습 진도 관련 모델들에 대한 상세 가이드입니다.

---

## 목차
1. [UserProgress 모델](#userprogress-모델)
2. [WorldProgress 모델](#worldprogress-모델)
3. [LessonProgress 모델](#lessonprogress-모델)
4. [DailyStudy 모델](#dailystudy-모델)
5. [StudySession 모델](#studysession-모델)

---

## UserProgress 모델

**위치**: `progress/models.py:9-97`

### 개요
사용자의 전체 학습 진도를 추적하는 모델입니다. User와 1:1 관계를 가지며, 전체 통계, 연속 학습, 주간 목표 등을 관리합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | UUIDField | 고유 ID (PK, 자동생성) |
| `user` | OneToOneField | 사용자 (User와 1:1 관계) |

**관계**: `user.progress`로 접근 가능

#### 전체 학습 통계
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `total_lessons_completed` | IntegerField | 완료한 총 레슨 수 | 0 |
| `total_problems_solved` | IntegerField | 해결한 총 문제 수 | 0 |
| `total_study_time_minutes` | IntegerField | 총 학습 시간(분) | 0 |
| `total_exp_earned` | IntegerField | 총 획득 경험치 | 0 |

#### 현재 학습 상태
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `current_world` | CharField | 현재 학습 중인 월드 | '' |
| `current_stage` | IntegerField | 현재 스테이지 번호 | 1 |
| `current_lesson` | IntegerField | 현재 레슨 번호 | 1 |

**예시**: `current_world='Python'`, `current_stage=2`, `current_lesson=5` → Python 월드의 2번 스테이지, 5번 레슨

#### 연속 학습 (Streak)
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `current_streak` | IntegerField | 현재 연속 학습 일수 | 0 |
| `longest_streak` | IntegerField | 최장 연속 학습 일수 | 0 |
| `last_study_date` | DateField | 마지막 학습 날짜 | null |

#### 주간 목표
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `weekly_goal_days` | IntegerField | 주간 목표 일수 | 5 |
| `current_week_days` | IntegerField | 이번 주 달성 일수 | 0 |
| `week_start_date` | DateField | 주간 목표 시작일 | null |

#### 성취도
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `accuracy_rate` | FloatField | 정답률 (%) | 0.0 |
| `average_completion_time` | FloatField | 평균 완료 시간(분) | 0.0 |

#### 타임스탬프
| 필드명 | 타입 | 설명 | 자동 갱신 |
|--------|------|------|----------|
| `created_at` | DateTimeField | 생성 시간 | ❌ |
| `updated_at` | DateTimeField | 수정 시간 | ✅ |

### 메서드

#### `update_streak()`
연속 학습 일수를 업데이트합니다.

**파라미터**: 없음

**반환값**: 현재 연속 학습 일수 (int)

**로직**:
1. 오늘 이미 학습했으면 → 현재 연속 일수 반환
2. 마지막 학습이 어제면 → 연속 일수 +1
   - 최장 기록 갱신 시 `longest_streak` 업데이트
3. 그 외 (하루 이상 학습 안 함) → 연속 일수 1로 초기화
4. `last_study_date`를 오늘로 업데이트

**사용 예시**:
```python
progress = user.progress
current_streak = progress.update_streak()
print(f'{current_streak}일 연속 학습 중!')
```

#### `update_weekly_goal()`
주간 목표 달성 일수를 업데이트합니다.

**파라미터**: 없음

**반환값**: 없음

**로직**:
1. 현재 주의 시작일 계산 (월요일 기준)
2. 새로운 주가 시작되었으면 → `current_week_days`를 0으로 초기화
3. 오늘 학습 기록이 없으면 → `current_week_days` +1

**사용 예시**:
```python
progress.update_weekly_goal()
print(f'이번 주 {progress.current_week_days}/{progress.weekly_goal_days}일 학습 완료')
```

**참고**: 78번 줄에 오타가 있습니다. `today = timedelta(days=today.weekday())`는 `today - timedelta(days=today.weekday())`이어야 합니다.

#### `get_weekly_progress_percentage()`
주간 목표 달성률을 계산합니다.

**파라미터**: 없음

**반환값**: 달성률 (0.0 ~ 100.0)

**로직**:
- `(current_week_days / weekly_goal_days) * 100`
- 최대 100%로 제한

**사용 예시**:
```python
percentage = progress.get_weekly_progress_percentage()
print(f'주간 목표 달성률: {percentage:.1f}%')

# 출력 예시: "주간 목표 달성률: 80.0%" (4/5일 완료)
```

### Meta 정보

- **DB 테이블명**: `user_progress`
- **verbose_name**: 사용자 진도

---

## WorldProgress 모델

**위치**: `progress/models.py:99-145`

### 개요
월드별(Python, JavaScript 등) 학습 진도를 추적하는 모델입니다. 한 사용자가 여러 월드를 진행할 수 있습니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | UUIDField | 고유 ID (PK, 자동생성) |
| `user` | ForeignKey | 사용자 (User와 다대일 관계) |
| `world_name` | CharField | 월드 이름 (예: 'Python', 'JavaScript') |

**유니크 제약**: `user` + `world_name` 조합은 유일해야 함

#### 진행률
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `total_stages` | IntegerField | 전체 스테이지 수 | 0 |
| `completed_stages` | IntegerField | 완료한 스테이지 수 | 0 |
| `current_stage` | IntegerField | 현재 스테이지 번호 | 1 |
| `total_lessons` | IntegerField | 전체 레슨 수 | 0 |
| `completed_lessons` | IntegerField | 완료한 레슨 수 | 0 |

#### 통계
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `exp_earned` | IntegerField | 획득 경험치 | 0 |
| `time_spent_minutes` | IntegerField | 소요 시간(분) | 0 |
| `accuracy_rate` | FloatField | 정답률 (%) | 0.0 |

#### 상태
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `is_unlocked` | BooleanField | 잠금 해제 여부 | False |
| `is_completed` | BooleanField | 완료 여부 | False |
| `started_at` | DateTimeField | 시작 시간 | null |
| `completed_at` | DateTimeField | 완료 시간 | null |

#### 타임스탬프
| 필드명 | 타입 | 설명 | 자동 갱신 |
|--------|------|------|----------|
| `created_at` | DateTimeField | 생성 시간 | ❌ |
| `updated_at` | DateTimeField | 수정 시간 | ✅ |

### 속성 (Property)

#### `completion_percentage`
월드 완료 퍼센티지를 계산하는 읽기 전용 속성입니다.

**타입**: float

**계산식**: `(completed_lessons / total_lessons) * 100`

**사용 예시**:
```python
world_progress = WorldProgress.objects.get(user=user, world_name='Python')
print(f'Python 월드 진행률: {world_progress.completion_percentage:.1f}%')

# 출력 예시: "Python 월드 진행률: 45.5%" (20/44 레슨 완료)
```

**참고**: `@property` 데코레이터를 사용하여 메서드를 속성처럼 접근할 수 있습니다.

### Meta 정보

- **DB 테이블명**: `world_progress`
- **verbose_name**: 월드 진도
- **유니크 제약**: `user` + `world_name` (한 사용자가 같은 월드를 중복으로 가질 수 없음)

---

## LessonProgress 모델

**위치**: `progress/models.py:147-212`

### 개요
레슨별 상세 진도를 추적하는 모델입니다. 각 레슨의 진행 상태, 문제 풀이 결과, 점수 등을 기록합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | UUIDField | 고유 ID (PK, 자동생성) |
| `user` | ForeignKey | 사용자 (User와 다대일 관계) |

#### 레슨 식별
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `world_name` | CharField | 월드 이름 (예: 'Python') |
| `stage_number` | IntegerField | 스테이지 번호 |
| `lesson_number` | IntegerField | 레슨 번호 |

**유니크 제약**: `user` + `world_name` + `stage_number` + `lesson_number` 조합은 유일

**예시**: Python 월드의 3번 스테이지, 5번 레슨 → `world_name='Python'`, `stage_number=3`, `lesson_number=5`

#### 진행 상태
| 필드명 | 타입 | 설명 | 기본값 | 선택지 |
|--------|------|------|--------|--------|
| `status` | CharField | 진행 상태 | 'locked' | 'locked', 'unlocked', 'in_progress', 'completed', 'mastered' |

**상태별 의미**:
- `locked`: 잠김 (이전 레슨 미완료)
- `unlocked`: 해제됨 (시작 가능)
- `in_progress`: 진행 중 (시작했지만 미완료)
- `completed`: 완료됨 (한 번 이상 완료)
- `mastered`: 마스터 (높은 점수로 완료)

#### 성과
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `total_problems` | IntegerField | 전체 문제 수 | 0 |
| `solved_problems` | IntegerField | 해결한 문제 수 | 0 |
| `correct_answers` | IntegerField | 정답 수 | 0 |
| `total_attempts` | IntegerField | 총 시도 횟수 | 0 |

**참고**: `total_attempts`는 모든 문제 풀이 시도를 합산한 값입니다.

#### 점수/시간
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `best_score` | IntegerField | 최고 점수 | 0 |
| `total_time_seconds` | IntegerField | 총 소요 시간(초) | 0 |
| `exp_earned` | IntegerField | 획득 경험치 | 0 |

#### 타임스탬프
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `first_started_at` | DateTimeField | 최초 시작 시간 | null |
| `first_completed_at` | DateTimeField | 최초 완료 시간 | null |
| `last_attempt_at` | DateTimeField | 마지막 시도 시간 | null |
| `created_at` | DateTimeField | 생성 시간 | - |
| `updated_at` | DateTimeField | 수정 시간 | - |

### 속성 (Property)

#### `accuracy_rate`
정확도를 계산하는 읽기 전용 속성입니다.

**타입**: float

**계산식**: `(correct_answers / total_attempts) * 100`

**사용 예시**:
```python
lesson = LessonProgress.objects.get(
    user=user,
    world_name='Python',
    stage_number=1,
    lesson_number=3
)
print(f'정확도: {lesson.accuracy_rate:.1f}%')

# 출력 예시: "정확도: 85.0%" (17/20 정답)
```

### Meta 정보

- **DB 테이블명**: `lesson_progress`
- **verbose_name**: 레슨 진도
- **유니크 제약**: `user` + `world_name` + `stage_number` + `lesson_number`
- **인덱스**:
  - `user, status` (복합 인덱스, 사용자별 진행 상태 조회)
  - `world_name, stage_number` (복합 인덱스, 월드/스테이지별 조회)

---

## DailyStudy 모델

**위치**: `progress/models.py:214-260`

### 개요
일일 학습 기록을 저장하는 모델입니다. 하루 단위로 학습량과 성과를 추적합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | UUIDField | 고유 ID (PK, 자동생성) |
| `user` | ForeignKey | 사용자 (User와 다대일 관계) |
| `study_date` | DateField | 학습 날짜 |

**관계**: `user.daily_studies`로 접근 가능

**유니크 제약**: `user` + `study_date` (한 사용자의 같은 날짜 기록은 하나만)

#### 학습량
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `lessons_completed` | IntegerField | 완료한 레슨 수 | 0 |
| `problems_solved` | IntegerField | 해결한 문제 수 | 0 |
| `exp_earned` | IntegerField | 획득 경험치 | 0 |
| `study_time_minutes` | IntegerField | 학습 시간(분) | 0 |

#### 성과
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `correct_answers` | IntegerField | 정답 수 | 0 |
| `total_attempts` | IntegerField | 총 시도 횟수 | 0 |

#### 목표 달성 여부
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `goal_achieved` | BooleanField | 일일 목표 달성 여부 | False |

**참고**: 사용자의 `daily_goal_minutes`와 비교하여 설정

#### 타임스탬프
| 필드명 | 타입 | 설명 | 자동 갱신 |
|--------|------|------|----------|
| `created_at` | DateTimeField | 생성 시간 | ❌ |
| `updated_at` | DateTimeField | 수정 시간 | ✅ |

### 속성 (Property)

#### `accuracy_rate`
정확도를 계산하는 읽기 전용 속성입니다.

**타입**: float

**계산식**: `(correct_answers / total_attempts) * 100`

**사용 예시**:
```python
from datetime import date

# 오늘의 학습 기록 조회
today_study = DailyStudy.objects.get(user=user, study_date=date.today())
print(f'오늘 학습 시간: {today_study.study_time_minutes}분')
print(f'오늘 정확도: {today_study.accuracy_rate:.1f}%')
print(f'목표 달성: {"✓" if today_study.goal_achieved else "✗"}')

# 출력 예시:
# 오늘 학습 시간: 45분
# 오늘 정확도: 88.5%
# 목표 달성: ✓
```

### Meta 정보

- **DB 테이블명**: `daily_studies`
- **verbose_name**: 일일 학습 기록
- **유니크 제약**: `user` + `study_date`
- **기본 정렬**: 학습 날짜 내림차순 (`-study_date`)
- **인덱스**:
  - `user, study_date` (복합 인덱스, 사용자별 날짜 조회)
  - `study_date` (전체 통계 조회)

---

## StudySession 모델

**위치**: `progress/models.py:262-312`

### 개요
개별 학습 세션을 추적하는 모델입니다. 사용자가 특정 레슨을 시작하고 종료할 때까지의 세션을 기록합니다.

### 필드 설명

#### 기본 정보
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `id` | UUIDField | 고유 ID (PK, 자동생성) |
| `user` | ForeignKey | 사용자 (User와 다대일 관계) |

**관계**: `user.study_sessions`로 접근 가능

#### 세션 정보
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `session_start` | DateTimeField | 세션 시작 시간 | 현재 시간 |
| `session_end` | DateTimeField | 세션 종료 시간 | null |
| `duration_seconds` | IntegerField | 세션 지속 시간(초) | 0 |

**참고**: `duration_seconds`는 세션 종료 시 자동 계산됩니다.

#### 학습 내용
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `world_name` | CharField | 월드 이름 |
| `stage_number` | IntegerField | 스테이지 번호 |
| `lesson_number` | IntegerField | 레슨 번호 |

#### 세션 성과
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `problems_attempted` | IntegerField | 시도한 문제 수 | 0 |
| `problems_solved` | IntegerField | 해결한 문제 수 | 0 |
| `exp_gained` | IntegerField | 획득 경험치 | 0 |

#### 상태
| 필드명 | 타입 | 설명 | 기본값 |
|--------|------|------|--------|
| `is_active` | BooleanField | 활성 상태 (진행 중) | True |
| `completed_successfully` | BooleanField | 성공적으로 완료됨 | False |

#### 타임스탬프
| 필드명 | 타입 | 설명 |
|--------|------|------|
| `created_at` | DateTimeField | 생성 시간 |

### 메서드

#### `end_session()`
학습 세션을 종료합니다.

**파라미터**: 없음

**반환값**: 없음

**동작**:
1. `session_end`가 아직 설정되지 않았는지 확인
2. `session_end`를 현재 시간으로 설정
3. `duration_seconds` 계산 (종료 시간 - 시작 시간)
4. `is_active`를 False로 변경
5. `completed_successfully`를 True로 변경
6. 변경사항 저장

**사용 예시**:
```python
# 세션 시작
session = StudySession.objects.create(
    user=user,
    world_name='Python',
    stage_number=2,
    lesson_number=4
)

# ... 학습 진행 ...
session.problems_attempted = 5
session.problems_solved = 4
session.exp_gained = 20
session.save()

# 세션 종료
session.end_session()

print(f'학습 세션 완료!')
print(f'소요 시간: {session.duration_seconds // 60}분 {session.duration_seconds % 60}초')

# 출력 예시:
# 학습 세션 완료!
# 소요 시간: 15분 30초
```

### Meta 정보

- **DB 테이블명**: `study_sessions`
- **verbose_name**: 학습 세션
- **기본 정렬**: 세션 시작 시간 내림차순 (`-session_start`)
- **인덱스**:
  - `user, is_active` (복합 인덱스, 진행 중인 세션 조회)
  - `session_start` (시간대별 통계)

---

## 일반적인 사용 시나리오

### 1. 사용자 학습 시작
```python
from datetime import date
from django.utils import timezone

# UserProgress 생성 (회원가입 시)
user_progress = UserProgress.objects.create(user=user)

# Python 월드 잠금 해제
python_world = WorldProgress.objects.create(
    user=user,
    world_name='Python',
    total_stages=10,
    total_lessons=50,
    is_unlocked=True,
    started_at=timezone.now()
)

# 첫 번째 레슨 잠금 해제
lesson = LessonProgress.objects.create(
    user=user,
    world_name='Python',
    stage_number=1,
    lesson_number=1,
    status='unlocked',
    total_problems=5
)
```

### 2. 레슨 학습 세션
```python
# 세션 시작
session = StudySession.objects.create(
    user=user,
    world_name='Python',
    stage_number=1,
    lesson_number=1
)

# 문제 풀이
session.problems_attempted += 1
if answer_correct:
    session.problems_solved += 1
    session.exp_gained += 10
session.save()

# 세션 종료
session.end_session()
```

### 3. 레슨 완료 처리
```python
# 레슨 진도 업데이트
lesson.solved_problems += 1
lesson.correct_answers += 1
lesson.total_attempts += 1
lesson.last_attempt_at = timezone.now()

if lesson.solved_problems == lesson.total_problems:
    # 레슨 완료
    lesson.status = 'completed'
    if not lesson.first_completed_at:
        lesson.first_completed_at = timezone.now()

    # 다음 레슨 잠금 해제
    next_lesson, created = LessonProgress.objects.get_or_create(
        user=user,
        world_name='Python',
        stage_number=1,
        lesson_number=2,
        defaults={'status': 'unlocked'}
    )

lesson.save()
```

### 4. 일일 학습 기록 업데이트
```python
from datetime import date

today = date.today()
daily_study, created = DailyStudy.objects.get_or_create(
    user=user,
    study_date=today
)

# 학습 통계 업데이트
daily_study.lessons_completed += 1
daily_study.problems_solved += 5
daily_study.exp_earned += 50
daily_study.study_time_minutes += session.duration_seconds // 60
daily_study.correct_answers += 4
daily_study.total_attempts += 5

# 목표 달성 여부 확인
if daily_study.study_time_minutes >= user.daily_goal_minutes:
    daily_study.goal_achieved = True

daily_study.save()
```

### 5. 전체 진도 업데이트
```python
# UserProgress 업데이트
user_progress = user.progress
user_progress.total_lessons_completed += 1
user_progress.total_problems_solved += 5
user_progress.total_exp_earned += 50
user_progress.total_study_time_minutes += session.duration_seconds // 60
user_progress.current_world = 'Python'
user_progress.current_stage = 1
user_progress.current_lesson = 2
user_progress.save()

# 연속 학습 업데이트
user_progress.update_streak()
user_progress.update_weekly_goal()

# WorldProgress 업데이트
python_world.completed_lessons += 1
python_world.exp_earned += 50
python_world.time_spent_minutes += session.duration_seconds // 60
python_world.save()
```

### 6. 통계 조회
```python
# 최근 7일 학습 기록
from datetime import timedelta

week_ago = date.today() - timedelta(days=7)
recent_studies = DailyStudy.objects.filter(
    user=user,
    study_date__gte=week_ago
).order_by('study_date')

for study in recent_studies:
    print(f'{study.study_date}: {study.lessons_completed}레슨, {study.study_time_minutes}분')

# 월드별 진행률
worlds = WorldProgress.objects.filter(user=user, is_unlocked=True)
for world in worlds:
    print(f'{world.world_name}: {world.completion_percentage:.1f}% 완료')

# 현재 진행 중인 레슨
current_lessons = LessonProgress.objects.filter(
    user=user,
    status='in_progress'
)
```

---

## 주의사항 및 개선 제안

### 버그 가능성
1. **UserProgress.update_weekly_goal()**: 78번 줄에 오타
   ```python
   # 현재 (잘못됨)
   week_start = today = timedelta(days=today.weekday())

   # 수정 필요
   week_start = today - timedelta(days=today.weekday())
   ```

### 데이터 일관성
1. **트랜잭션 처리**: 여러 모델을 동시에 업데이트할 때 트랜잭션 사용 권장
   ```python
   from django.db import transaction

   with transaction.atomic():
       lesson.save()
       daily_study.save()
       user_progress.save()
   ```

2. **정확도 계산**: `accuracy_rate`가 여러 모델에 중복 계산됨
   - 고려: 정확도 계산 로직을 유틸리티 함수로 분리

### 성능 최적화
1. **인덱스**: 자주 조회되는 필드에 인덱스가 잘 설정됨
2. **Select Related**: 관계 조회 시 `select_related()` 사용 권장
   ```python
   # 권장
   sessions = StudySession.objects.select_related('user').filter(is_active=True)
   ```

### 기능 확장 제안
1. **레벨 계산**: UserProgress에 level 필드 추가 고려
2. **배지/업적**: 특정 조건 달성 시 배지 부여 기능
3. **학습 분석**: 시간대별, 요일별 학습 패턴 분석 기능

---

## 모델 간 관계도

```
User (users.User)
  │
  ├─ 1:1 ─> UserProgress (전체 학습 진도)
  │
  ├─ 1:N ─> WorldProgress (월드별 진도)
  │
  ├─ 1:N ─> LessonProgress (레슨별 진도)
  │
  ├─ 1:N ─> DailyStudy (일일 학습 기록)
  │
  └─ 1:N ─> StudySession (학습 세션)
```

**데이터 흐름**:
1. StudySession 생성 (학습 시작)
2. StudySession 업데이트 (문제 풀이)
3. StudySession 종료
4. LessonProgress 업데이트
5. DailyStudy 업데이트
6. WorldProgress 업데이트
7. UserProgress 업데이트

---

## 관련 파일
- 모델 정의: `progress/models.py`
- 시리얼라이저: `progress/serializers.py` (있는 경우)
- 뷰: `progress/views.py` (있는 경우)
- URL 설정: `progress/urls.py` (있는 경우)

---

**문서 최종 업데이트**: 2025-11-13
