"""Точка входа; на первом этапе выводит проверенные настройки."""
from cli import options


def main():
    args = options()
    for key, value in vars(args).items():
        print(f'{key}={value}')


if __name__ == '__main__':
    main()
