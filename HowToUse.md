# 사용방법입니다.

유저라는 폴더를 만들고싶으면 
python manage.py startapp user
위의 코드를 치면 자동적으로 필요한 폴더가 생성됩니다.

example 폴더를 보시면 각 파일의 기능에 대해서 설명하겠습니다.

기본 구조 
-migrations
-__init__.py
admin.py
apps.py
models.py ->
test.py
views.py

이런식으로 생성이 되는데
여기에 urls.py와 serializers 새로만들기하셔서 만듭니다. 각 파일에 해당 기능을 명시해두었습니다.

