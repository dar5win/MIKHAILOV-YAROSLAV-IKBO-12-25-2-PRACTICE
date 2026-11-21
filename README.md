# Вариант 15 — граф зависимостей NuGet

## Запуск в VS Code

1. Открой папку проекта, в которой лежит `main.py`.
2. Выбери свой Python 3.10 или новее через `Ctrl+Shift+P` → `Python: Select Interpreter`. Для кнопки запуска нужны расширения Python и Python Debugger.
3. Если выбранный Python ещё не содержит Pillow и в системе нет Graphviz, установи зависимости в новом терминале VS Code:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. В панели «Запуск и отладка» (`Ctrl+Shift+D`) выбери «Показать граф зависимостей» и нажми ▶ или `F5`.

Тот же пример можно запустить из терминала:

```powershell
python main.py --test --repository data/branch.json --package A --version 1.0.0 --open
```

При каждом запуске программа заново строит граф из данных и перезаписывает PNG.
Опция `--open` открывает только что созданный PNG в просмотрщике Windows.
Для рисования используется установленный Graphviz, а если его нет — Pillow.

Проверки: `python -m unittest discover -s tests -v`.

## Настройки

| Опция | Значение |
|---|---|
| --package | Имя корневого пакета, обязательна |
| --version | Точная версия корня, обязательна |
| --repository | По умолчанию https://api.nuget.org/v3/index.json; с --test путь к JSON |
| --test | Учебный репозиторий вместо интернета |
| --max-depth | Число переходов от корня; по умолчанию 3 |
| --filter | Исключить имена с подстрокой, без учета регистра |
| --stage | Этап 1–5, по умолчанию 5 |
| --reverse | Имя пакета для поиска обратных зависимостей |
| --framework | Точное имя группы nuspec; без опции объединяются все группы |
| --output | DOT-файл, по умолчанию output/graph.dot |
| --png | PNG-файл, по умолчанию output/graph.png |
| --open | Открыть PNG после новой генерации |
| --help | Справка |

Этапы 1–4 печатают текст. Этап 4 требует `--reverse`. Этап 5 печатает DOT, сохраняет DOT и PNG.
Открой PNG командой `Invoke-Item .\output\graph.png`.

## Показ этапов

```powershell
python main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 1
python main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 2
python main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 3 --max-depth 3
python main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 4 --reverse D --max-depth 3
python main.py --test --repository data/cycle.json --package A --version 1.0.0 --stage 4 --reverse A
python main.py --test --repository data/empty.json --package A --version 1.0.0 --stage 4 --reverse A
python main.py --test --repository data/cycle.json --package A --version 1.0.0 --max-depth 10 --png output/cycle.png
```

## Данные и алгоритм

Учебный JSON: `{"packages":{"A":["B","C"],"B":["D"],"C":["D","E"],"D":[],"E":[],"F":["D"]}}`.
Все учебные версии 1.0.0; имена — большие латинские буквы.
branch.json — ветвление, cycle.json — цикл, empty.json — пакет без зависимостей.

В реальном режиме программа читает индекс NuGet v3, находит PackageBaseAddress,
загружает список версий и .nuspec. XML содержит имена и диапазоны версий
зависимостей. Для каждого ребра выбирается минимальная подходящая версия.
Далее выполняется DFS без рекурсии: непосещенные вершины хранятся в стеке.
Запоминается наименьшая глубина посещения: это обрабатывает циклы и
позволяет раскрывать вершину после нахождения более короткого пути.

Вершина — имя и версия; A -> B означает, что A нужен B.
Глубина 0 — один корень, глубина 1 — прямые зависимости.
На пределе глубины вершины не раскрываются: это не признак отсутствия зависимостей.
Фильтр исключает вершину и путь через нее. Обратный поиск разворачивает ребра
и снова применяет DFS. В учебном режиме он рассматривает весь файл,
в реальном — только уже исследованную часть репозитория.

