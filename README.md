# Вариант 15 — граф зависимостей NuGet

Это работа по PDF «ИКБО-12-25 (1).pdf», стр. 50–52. Эмулятор терминала
из соседней папки относится к другому заданию и здесь не используется.
Язык Python 3.10+, только стандартная библиотека. Сборка и pip не нужны.

## Запуск

Двойной щелчок START_DEMO.bat — учебная схема, без интернета.
Двойной щелчок TESTS.bat — тесты.
REAL_EXAMPLES.bat — три настоящих пакета; нужен доступ Python к api.nuget.org.
На другом компьютере нужен установленный Python в PATH либо переменная
PYTHON_EXE с абсолютным путем к python.exe.

Открыть терминал в этой папке: в Проводнике нажать адресную строку,
ввести powershell и Enter. Все команды ниже выполняются именно здесь.

```powershell
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 1
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 2
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 3 --max-depth 3
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 4 --reverse D --max-depth 3
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 5 --html output/branch.html
.\python_run.bat -m unittest discover -s tests -v
```

Можно вместо `.\python_run.bat` писать `python`, если он доступен.

## Все настройки

| Опция | Что означает |
|---|---|
| --package | Корневой пакет, обязательна |
| --version | Точная версия корня, обязательна |
| --repository | Индекс NuGet v3; по умолчанию https://api.nuget.org/v3/index.json; в тестовом режиме путь JSON |
| --test | Читать локальный учебный репозиторий |
| --max-depth | Максимальное число переходов от корня, по умолчанию 3 |
| --filter | Не учитывать пакеты с подстрокой в имени, без учета регистра |
| --stage | Режим демонстрации 1–5; по умолчанию 5 |
| --reverse | Показать, кто прямо или косвенно зависит от указанного пакета |
| --framework | Необязательно: точное имя группы из nuspec; без опции объединяются все группы |
| --output | Путь сохранения DOT, по умолчанию output/graph.dot |
| --html | Необязательный путь сохранения HTML-картинки |
| --help | Справка |

Строковые значения с пробелами заключать в двойные кавычки.
В режиме --test все версии 1.0.0; имена — большие латинские буквы.
Ошибки параметров дают код 2; ошибки чтения или сети — ненулевой код.

## Что делает каждый файл

- cli.py — проверяет настройки.
- repository.py — получает индекс, список версий и .nuspec по HTTP; разбирает JSON и XML.
- graph.py — строит граф нерекурсивным DFS и ищет обратные связи.
- visualize.py — формирует DOT и дополнительную автономную HTML-схему.
- main.py — связывает этапы.
- data/ — маленькие репозитории, понятные без интернета.
- tests/ — автоматические проверки.
- GUIDE_RU.md — объяснение с нуля и сценарий защиты.

## Как работает реальный NuGet

1. Читается индекс репозитория и адрес ресурса PackageBaseAddress/3.0.0.
2. Читается список доступных версий пакета.
3. Для точной версии корня скачивается .nuspec.
4. Из XML берутся dependency: id и диапазон version.
5. Для каждого ребра выбирается минимальная подходящая версия.
6. С помощью стека строятся оставшиеся связи до нужной глубины.

Прямые зависимости на этапе 2 выводятся с исходными диапазонами.
Список версий и прочитанные описания кешируются на время одного запуска.
Ребро A -> B означает «A зависит от B». Вершина — имя И версия.
Глубина 0 оставляет только корень; глубина 1 — только прямые зависимости.
Фильтрация убирает и вершину, и путь через нее.
Вершина, достигнутая на пределе глубины, не обязательно лишена зависимостей.

Не используется готовая библиотека получения зависимостей: только urllib,
json, xml.etree и собственный обход. NuGet/dotnet не вызываются программой.

## Формат учебных данных

```json
{"packages":{"A":["B","C"],"B":["D"],"C":["D","E"],"D":[],"E":[],"F":["D"]}}
```

