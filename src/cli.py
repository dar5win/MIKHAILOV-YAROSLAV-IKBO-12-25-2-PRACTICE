import argparse
from pathlib import Path
import re
from urllib.parse import urlparse


PACKAGE_NAME = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}')
EXACT_VERSION = re.compile(
    r'\d+(?:\.\d+){1,3}(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?'
)
NUGET_INDEX = 'https://api.nuget.org/v3/index.json'
TEST_VERSION = '1.0.0'
CONFIG_STAGE = 1
DIRECT_STAGE = 2
REVERSE_STAGE = 4
IMAGE_STAGE = 5


def add_source_options(parser):
    parser.add_argument(
        '--package', required=True, help='Имя пакета, например Serilog'
    )
    parser.add_argument(
        '--version', required=True, help='Точная версия, например 3.1.1'
    )
    parser.add_argument('--repository', default=NUGET_INDEX)
    parser.add_argument(
        '--test', action='store_true', help='Читать локальный JSON вместо сети'
    )


def add_graph_options(parser):
    parser.add_argument(
        '--max-depth', type=int, default=3,
        help='0 — только корень; 1 — прямые связи',
    )
    parser.add_argument(
        '--filter', default='', help='Исключить имена с этой подстрокой'
    )
    parser.add_argument(
        '--stage', type=int, choices=range(CONFIG_STAGE, IMAGE_STAGE + 1),
        default=IMAGE_STAGE,
    )
    parser.add_argument(
        '--framework', help='Группа nuspec; без опции объединяем все группы'
    )
    parser.add_argument(
        '--reverse', metavar='PACKAGE', help='Обратные зависимости пакета'
    )
    parser.add_argument(
        '--output', default='output/graph.dot', help='Куда сохранить DOT'
    )
    parser.add_argument(
        '--png', default='output/graph.png', help='Куда сохранить PNG'
    )
    parser.add_argument(
        '--open', action='store_true', help='Открыть PNG после генерации'
    )


def validate_package(parser, arguments):
    if not PACKAGE_NAME.fullmatch(arguments.package):
        parser.error('--package: допустимы латинские буквы, цифры, _, . и -')
    if not EXACT_VERSION.fullmatch(arguments.version):
        parser.error('--version: нужна точная версия, например 1.0.0')
    if arguments.framework is not None and not arguments.framework.strip():
        parser.error('--framework не должен быть пустым')


def validate_graph(parser, arguments):
    if arguments.stage == REVERSE_STAGE and arguments.reverse is None:
        parser.error('--stage 4: укажите пакет, например --reverse D')
    if arguments.reverse is not None:
        if not PACKAGE_NAME.fullmatch(arguments.reverse):
            parser.error('--reverse: некорректное имя пакета')
    if arguments.max_depth < 0:
        parser.error('--max-depth не может быть отрицательным')
    if arguments.filter:
        if not arguments.filter.strip():
            parser.error('--filter не должен состоять только из пробелов')
        if arguments.filter.casefold() in arguments.package.casefold():
            parser.error('--filter исключает корневой пакет; измените фильтр')


def validate_source(parser, arguments):
    if arguments.test:
        if not Path(arguments.repository).is_file():
            parser.error('--repository: файл тестового репозитория не найден')
        if not re.fullmatch('[A-Z]+', arguments.package):
            parser.error('--test: имена пакетов — большие латинские буквы')
        if arguments.version != TEST_VERSION:
            parser.error('--test: версия всех учебных пакетов 1.0.0')
        return
    address = urlparse(arguments.repository)
    if address.scheme not in ('http', 'https') or not address.netloc:
        parser.error('--repository: нужен http(s) URL индекса NuGet v3')


def options(argv=None):
    parser = argparse.ArgumentParser(
        description='Вариант 15: граф зависимостей NuGet'
    )
    add_source_options(parser)
    add_graph_options(parser)
    arguments = parser.parse_args(argv)
    validate_package(parser, arguments)
    validate_graph(parser, arguments)
    validate_source(parser, arguments)
    return arguments
