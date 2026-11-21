import os
from pathlib import Path
import sys
import xml.etree.ElementTree as etree

from src.cli import CONFIG_STAGE, DIRECT_STAGE, IMAGE_STAGE, options
from src.graph import build_graph, reverse_dependencies, text_graph
from src.repository import NuGetRepository, TestRepository
from src.visualize import dot_graph, save_png


APPLICATION_ERRORS = (
    ValueError, OSError, KeyError, TypeError, etree.ParseError,
)


def get_repository(arguments):
    if arguments.test:
        return TestRepository(arguments.repository)
    return NuGetRepository(arguments.repository, arguments.framework)


def print_configuration(arguments):
    for key, value in vars(arguments).items():
        print(f'{key}={value}')


def print_direct(repository, root):
    dependencies = repository.dependencies(root)
    rows = '\n'.join(f'{name}: {value}' for name, value in dependencies)
    print(rows or 'Прямых зависимостей нет.')


def build_test_reverse_graph(repository, excluded):
    graph = {}
    for name in repository.packages:
        if excluded and excluded.casefold() in name.casefold():
            continue
        root = (name, repository.version)
        part = build_graph(repository, root, 1, excluded)
        for node, children in part.items():
            graph.setdefault(node, set()).update(children)
    return graph


def print_reverse(repository, root, arguments):
    if arguments.test:
        graph = build_test_reverse_graph(repository, arguments.filter)
    else:
        graph = build_forward(repository, root, arguments)
        print('Обратные зависимости только внутри исследованного графа, '
              'не всего NuGet.')
    result = reverse_dependencies(graph, arguments.reverse, arguments.max_depth)
    rows = '\n'.join(f'{name}@{version}' for name, version in result)
    print(rows or 'Обратных зависимостей нет.')


def build_forward(repository, root, arguments):
    return build_graph(repository, root, arguments.max_depth, arguments.filter)


def open_png(path):
    if sys.platform != 'win32':
        raise ValueError('--open поддерживается в Windows; PNG уже сохранён')
    os.startfile(str(path.resolve()))


def write_graph(graph, arguments):
    dot = dot_graph(graph)
    print(dot)
    dot_path = Path(arguments.output)
    dot_path.parent.mkdir(parents=True, exist_ok=True)
    dot_path.write_text(dot + '\n', encoding='utf-8')
    png_path = Path(arguments.png)
    save_png(graph, dot, png_path)
    print(f'PNG: {png_path.resolve()}')
    if arguments.open:
        open_png(png_path)
    if not arguments.test and arguments.framework is None:
        print('Примечание: объединены зависимости всех групп .NET из nuspec.',
              file=sys.stderr)


def main():
    arguments = options()
    if arguments.stage == CONFIG_STAGE:
        print_configuration(arguments)
        return
    repository = get_repository(arguments)
    root = repository.exact(arguments.package, arguments.version)
    if arguments.stage == DIRECT_STAGE:
        print_direct(repository, root)
        return
    if arguments.reverse:
        print_reverse(repository, root, arguments)
        return
    graph = build_forward(repository, root, arguments)
    if arguments.stage < IMAGE_STAGE:
        print(text_graph(graph))
    else:
        write_graph(graph, arguments)


if __name__ == '__main__':
    try:
        main()
    except APPLICATION_ERRORS as error:
        raise SystemExit(f'Ошибка: {error}') from error
