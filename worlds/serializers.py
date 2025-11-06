# worlds/serializers.py

from rest_framework import serializers
from .models import World, Stage, UserWorld, UserStageProgress


class WorldSerializer(serializers.ModelSerializer):
    """
    월드 Serializer

    기능:
    - 월드 기본 정보 직렬화
    - 스테이지 개수 계산

    사용처:
    - GET /api/worlds/ (월드 목록)
    - POST /api/worlds/ (월드 생성)
    """

    # 스테이지 개수 (계산 필드)
    stage_count = serializers.SerializerMethodField()

    class Meta:
        model = World
        fields = [
            'id',               # 월드 ID
            'title',            # 제목 (예: Python, Java)
            'description',      # 설명
            'icon',             # 아이콘 (이모지)
            'is_locked',        # 전역 잠금 여부
            'stage_count',      # 스테이지 개수 (계산)
            'created_at',       # 생성일
            'updated_at'        # 수정일
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_stage_count(self, obj):
        """
        스테이지 개수 계산

        Args:
            obj (World)         : 월드 객체
            obj.stages          : 월드 객체에 있는 stages
            obj.stages.count()  : 월드객체에 있는 stages의 갯수

        Returns:
            int: 스테이지 개수
        """
        return obj.stages.count()


class StageSerializer(serializers.ModelSerializer):
    """
    스테이지 Serializer

    기능:
    - 스테이지 기본 정보 직렬화
    - 월드 정보 포함 (world_title, world_icon)
    - 레슨 개수 계산

    사용처:
    - GET /api/stages/ (스테이지 목록)
    - POST /api/stages/ (스테이지 생성)
    """

    # 월드 정보 (읽기 전용)
    world_title = serializers.CharField(source='world.title', read_only=True)
    world_icon = serializers.CharField(source='world.icon', read_only=True)

    # 레슨 개수 (계산 필드)
    lesson_count = serializers.SerializerMethodField()

    class Meta:
        model = Stage
        fields = [
            'id',  # 스테이지 ID
            'world',  # 월드 ID (FK)
            'world_title',  # 월드 제목 (읽기 전용)
            'world_icon',  # 월드 아이콘 (읽기 전용)
            'title',  # 스테이지 제목
            'description',  # 스테이지 설명
            'order',  # 순서
            'lesson_count',  # 레슨 개수 (계산)
            'created_at',  # 생성일
            'updated_at'  # 수정일
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_lesson_count(self, obj):
        """
        레슨 개수 계산

        Args:
            obj (Stage): 스테이지 객체

        Returns:
            int: 레슨 개수
        """
        return obj.lessons.count()


class StageDetailSerializer(StageSerializer):
    """
    스테이지 상세 Serializer (잠금 상태 포함)

    기능:
    - StageSerializer의 모든 필드
    - 사용자별 잠금 해제 여부 추가

    사용처:
    - GET /api/worlds/{id}/stages/ (월드별 스테이지 목록, 잠금 상태 포함)
    - GET /api/stages/{id}/ (스테이지 상세)

    주의사항:
    - context에 request가 필요함
    - 인증된 사용자만 잠금 상태 확인 가능
    """

    # 사용자별 잠금 해제 여부 (계산 필드)
    is_unlocked = serializers.SerializerMethodField()

    class Meta(StageSerializer.Meta):
        fields = StageSerializer.Meta.fields + ['is_unlocked']

    def get_is_unlocked(self, obj):
        """
        사용자별 잠금 해제 여부 확인

        Args:
            obj (Stage): 스테이지 객체

        Returns:
            bool: True(잠금 해제), False(잠김)

        로직:
        1. request.user 확인
        2. 인증된 사용자면 is_unlocked_for_user() 호출
        3. 미인증 사용자는 False 반환
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_unlocked_for_user(request.user)
        return False


class UserWorldSerializer(serializers.ModelSerializer):
    """
    사용자 월드 진행 상황 Serializer

    기능:
    - 사용자의 월드 학습 진행 상황 직렬화
    - 월드 기본 정보 포함
    - 진행률 계산 (property 사용)

    사용처:
    - GET /api/user/worlds/ (내 월드 목록)
    - POST /api/worlds/{id}/start/ (월드 시작)

    주의사항:
    - total_stage, progress_percentage는 모델의 @property 사용
    - started_at은 created_at의 별칭
    """

    # 월드 기본 정보 (읽기 전용)
    world_title = serializers.CharField(source='world.title', read_only=True)
    world_icon = serializers.CharField(source='world.icon', read_only=True)
    world_description = serializers.CharField(source='world.description', read_only=True)

    # 진행 상황 (모델 property 사용)
    total_stage = serializers.IntegerField(read_only=True)  # 전체 스테이지 수
    progress_percentage = serializers.IntegerField(read_only=True)  # 진행률 (%)
    started_at = serializers.DateTimeField(read_only=True)  # 시작 시간 (created_at 별칭)

    class Meta:
        model = UserWorld
        fields = [
            'id',  # UserWorld ID
            'world',  # 월드 ID (FK)
            'world_title',  # 월드 제목 (읽기)
            'world_icon',  # 월드 아이콘 (읽기)
            'world_description',  # 월드 설명 (읽기)
            'is_unlocked',  # 잠금 해제 여부
            'completed_stage',  # 완료한 스테이지 수
            'total_stage',  # 전체 스테이지 수 (property)
            'progress_percentage',  # 진행률 % (property)
            'last_studied_at',  # 마지막 공부 시간
            'started_at',  # 시작 시간 (property)
            'created_at',  # 생성일
            'updated_at'  # 수정일
        ]
        read_only_fields = [
            'completed_stage',  # update_progress()로만 업데이트
            'last_studied_at',  # touch()로만 업데이트
            'created_at',
            'updated_at'
        ]


class UserStageProgressSerializer(serializers.ModelSerializer):
    """
    사용자 스테이지 진행 상황 Serializer

    기능:
    - 사용자의 스테이지별 완료 상황 직렬화
    - 스테이지 및 월드 정보 포함

    사용처:
    - GET /api/user/stages/progress/ (내 스테이지 진행 상황)
    - 스테이지 완료 처리 시
    """

    # 스테이지 정보 (읽기 전용)
    stage_title = serializers.CharField(source='stage.title', read_only=True)
    stage_order = serializers.IntegerField(source='stage.order', read_only=True)
    world_title = serializers.CharField(source='stage.world.title', read_only=True)

    class Meta:
        model = UserStageProgress
        fields = [
            'id',  # UserStageProgress ID
            'user',  # 사용자 ID (FK)
            'stage',  # 스테이지 ID (FK)
            'stage_title',  # 스테이지 제목 (읽기)
            'stage_order',  # 스테이지 순서 (읽기)
            'world_title',  # 월드 제목 (읽기)
            'is_completed',  # 완료 여부
            'completed_at',  # 완료 일시
            'created_at',  # 생성일
            'updated_at'  # 수정일
        ]
        read_only_fields = [
            'is_completed',  # 자동 업데이트
            'completed_at',  # 자동 업데이트
            'created_at',
            'updated_at'
        ]


class WorldWithStagesSerializer(WorldSerializer):
    """
    월드 + 스테이지 목록 Serializer

    기능:
    - WorldSerializer의 모든 필드
    - 스테이지 목록 포함 (nested)

    사용처:
    - GET /api/worlds/{id}/ (월드 상세, 스테이지 포함)
    - 월드 선택 화면

    주의사항:
    - StageDetailSerializer 사용 (잠금 상태 포함)
    - context에 request 전달 필요
    """

    # 스테이지 목록 (nested, 읽기 전용)
    stages = StageDetailSerializer(many=True, read_only=True)

    class Meta(WorldSerializer.Meta):
        fields = WorldSerializer.Meta.fields + ['stages']


class UserWorldDetailSerializer(UserWorldSerializer):
    """
    사용자 월드 상세 Serializer (스테이지 진행 상황 포함)

    기능:
    - UserWorldSerializer의 모든 필드
    - 월드 상세 정보 (nested)
    - 스테이지별 진행 상황 (계산)

    사용처:
    - GET /api/user/worlds/{id}/ (내 월드 상세)
    - 월드 학습 화면 (스테이지 목록 + 진행 상황)

    반환 데이터 예시:
    {
        "id": 1,
        "world": {...},
        "progress_percentage": 60,
        "stage_progress": [
            {
                "stage_id": 1,
                "title": "변수와 출력",
                "order": 1,
                "is_unlocked": true,
                "is_completed": true,
                "completed_at": "2025-11-04T10:00:00Z"
            },
            {
                "stage_id": 2,
                "title": "조건문",
                "order": 2,
                "is_unlocked": true,
                "is_completed": false,
                "completed_at": null
            },
            ...
        ]
    }
    """

    # 월드 상세 정보 (nested, 읽기 전용)
    world = WorldSerializer(read_only=True)

    # 스테이지별 진행 상황 (계산 필드)
    stage_progress = serializers.SerializerMethodField()

    class Meta(UserWorldSerializer.Meta):
        fields = UserWorldSerializer.Meta.fields + ['stage_progress']

    def get_stage_progress(self, obj):
        """
        스테이지별 진행 상황 계산

        Args:
            obj (UserWorld): 사용자 월드 객체

        Returns:
            list: 스테이지별 상태 목록

        로직:
        1. 월드의 모든 스테이지 조회
        2. 각 스테이지마다:
           - is_unlocked_for_user() 호출 (잠금 상태)
           - UserStageProgress 조회 (완료 상태)
        3. 결과를 리스트로 반환

        주의사항:
        - N+1 쿼리 발생 가능 (스테이지 개수만큼)
        - 스테이지가 많으면 성능 이슈 가능
        """
        stages = obj.world.stages.all()
        user = obj.user

        result = []
        for stage in stages:
            # 1. 잠금 상태 확인
            is_unlocked = stage.is_unlocked_for_user(user)

            # 2. 완료 상태 확인
            try:
                progress = UserStageProgress.objects.get(
                    user=user,
                    stage=stage
                )
                is_completed = progress.is_completed
                completed_at = progress.completed_at
            except UserStageProgress.DoesNotExist:
                is_completed = False
                completed_at = None

            # 3. 결과 추가
            result.append({
                'stage_id': stage.id,
                'title': stage.title,
                'order': stage.order,
                'is_unlocked': is_unlocked,  # 이전 스테이지 완료 여부
                'is_completed': is_completed,  # 현재 스테이지 완료 여부
                'completed_at': completed_at  # 완료 시간
            })

        return result