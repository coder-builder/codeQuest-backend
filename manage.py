#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


# main 메서드 생성 이걸 실행함(장고 코어를 실행함 )
def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

# manage.py는 자바의 main 하나만 실행하는 것처럼 이녀석을 실행함
if __name__ == '__main__':
    main()