A нужны B и C; B нужен D; C нужны D и E. F тоже нужен D,
но из A пакет F недостижим. Поэтому F появляется только при поиске
обратных зависимостей D по всему учебному репозиторию.
branch.json — ветвление и общая зависимость; cycle.json — цикл; empty.json — пустой список.

## Graphviz и три примера

Этап 5 печатает DOT на экран и сохраняет .dot.
Картинка HTML — дополнительный простой SVG-просмотр, а не движок Graphviz.
При установленном Graphviz можно получить его собственную раскладку:

```powershell
dot -Tsvg output/graph.dot -o output/graph.svg
```

Учебные готовые примеры находятся в examples/A.html, B.html, C.html и
соответствующих .dot. Это результаты трех запусков на пакетах A, B и C.

Три команды для настоящего NuGet:

```powershell
.\python_run.bat main.py --package Serilog --version 3.1.1 --max-depth 2 --output output/Serilog.dot --html output/Serilog.html
.\python_run.bat main.py --package Humanizer.Core --version 2.14.1 --max-depth 2 --output output/Humanizer.dot --html output/Humanizer.html
.\python_run.bat main.py --package Microsoft.Extensions.Logging --version 8.0.0 --max-depth 2 --output output/Logging.dot --html output/Logging.html
```

## Ограничения и проверка перед окончательной сдачей

Офлайн-тесты пройдены. Из среды выполнения Python сетевой запрос заблокирован
ошибкой Windows 10013; живой прогон реальных пакетов здесь НЕ подтвержден.
На компьютере есть dotnet host, но нет .NET SDK. Поэтому фактическое сравнение
со штатным dotnet также еще НЕ выполнено. Не выдавайте это за выполненную проверку.

Для сравнения нужен отдельный временный .NET-проект и SDK:

```powershell
dotnet new console -n NuGetComparison -f net8.0
cd NuGetComparison
dotnet add package Microsoft.Extensions.Logging --version 8.0.0
dotnet list package --include-transitive
```

Табличный вывод dotnet сравнивается с вершинами графа. Для сравнения
наглядного дерева в Visual Studio: Solution Explorer -> Dependencies ->
Packages -> раскрывать вложенные зависимости. Записать фактические отличия.
Эти команды — только независимая проверка, они не входят в код анализатора.

Почему возможны различия: наш режим по умолчанию объединяет группы всех .NET;
dotnet выбирает совместимую группу для конкретного проекта. Наш анализатор
выбирает версию отдельно для каждого ребра, не решает глобальные конфликты
версий всего проекта. Поддерживаются обычные точные версии и интервалы
NuGet, не плавающие версии. --framework выбирает точное имя группы, а не
полную совместимость фреймворков. Обратный поиск в реальном режиме ограничен
исследованным графом; в тестовом — всем файлом репозитория.

## Git и сдача

В локальной истории есть отдельные коммиты этапов. Автор пока технический:
Student <student@localhost>. Эти коммиты созданы при подготовке программы,
они не означают, что этапы уже защищены на семинаре.
Публикация на публичный git-сервис еще не выполнена.

Создать пустой публичный репозиторий в своем аккаунте. Затем:

```powershell
git remote add origin https://github.com/YOUR_LOGIN/YOUR_REPO.git
git push -u origin master
```

YOUR_LOGIN и YOUR_REPO заменить своими. Если GitHub недоступен,
подойдет другой публичный git-сервис из методички. ZIP содержит .git,
чтобы история этапов сохранялась после распаковки.

## Официальные источники

- https://learn.microsoft.com/nuget/api/package-base-address-resource
- https://learn.microsoft.com/nuget/reference/nuspec
- https://learn.microsoft.com/nuget/concepts/package-versioning
- https://www.nuget.org/packages/Serilog/3.1.1
- https://www.nuget.org/packages/Humanizer.Core/2.14.1
- https://www.nuget.org/packages/Microsoft.Extensions.Logging/8.0.0
