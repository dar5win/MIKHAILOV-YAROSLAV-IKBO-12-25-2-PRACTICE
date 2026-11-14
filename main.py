"""Точка входа; на первом этапе выводит проверенные настройки."""
from cli import options
from repository import NuGetRepository, TestRepository


def main():
    args = options()
    if args.stage == 1:
        for key, value in vars(args).items():
            print(f'{key}={value}')
        return
    repository = TestRepository(args.repository) if args.test else NuGetRepository(args.repository, args.framework)
    root = repository.exact(args.package, args.version)
    for name, requirement in repository.dependencies(root):
        print(f'{name}: {requirement}')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(f'Ошибка: {error}') from error
