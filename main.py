"""Точка входа: выбор этапа демонстрации."""
from cli import options
from repository import NuGetRepository, TestRepository
from graph import build_graph, text_graph


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
    print(text_graph(graph))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(f'Ошибка: {error}') from error
