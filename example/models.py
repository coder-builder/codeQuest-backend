from django.db import models

# Create your models here.

# 데이터베이스를 만드는 곳입니다.
# 이거 입력하고 아래
# python manage.py makemigrations
# python manage.py migrate
# 여기까지 터미널에 입력 후 실행하면 자체적으로 데이터베이스에 테이블이 생성됩니다!
#  migrate = 테이블 자동 생성 ✅ CREATE TABLE 직접 안써도 됨 ✅ models.py만 작성하면 끝!

# 개꿀인 것은 컬럼 수정,삭제하고 싶으면 아래의 테이블에서 해당값을 수정하고
# python manage.py makemigrations
# python manage.py migrate 이거 다시 실행하면 자체적으로 테이블이 바뀝니다.
# ⚠️⚠️⚠️ !!주의사항!!! ⚠️⚠️⚠️
# 컬럼 삭제하면 그냥 기존의 데이터는 물어보지도 않고 바로 삭제되므로 백업 받으신 후 삭제해주세요

# 백업 방법
"""class User(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()  # 기존
    age_backup = models.IntegerField(null=True)  # ️⚠️️⚠️백업용 테이블을 만든다!️⚠️️⚠️
    
    python manage.py makemigrations
    python manage.py migrate 터미널에 쳐서 반영!
    
    python manage.py shell 터미널에 쳐서 쉘모드 진입!
    
    from api.models import User
    for user in User.objects.all():
    user.age_backup = user.age
    user.save()
    
    후 기존 컬럼 삭제!
    
"""

class exampleUser(models.Model):
    """사용자 모델"""
    name = models.CharField(max_length=100, verbose_name='이름')
    email = models.EmailField(unique=True, verbose_name='이메일')
    age = models.IntegerField(verbose_name='나이')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        db_table = 'exampleUser' # 디비에 삽입될 테이블 이름!
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return f"{self.name} ({self.email})"