## Проверка и ограничения

Офлайн-тесты и генерация PNG проверены. На NuGet.org проверено получение
прямых зависимостей Microsoft.Extensions.Logging 8.0.0 и построение графа
Humanizer.Core 2.14.1 с глубиной 1.
Для реального запуска нужен интернет для Python:

```powershell
python main.py --package Serilog --version 3.1.1 --max-depth 2 --output output/Serilog.dot --png output/Serilog.png
python main.py --package Humanizer.Core --version 2.14.1 --max-depth 2 --output output/Humanizer.dot --png output/Humanizer.png
python main.py --package Microsoft.Extensions.Logging --version 8.0.0 --max-depth 2 --output output/Logging.dot --png output/Logging.png
```


Программа объединяет группы зависимостей всех платформ .NET, если не задан
точный --framework. Это может отличаться от зависимостей конкретного проекта.
Полного разрешения глобальных конфликтов версий и совместимости фреймворков нет.
Поддерживаются точные версии и обычные интервалы NuGet, не плавающие версии.

## Этап 5. Сравнение с NuGet Gallery

Прямые рёбра сверены с вкладкой **Dependencies** официального каталога NuGet.
Целевой фреймворк определяет, какую группу зависимостей использует проект.
Для наглядности в таблице сопоставлены результат без `--framework` и конкретная группа каталога.

| Пакет | Наш анализатор без `--framework` | NuGet Gallery для указанного фреймворка | Причина разницы |
|---|---|---|---|
| [Microsoft.Extensions.Logging 8.0.0](https://www.nuget.org/packages/Microsoft.Extensions.Logging/8.0.0#dependencies-body-tab) | 6 прямых зависимостей | Для `net8.0` есть 3: `Microsoft.Extensions.DependencyInjection`, `Microsoft.Extensions.Logging.Abstractions`, `Microsoft.Extensions.Options` | Другие группы добавляют `Microsoft.Bcl.AsyncInterfaces`, `System.Diagnostics.DiagnosticSource` и `System.ValueTuple`. |
| [Humanizer.Core 2.14.1](https://www.nuget.org/packages/Humanizer.Core/2.14.1#dependencies-body-tab) | 1 прямая зависимость, `NETStandard.Library` | Для `net6.0` зависимостей нет | `NETStandard.Library` относится к группе `.NETStandard 1.0`. |

Объединение групп NuGet Gallery совпадает с результатом анализатора без `--framework` для этих прямых зависимостей. С параметром `--framework net6.0` программа построила для Humanizer.Core граф из одной вершины, что совпадает с результатом в каталоге.
Также проверен [Serilog 3.1.1](https://www.nuget.org/packages/Serilog/3.1.1#dependencies-body-tab) с `--framework net7.0`. Анализатор построил граф из одной вершины. Для `net7.0` каталог тоже не показывает зависимостей.
Для сравнения транзитивных зависимостей конкретного проекта можно дополнительно использовать .NET SDK:

```powershell
dotnet new console -n NuGetComparison -f net8.0
cd NuGetComparison
dotnet add package Microsoft.Extensions.Logging --version 8.0.0
dotnet list package --include-transitive
```

Список можно сопоставить с вершинами графа, сформированного с `--framework net8.0`.
Штатный NuGet сам выбирает совместимые группы и разрешает версии для всего проекта, поэтому такое сравнение включает и различия в алгоритме разрешения.

## Git и сдача

Исходное задание: PDF «ИКБО-12-25 (1).pdf», стр. 50–52.
Нужны README, история этапов и публичный Git-репозиторий; Word-отчет не нужен.
История пяти этапов доступна в ветке `master`.

## Источники

- https://learn.microsoft.com/nuget/api/package-base-address-resource
- https://learn.microsoft.com/nuget/reference/nuspec
- https://learn.microsoft.com/nuget/concepts/package-versioning
