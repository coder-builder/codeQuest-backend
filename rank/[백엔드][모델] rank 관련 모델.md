# Rank Models 가이드

> rank/models.py 파일에 정의된 랭킹 시스템 모델들의 상세 가이드

---

## 목차
1. [League 모델](#1-league-모델)
2. [LeagueParticipant 모델](#2-leagueparticipant-모델)
3. [UserRankingHistory 모델](#3-userrankinghistory-모델)
4. [TierConfig 모델](#4-tierconfig-모델)
5. [GlobalRanking 모델](#5-globalranking-모델)

---

## 1. League 모델

### 개요
주간 리그를 관리하는 모델입니다. 듀오링고 스타일의 주간 경쟁 시스템을 구현하며, 각 티어별로 매주 새로운 리그가 생성됩니다.

### 테이블 정보
- **테이블명**: `leagues`
- **파일 위치**: [rank/models.py:16](rank/models.py#L16)

### 필드 설명

#### 1.1 기본 키
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `league_id` | UUIDField | 리그의 고유 식별자 (Primary Key, 자동 생성) |

#### 1.2 티어 정보
| 필드명 | 타입 | 설명 | 선택지 |
|-------|------|------|-------|
| `tier` | CharField(20) | 리그의 티어 등급 | BRONZE, SILVER, GOLD, PLATINUM, DIAMOND, MASTER, LEGEND |

**티어별 EXP 범위**:
- BRONZE: 0 ~ 999 XP
- SILVER: 1,000 ~ 2,499 XP
- GOLD: 2,500 ~ 4,999 XP
- PLATINUM: 5,000 ~ 9,999 XP
- DIAMOND: 10,000 ~ 19,999 XP
- MASTER: 20,000 ~ 49,999 XP
- LEGEND: 50,000+ XP

#### 1.3 기간 정보
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `week_start` | DateField | 리그 시작 날짜 |
| `week_end` | DateField | 리그 종료 날짜 |

#### 1.4 참가자 관리
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `max_participants` | IntegerField | 50 | 리그 최대 참가자 수 |
| `current_participants` | IntegerField | 0 | 현재 참가자 수 |

#### 1.5 상태 관리
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `is_active` | BooleanField | True | 리그 활성화 상태 |
| `is_finished` | BooleanField | False | 리그 종료 여부 |

#### 1.6 타임스탬프
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `created_at` | DateTimeField | 생성 시간 (자동 기록) |
| `updated_at` | DateTimeField | 수정 시간 (자동 갱신) |

### 계산 속성 (@property)

#### `is_full`
```python
league.is_full  # True 또는 False
```
- **반환값**: Boolean
- **설명**: 리그 정원이 가득 찼는지 확인
- **계산 로직**: `current_participants >= max_participants`
- **위치**: [rank/models.py:67-69](rank/models.py#L67-L69)

#### `days_remaining`
```python
league.days_remaining  # 3 (남은 일수)
```
- **반환값**: Integer (일수)
- **설명**: 리그 종료까지 남은 일수
- **계산 로직**:
  - 종료일이 지나면 0 반환
  - 그렇지 않으면 `(week_end - today).days + 1`
- **위치**: [rank/models.py:71-76](rank/models.py#L71-L76)

### 메서드

#### `add_participant()`
```python
success = league.add_participant()
```
- **매개변수**: 없음
- **반환값**: Boolean (성공 여부)
- **설명**: 리그에 참가자를 추가
- **동작**:
  1. 리그가 가득 차지 않았는지 확인
  2. `current_participants` 1 증가
  3. 변경사항 저장
- **반환**: 성공 시 True, 정원 초과 시 False
- **위치**: [rank/models.py:79-84](rank/models.py#L79-L84)

#### `remove_participant()`
```python
league.remove_participant()
```
- **매개변수**: 없음
- **반환값**: 없음
- **설명**: 리그에서 참가자를 제거
- **동작**:
  1. 참가자 수가 0보다 큰지 확인
  2. `current_participants` 1 감소
  3. 변경사항 저장
- **위치**: [rank/models.py:86-89](rank/models.py#L86-L89)

### 데이터베이스 인덱스
- `['tier', 'week_start', 'is_active']`: 티어별 활성 리그 조회 최적화
- `['is_active', 'is_finished']`: 리그 상태별 조회 최적화

### 사용 예시
```python
from rank.models import League
from datetime import date, timedelta

# 1. 새로운 주간 리그 생성
league = League.objects.create(
    tier='GOLD',
    week_start=date.today(),
    week_end=date.today() + timedelta(days=7),
    max_participants=50
)

# 2. 리그 정원 확인
if not league.is_full:
    league.add_participant()

# 3. 남은 일수 확인
print(f"리그 종료까지 {league.days_remaining}일 남았습니다.")

# 4. 활성화된 GOLD 티어 리그 조회
active_gold_leagues = League.objects.filter(
    tier='GOLD',
    is_active=True,
    is_finished=False
)
```

---

## 2. LeagueParticipant 모델

### 개요
리그에 참가한 사용자의 정보와 성적을 관리하는 모델입니다. 주간 EXP, 순위, 승급/강등 상태 등을 추적합니다.

### 테이블 정보
- **테이블명**: `league_participants`
- **파일 위치**: [rank/models.py:95](rank/models.py#L95)

### 필드 설명

#### 2.1 기본 키 및 관계
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `participant_id` | UUIDField | 참가자 고유 식별자 (Primary Key, 자동 생성) |
| `league` | ForeignKey | 참가 중인 리그 (League 모델 참조) |
| `user` | ForeignKey | 참가자 (users.User 모델 참조) |

**관계 설정**:
- `league`: CASCADE 삭제 (리그 삭제 시 참가 기록도 삭제)
- `user`: CASCADE 삭제 (유저 탈퇴 시 참가 기록도 삭제)

#### 2.2 주간 EXP 정보
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `weekly_coding_exp` | IntegerField | 0 | 주간 코딩 문제 획득 EXP |
| `weekly_cert_exp` | IntegerField | 0 | 주간 자격증 문제 획득 EXP |

#### 2.3 순위 정보
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `current_rank` | IntegerField | 0 | 현재 순위 |
| `previous_rank` | IntegerField | 0 | 이전 순위 |
| `highest_rank` | IntegerField | 0 | 최고 순위 (역대 최고) |

#### 2.4 승급/강등 상태
| 필드명 | 타입 | 기본값 | 선택지 | 설명 |
|-------|------|--------|-------|------|
| `status` | CharField(20) | 'SAFE' | SAFE, PROMOTION, DEMOTION | 현재 승급/강등 상태 |

**상태 기준** (50명 리그 기준):
- `PROMOTION`: 1~10위 (승급권)
- `SAFE`: 11~40위 (안전권)
- `DEMOTION`: 41~50위 (강등권)

#### 2.5 활동 추적
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `last_activity_at` | DateTimeField | null | 마지막 활동 시간 |
| `total_activities` | IntegerField | 0 | 총 활동 횟수 (문제 풀이 횟수) |

#### 2.6 타임스탬프
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `joined_at` | DateTimeField | 리그 참가 시간 (자동 기록) |
| `updated_at` | DateTimeField | 마지막 업데이트 시간 (자동 갱신) |

### 계산 속성 (@property)

#### `weekly_total_exp`
```python
participant.weekly_total_exp  # 350
```
- **반환값**: Integer
- **설명**: 주간 총 EXP (코딩 + 자격증)
- **계산 로직**: `weekly_coding_exp + weekly_cert_exp`
- **위치**: [rank/models.py:148-150](rank/models.py#L148-L150)

#### `rank_change`
```python
participant.rank_change  # 3 (3계단 상승)
```
- **반환값**: Integer
- **설명**: 순위 변동폭
- **계산 로직**: `previous_rank - current_rank`
- **해석**:
  - 양수: 순위 상승 (예: 10위 → 7위 = +3)
  - 음수: 순위 하락 (예: 5위 → 8위 = -3)
  - 0: 순위 유지 또는 첫 순위
- **위치**: [rank/models.py:152-157](rank/models.py#L152-L157)

#### `rank_trend`
```python
participant.rank_trend  # 'UP', 'DOWN', 또는 'SAME'
```
- **반환값**: String
- **설명**: 순위 변동 추세
- **계산 로직**:
  - `rank_change > 0` → 'UP' (상승)
  - `rank_change < 0` → 'DOWN' (하락)
  - `rank_change == 0` → 'SAME' (유지)
- **위치**: [rank/models.py:159-167](rank/models.py#L159-L167)

### 메서드

#### `add_exp(exp_amount, exp_type='coding')`
```python
participant.add_exp(100, 'coding')        # 코딩 EXP 100 추가
participant.add_exp(50, 'certification')  # 자격증 EXP 50 추가
```
- **매개변수**:
  - `exp_amount` (int): 추가할 EXP 양
  - `exp_type` (str): EXP 타입 ('coding' 또는 'certification')
- **반환값**: 없음
- **설명**: 참가자에게 EXP를 추가하고 활동을 기록
- **동작**:
  1. exp_type에 따라 `weekly_coding_exp` 또는 `weekly_cert_exp` 증가
  2. `last_activity_at`을 현재 시간으로 갱신
  3. `total_activities` 1 증가
  4. 변경사항 저장
- **위치**: [rank/models.py:170-184](rank/models.py#L170-L184)

#### `update_rank(new_rank)`
```python
participant.update_rank(5)  # 5위로 순위 업데이트
```
- **매개변수**:
  - `new_rank` (int): 새로운 순위
- **반환값**: 없음
- **설명**: 참가자의 순위를 업데이트하고 최고 순위를 갱신
- **동작**:
  1. 현재 순위를 이전 순위로 백업
  2. 새 순위 설정
  3. 최고 순위 갱신 체크 (새 순위가 더 높으면 갱신)
  4. 변경사항 저장
- **위치**: [rank/models.py:186-196](rank/models.py#L186-L196)

#### `update_status(total_participants)`
```python
participant.update_status(50)  # 50명 리그에서 상태 업데이트
```
- **매개변수**:
  - `total_participants` (int): 리그 내 총 참가자 수
- **반환값**: 없음
- **설명**: 현재 순위에 따라 승급/강등 상태를 업데이트
- **동작**:
  1. 순위에 따라 상태 결정:
     - 1~10위: 'PROMOTION' (승급권)
     - 하위 10명: 'DEMOTION' (강등권)
     - 나머지: 'SAFE' (안전권)
  2. 변경사항 저장
- **위치**: [rank/models.py:198-206](rank/models.py#L198-L206)

### 데이터베이스 인덱스
- `['league', 'current_rank']`: 리그별 순위 조회 최적화
- `['user', 'league']`: 유저의 리그 참가 기록 조회 최적화
- `['-weekly_coding_exp', '-weekly_cert_exp']`: EXP 기준 정렬 최적화

### 유니크 제약
- `('league', 'user')`: 한 유저는 한 리그에 한 번만 참가 가능

### 사용 예시
```python
from rank.models import LeagueParticipant

# 1. 리그 참가자 생성
participant = LeagueParticipant.objects.create(
    league=league,
    user=user
)

# 2. 문제 풀이 후 EXP 추가
participant.add_exp(100, 'coding')       # 코딩 문제 100 EXP
participant.add_exp(50, 'certification') # 자격증 문제 50 EXP

# 3. 총 EXP 확인
print(f"총 EXP: {participant.weekly_total_exp}")  # 150

# 4. 순위 업데이트
participant.update_rank(15)

# 5. 순위 변동 확인
print(f"순위 변동: {participant.rank_change}계단 ({participant.rank_trend})")

# 6. 승급/강등 상태 업데이트
participant.update_status(total_participants=50)
print(f"상태: {participant.get_status_display()}")  # "Safe"

# 7. 리그 내 순위표 조회
leaderboard = LeagueParticipant.objects.filter(
    league=league
).order_by('current_rank')
```

---

## 3. UserRankingHistory 모델

### 개요
종료된 리그의 최종 결과를 기록하는 모델입니다. 유저의 주간 랭킹 히스토리, 승급/강등 결과, 보상 내역을 영구 보관합니다.

### 테이블 정보
- **테이블명**: `user_ranking_history`
- **파일 위치**: [rank/models.py:212](rank/models.py#L212)

### 필드 설명

#### 3.1 기본 키 및 관계
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `history_id` | UUIDField | 히스토리 고유 식별자 (Primary Key, 자동 생성) |
| `user` | ForeignKey | 유저 (users.User 모델 참조) |
| `league` | ForeignKey | 해당 리그 (League 모델 참조) |

**관계 설정**:
- `user`: CASCADE 삭제 (유저 탈퇴 시 히스토리도 삭제)
  - 대안: `PROTECT`로 변경하여 히스토리 보존 가능
- `league`: CASCADE 삭제 (리그 삭제 시 히스토리도 삭제)

**역참조**:
- `user.ranking_history.all()` → 이 유저의 모든 주간 랭킹 히스토리
- `league.history_records.all()` → 이 리그의 모든 히스토리 기록

#### 3.2 최종 기록
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `final_rank` | IntegerField | 리그 종료 시 최종 순위 |
| `final_exp` | IntegerField | 리그 종료 시 총 EXP |
| `final_coding_exp` | IntegerField | 리그 종료 시 코딩 EXP |
| `final_cert_exp` | IntegerField | 리그 종료 시 자격증 EXP |

#### 3.3 승급/강등 결과
| 필드명 | 타입 | 선택지 | 설명 |
|-------|------|--------|------|
| `result` | CharField(20) | PROMOTED, DEMOTED, MAINTAINED | 승급/강등/유지 결과 |

**결과 타입**:
- `PROMOTED`: 승급됨 (상위 티어로 이동)
- `DEMOTED`: 강등됨 (하위 티어로 이동)
- `MAINTAINED`: 티어 유지

#### 3.4 보상 정보
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `reward_coins` | IntegerField | 0 | 획득한 코인 수 |
| `reward_items` | JSONField | {} | 획득한 아이템 정보 (JSON 형식) |

**reward_items 예시**:
```json
{
  "badge": "gold_weekly_winner",
  "skin": "champion_avatar",
  "boost": "2x_exp_24h"
}
```

#### 3.5 타임스탬프
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `recorded_at` | DateTimeField | 기록 생성 시간 (자동 기록) |

### 데이터베이스 인덱스
- `['user', '-recorded_at']`: 유저의 최근 히스토리 조회 최적화
- `['league', 'final_rank']`: 리그별 순위 조회 최적화

### 정렬
- 기본 정렬: 최신순 (`-recorded_at`)

### 사용 예시
```python
from rank.models import UserRankingHistory

# 1. 리그 종료 후 히스토리 기록 생성
history = UserRankingHistory.objects.create(
    user=user,
    league=league,
    final_rank=5,
    final_exp=1500,
    final_coding_exp=1000,
    final_cert_exp=500,
    result='PROMOTED',
    reward_coins=500,
    reward_items={
        'badge': 'gold_weekly_winner',
        'boost': '2x_exp_24h'
    }
)

# 2. 유저의 최근 랭킹 히스토리 조회 (최근 5주)
recent_history = UserRankingHistory.objects.filter(
    user=user
).order_by('-recorded_at')[:5]

# 3. 특정 리그의 TOP 10 조회
league_top10 = UserRankingHistory.objects.filter(
    league=league
).order_by('final_rank')[:10]

# 4. 유저의 승급 횟수 확인
promotion_count = UserRankingHistory.objects.filter(
    user=user,
    result='PROMOTED'
).count()

# 5. 월별 통계
from django.db.models import Avg, Max, Count
monthly_stats = UserRankingHistory.objects.filter(
    user=user,
    recorded_at__month=11
).aggregate(
    avg_rank=Avg('final_rank'),
    best_rank=Max('final_rank'),
    total_weeks=Count('history_id')
)
```

---

## 4. TierConfig 모델

### 개요
게임의 티어 시스템 설정을 관리하는 모델입니다. 각 티어의 EXP 범위, UI 표시 정보, 보상 배율 등을 저장합니다.

### 테이블 정보
- **테이블명**: `tier_configs`
- **파일 위치**: [rank/models.py:289](rank/models.py#L289)

### 필드 설명

#### 4.1 기본 키
| 필드명 | 타입 | 제약 | 설명 |
|-------|------|------|------|
| `tier` | CharField(20) | Primary Key, Unique | 티어 이름 (BRONZE, SILVER 등) |

#### 4.2 EXP 범위
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `min_exp` | IntegerField | 해당 티어의 최소 EXP |
| `max_exp` | IntegerField | 해당 티어의 최대 EXP |

#### 4.3 UI 표시 정보
| 필드명 | 타입 | 설명 | 예시 |
|-------|------|------|------|
| `icon` | CharField(10) | 티어 아이콘 (이모지 등) | 🥉, 🥈, 🥇 |
| `color` | CharField(7) | 티어 색상 코드 (HEX) | #CD7F32, #C0C0C0, #FFD700 |
| `order` | IntegerField | 티어 순서 (낮을수록 상위) | 1, 2, 3... |

#### 4.4 보상 배율
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `coin_multiplier` | FloatField | 1.0 | 코인 획득 배율 (티어가 높을수록 높음) |

### 데이터베이스 정렬
- 기본 정렬: `order` 오름차순 (1위부터)

### 사용 예시
```python
from rank.models import TierConfig

# 1. 티어 설정 초기화 (최초 1회)
tier_configs = [
    TierConfig(
        tier='BRONZE',
        min_exp=0,
        max_exp=999,
        icon='🥉',
        color='#CD7F32',
        order=1,
        coin_multiplier=1.0
    ),
    TierConfig(
        tier='SILVER',
        min_exp=1000,
        max_exp=2499,
        icon='🥈',
        color='#C0C0C0',
        order=2,
        coin_multiplier=1.2
    ),
    TierConfig(
        tier='GOLD',
        min_exp=2500,
        max_exp=4999,
        icon='🥇',
        color='#FFD700',
        order=3,
        coin_multiplier=1.5
    ),
    # ... 나머지 티어
]
TierConfig.objects.bulk_create(tier_configs)

# 2. 총 EXP로 티어 결정
def get_tier_by_exp(total_exp):
    return TierConfig.objects.filter(
        min_exp__lte=total_exp,
        max_exp__gte=total_exp
    ).first()

user_tier = get_tier_by_exp(3500)  # GOLD 티어

# 3. 티어 정보 조회
gold_tier = TierConfig.objects.get(tier='GOLD')
print(f"아이콘: {gold_tier.icon}")
print(f"색상: {gold_tier.color}")
print(f"코인 배율: {gold_tier.coin_multiplier}x")

# 4. 모든 티어 순서대로 조회
all_tiers = TierConfig.objects.all()  # order 기준 정렬됨

# 5. 코인 계산
base_coins = 100
reward_coins = int(base_coins * gold_tier.coin_multiplier)  # 150 코인
```

### 설정 예시
```python
# 전체 티어 설정 예시
TIER_SETTINGS = {
    'BRONZE': {
        'min_exp': 0,
        'max_exp': 999,
        'icon': '🥉',
        'color': '#CD7F32',
        'order': 1,
        'coin_multiplier': 1.0
    },
    'SILVER': {
        'min_exp': 1000,
        'max_exp': 2499,
        'icon': '🥈',
        'color': '#C0C0C0',
        'order': 2,
        'coin_multiplier': 1.2
    },
    'GOLD': {
        'min_exp': 2500,
        'max_exp': 4999,
        'icon': '🥇',
        'color': '#FFD700',
        'order': 3,
        'coin_multiplier': 1.5
    },
    'PLATINUM': {
        'min_exp': 5000,
        'max_exp': 9999,
        'icon': '💎',
        'color': '#E5E4E2',
        'order': 4,
        'coin_multiplier': 2.0
    },
    'DIAMOND': {
        'min_exp': 10000,
        'max_exp': 19999,
        'icon': '💠',
        'color': '#B9F2FF',
        'order': 5,
        'coin_multiplier': 2.5
    },
    'MASTER': {
        'min_exp': 20000,
        'max_exp': 49999,
        'icon': '👑',
        'color': '#FF6B6B',
        'order': 6,
        'coin_multiplier': 3.0
    },
    'LEGEND': {
        'min_exp': 50000,
        'max_exp': 999999999,
        'icon': '🌟',
        'color': '#FFD700',
        'order': 7,
        'coin_multiplier': 5.0
    }
}
```

---

## 5. GlobalRanking 모델

### 개요
전체 유저 대상의 글로벌 랭킹을 관리하는 모델입니다. 각 유저당 하나의 레코드만 존재하며, 총 EXP, 현재 티어, 문제 풀이 통계 등을 추적합니다.

### 테이블 정보
- **테이블명**: `global_rankings`
- **파일 위치**: [rank/models.py:349](rank/models.py#L349)

### 필드 설명

#### 5.1 기본 키 및 관계
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `user` | OneToOneField | 유저 (users.User 모델 참조, Primary Key) |

**관계 특징**:
- OneToOne 관계: 한 유저당 하나의 글로벌 랭킹 레코드
- CASCADE 삭제: 유저 탈퇴 시 랭킹 기록도 삭제
- 역참조: `user.global_ranking`

#### 5.2 순위 정보
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `rank` | IntegerField | 전체 유저 중 순위 (1위, 2위...) |

#### 5.3 EXP 정보
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `total_exp` | IntegerField | 0 | 누적 총 EXP (코딩 + 자격증) |

#### 5.4 티어 정보
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `current_tier` | CharField(20) | 현재 티어 (BRONZE, SILVER 등) |

#### 5.5 통계 정보
| 필드명 | 타입 | 기본값 | 설명 |
|-------|------|--------|------|
| `total_coding_problems` | IntegerField | 0 | 총 풀이한 코딩 문제 수 |
| `total_cert_problems` | IntegerField | 0 | 총 풀이한 자격증 문제 수 |

#### 5.6 타임스탬프
| 필드명 | 타입 | 설명 |
|-------|------|------|
| `last_updated` | DateTimeField | 마지막 업데이트 시간 (자동 갱신) |

### 데이터베이스 인덱스
- `['rank']`: 순위 조회 최적화 (TOP 100 등)
- `['current_tier', 'rank']`: 티어별 순위 조회 최적화

### 정렬
- 기본 정렬: `rank` 오름차순 (1위부터)

### 사용 예시
```python
from rank.models import GlobalRanking

# 1. 유저의 글로벌 랭킹 조회
try:
    ranking = GlobalRanking.objects.get(user=user)
    print(f"순위: {ranking.rank}위")
    print(f"총 EXP: {ranking.total_exp}")
    print(f"티어: {ranking.current_tier}")
except GlobalRanking.DoesNotExist:
    # 신규 유저의 경우 생성
    ranking = GlobalRanking.objects.create(
        user=user,
        rank=0,
        total_exp=0,
        current_tier='BRONZE'
    )

# 2. TOP 100 랭킹 조회
top_100 = GlobalRanking.objects.all()[:100]

# 3. 특정 티어의 상위 10명 조회
gold_top10 = GlobalRanking.objects.filter(
    current_tier='GOLD'
).order_by('rank')[:10]

# 4. 유저 순위 업데이트 (전체 재계산)
from django.db.models import F, Window
from django.db.models.functions import Rank

GlobalRanking.objects.update(
    rank=Window(
        expression=Rank(),
        order_by=F('total_exp').desc()
    )
)

# 5. 티어별 통계
from django.db.models import Count, Avg
tier_stats = GlobalRanking.objects.values('current_tier').annotate(
    user_count=Count('user'),
    avg_exp=Avg('total_exp'),
    avg_coding_problems=Avg('total_coding_problems')
).order_by('-avg_exp')

# 6. 특정 유저 주변 랭킹 조회 (위아래 5명씩)
user_rank = ranking.rank
nearby_rankings = GlobalRanking.objects.filter(
    rank__gte=user_rank - 5,
    rank__lte=user_rank + 5
).order_by('rank')
```

### 랭킹 업데이트 전략
```python
# 정기적인 랭킹 재계산 (Celery Task 예시)
from celery import shared_task
from django.db.models import F

@shared_task
def update_global_rankings():
    """
    전체 유저의 글로벌 랭킹을 EXP 기준으로 재계산
    매시간 또는 매일 실행 권장
    """
    rankings = GlobalRanking.objects.order_by('-total_exp')

    for idx, ranking in enumerate(rankings, start=1):
        ranking.rank = idx
        ranking.save(update_fields=['rank'])

    return f"Updated {rankings.count()} rankings"
```

---

## 모델 간 관계도

```
User (users.User)
  │
  ├─── OneToOne ───> GlobalRanking
  │
  ├─── OneToMany ──> LeagueParticipant
  │                      │
  │                      └─── ManyToOne ───> League
  │
  └─── OneToMany ──> UserRankingHistory
                         │
                         └─── ManyToOne ───> League

TierConfig (독립적인 설정 테이블)
```

---

## 주요 비즈니스 로직 예시

### 1. 주간 리그 시작 시 유저 배치
```python
from rank.models import League, LeagueParticipant, GlobalRanking

def assign_user_to_league(user):
    """유저를 적절한 티어의 리그에 배치"""

    # 1. 유저의 현재 티어 확인
    global_ranking = GlobalRanking.objects.get(user=user)
    tier = global_ranking.current_tier

    # 2. 해당 티어의 활성 리그 중 여유 있는 리그 찾기
    available_league = League.objects.filter(
        tier=tier,
        is_active=True,
        is_finished=False,
        current_participants__lt=F('max_participants')
    ).first()

    # 3. 여유 있는 리그가 없으면 새 리그 생성
    if not available_league:
        from datetime import date, timedelta
        available_league = League.objects.create(
            tier=tier,
            week_start=date.today(),
            week_end=date.today() + timedelta(days=7)
        )

    # 4. 참가자 등록
    participant = LeagueParticipant.objects.create(
        league=available_league,
        user=user
    )

    # 5. 리그 참가자 수 증가
    available_league.add_participant()

    return participant
```

### 2. 문제 풀이 후 EXP 및 순위 업데이트
```python
def solve_problem(user, problem_type, exp_earned):
    """문제 풀이 후 EXP 및 순위 업데이트"""

    # 1. 주간 리그 참가 기록 업데이트
    current_participant = LeagueParticipant.objects.filter(
        user=user,
        league__is_active=True
    ).first()

    if current_participant:
        current_participant.add_exp(exp_earned, problem_type)

    # 2. 글로벌 랭킹 업데이트
    global_ranking = GlobalRanking.objects.get(user=user)
    global_ranking.total_exp += exp_earned

    if problem_type == 'coding':
        global_ranking.total_coding_problems += 1
    elif problem_type == 'certification':
        global_ranking.total_cert_problems += 1

    global_ranking.save()

    # 3. 티어 업데이트 체크
    new_tier = TierConfig.objects.filter(
        min_exp__lte=global_ranking.total_exp,
        max_exp__gte=global_ranking.total_exp
    ).first()

    if new_tier and new_tier.tier != global_ranking.current_tier:
        global_ranking.current_tier = new_tier.tier
        global_ranking.save(update_fields=['current_tier'])
```

### 3. 주간 리그 종료 처리
```python
from datetime import date

def finalize_weekly_league(league):
    """주간 리그 종료 및 결과 처리"""

    # 1. 리그 상태 업데이트
    league.is_active = False
    league.is_finished = True
    league.save()

    # 2. 참가자 순위 최종 확정
    participants = league.participants.order_by('-weekly_coding_exp', '-weekly_cert_exp')

    for rank, participant in enumerate(participants, start=1):
        participant.update_rank(rank)
        participant.update_status(league.current_participants)

        # 3. 히스토리 기록 생성
        result = determine_result(participant, league)
        reward_coins = calculate_reward(participant, league)

        UserRankingHistory.objects.create(
            user=participant.user,
            league=league,
            final_rank=participant.current_rank,
            final_exp=participant.weekly_total_exp,
            final_coding_exp=participant.weekly_coding_exp,
            final_cert_exp=participant.weekly_cert_exp,
            result=result,
            reward_coins=reward_coins
        )

def determine_result(participant, league):
    """승급/강등/유지 결정"""
    if participant.status == 'PROMOTION':
        return 'PROMOTED'
    elif participant.status == 'DEMOTION':
        return 'DEMOTED'
    return 'MAINTAINED'

def calculate_reward(participant, league):
    """보상 계산"""
    tier_config = TierConfig.objects.get(tier=league.tier)
    base_reward = 100

    # 순위에 따른 보상
    if participant.current_rank <= 3:
        base_reward *= 5
    elif participant.current_rank <= 10:
        base_reward *= 3

    return int(base_reward * tier_config.coin_multiplier)
```

---

## 참고사항

### 데이터베이스 마이그레이션
```bash
# 마이그레이션 파일 생성
python manage.py makemigrations rank

# 마이그레이션 적용
python manage.py migrate rank
```

### Admin 등록 예시
```python
# rank/admin.py
from django.contrib import admin
from .models import League, LeagueParticipant, UserRankingHistory, TierConfig, GlobalRanking

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ['league_id', 'tier', 'week_start', 'week_end', 'current_participants', 'is_active']
    list_filter = ['tier', 'is_active', 'is_finished']
    search_fields = ['league_id']

@admin.register(LeagueParticipant)
class LeagueParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'league', 'current_rank', 'weekly_total_exp', 'status']
    list_filter = ['status', 'league__tier']
    search_fields = ['user__nickname']

# ... 나머지 모델들
```

### 성능 최적화 팁
1. **쿼리 최적화**: `select_related()`, `prefetch_related()` 사용
```python
# Bad
participants = LeagueParticipant.objects.all()
for p in participants:
    print(p.user.nickname)  # N+1 쿼리 발생

# Good
participants = LeagueParticipant.objects.select_related('user', 'league')
for p in participants:
    print(p.user.nickname)  # 1번의 JOIN 쿼리
```

2. **벌크 업데이트**: 대량 업데이트 시 `bulk_update()` 사용
```python
# 순위 일괄 업데이트
participants = list(league.participants.all())
for rank, p in enumerate(participants, start=1):
    p.current_rank = rank

LeagueParticipant.objects.bulk_update(participants, ['current_rank'])
```

3. **인덱스 활용**: 자주 조회하는 필드 조합에 인덱스 추가

---

## 문의 및 수정 이력
- **작성일**: 2025-11-14
- **작성자**: Claude Code
- **기반 파일**: [rank/models.py](rank/models.py)
