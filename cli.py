"""Этап 1: настройки командной строки и проверка ввода."""
import argparse
from pathlib import Path
import re
from urllib.parse import urlparse


def options(argv=None):
    p = argparse.ArgumentParser(description='Вариант 15: граф зависимостей NuGet')
    p.add_argument('--package', required=True, help='Имя пакета, например Serilog')
    p.add_argument('--version', required=True, help='Точная версия, например 3.1.1')
    p.add_argument('--repository', default='https://api.nuget.org/v3/index.json')
    p.add_argument('--test', action='store_true', help='Читать локальный JSON вместо сети')
    p.add_argument('--max-depth', type=int, default=3, help='0 — только корень; 1 — прямые связи')
    p.add_argument('--filter', default='', help='Исключить имена с этой подстрокой')
    p.add_argument('--stage', type=int, choices=range(1, 6), default=5)
    args = p.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}', args.package):
        p.error('--package: допустимы латинские буквы, цифры, _, . и -')
    if not re.fullmatch(r'\d+(?:\.\d+){1,3}(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?', args.version):
        p.error('--version: нужна точная версия, например 1.0.0')
    if args.max_depth < 0:
        p.error('--max-depth не может быть отрицательным')
    if args.filter and not args.filter.strip():
        p.error('--filter не должен состоять только из пробелов')
    if args.filter and args.filter.casefold() in args.package.casefold():
        p.error('--filter исключает сам корневой пакет; измените фильтр')
    if args.test:
        if not Path(args.repository).is_file():
            p.error('--repository: файл тестового репозитория не найден')
        if not re.fullmatch('[A-Z]+', args.package):
            p.error('--test: имена пакетов — большие латинские буквы')
        if args.version != '1.0.0':
            p.error('--test: в учебном репозитории версия всех пакетов 1.0.0')
    else:
        u = urlparse(args.repository)
        if u.scheme not in ('http', 'https') or not u.netloc:
            p.error('--repository: нужен http(s) URL индекса NuGet v3')
    return args
