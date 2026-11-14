"""Точка входа: выбор этапа демонстрации."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from visualize import dot_graph, save_html
from cli import options
from repository import NuGetRepository, TestRepository
from graph import build_graph, text_graph, reverse_dependencies


def main():
    args = options()
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f'{key}={value}')
        return
    repository = TestRepository(args.repository) if args.test else NuGetRepository(args.repository, args.framework)
    root = repository.exact(args.package, args.version)
    if args.stage == 2:
        deps = repository.dependencies(root)
        print('\n'.join(f'{name}: {requirement}' for name, requirement in deps) or 'Прямых зависимостей нет.')
        return
    graph = build_graph(repository, root, args.max_depth, args.filter)
    if args.reverse:
        if args.test:
            graph = {}
            for name in repository.packages:
                if args.filter and args.filter.casefold() in name.casefold():
                    continue
                part = build_graph(repository, (name, '1.0.0'), 1, args.filter)
                for node, children in part.items():
                    graph.setdefault(node, set()).update(children)
        else:
            print('Обратные зависимости только внутри исследованного графа, не всего NuGet.')
        result = reverse_dependencies(graph, args.reverse, args.max_depth)
        print('\n'.join(f'{n}@{v}' for n, v in result) or 'Обратных зависимостей нет.')
        return
    if args.stage < 5:
        print(text_graph(graph))
        return
    dot = dot_graph(graph)
    print(dot)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(dot + '\n', encoding='utf-8')
    if args.html:
        save_html(graph, dot, args.html)
    if not args.test and args.framework is None:
        print('Примечание: объединены зависимости всех групп .NET из nuspec.', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, ET.ParseError) as error:
        raise SystemExit(f'Ошибка: {error}') from error


