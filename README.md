# Вариант 15 — граф зависимостей NuGet

## Как открыть граф

Дважды нажмите **START_DEMO.bat**. Программа создаст `output/graph.png`
и откроет картинку в стандартном приложении Windows для изображений.
Белый фон, скругленные блоки, корневой пакет выделен цветом, стрелки идут
слева направо. Браузер для демонстрации не используется.

Готовые примеры: `examples/A.png`, `examples/B.png`, `examples/C.png`.
Их можно открыть обычным двойным щелчком.

## Установка и запуск

Python 3.10+. Для изображения без установленного Graphviz нужна Pillow:

```powershell
.\python_run.bat -m pip install -r requirements.txt
```

На текущем компьютере Pillow уже есть в используемом Python.
На другом компьютере установите Python в PATH либо задайте PYTHON_EXE.
Если установлен Graphviz и команда dot доступна, PNG рисуется его движком.
В противном случае работает встроенная слоистая раскладка через Pillow.
Для получения зависимостей используются только стандартные средства Python;
Pillow используется исключительно для рисования картинки.

Откройте PowerShell в папке проекта (в адресной строке Проводника введите powershell).

```powershell
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --png output/graph.png
.\python_run.bat -m unittest discover -s tests -v
```

## Файлы

| Файл | Для чего |
|---|---|
| START_DEMO.bat | Построить учебный граф и открыть PNG |
| TESTS.bat | Автоматические проверки |
| REAL_EXAMPLES.bat | Три реальных пакета; нужен интернет для Python |
| python_run.bat | Вспомогательный выбор Python |
| main.py | Управляет выполнением этапов |
| cli.py | Настройки командной строки и их проверка |
| repository.py | HTTP-запросы, чтение XML NuGet и учебного JSON |
| graph.py | DFS со стеком, глубина, фильтрация, обратные связи |
| visualize.py | Текст Graphviz DOT и картинка PNG |
| requirements.txt | Зависимость Pillow для рисования без Graphviz |
| data | Учебные репозитории |
| examples | Три готовые PNG-схемы и соответствующие DOT-файлы |
| output | Результаты запусков |
| GUIDE_RU.md | Понятное объяснение и подготовка к защите |

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
| --help | Справка |

Этапы 1–4 печатают текст; этап 5 печатает DOT, сохраняет DOT и PNG.
Сам main.py только сохраняет изображение; START_DEMO.bat также открывает его.
HTML-вывод заменен PNG: старую опцию --html использовать не нужно.

## Показ этапов

```powershell
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 1
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 2
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 3 --max-depth 3
.\python_run.bat main.py --test --repository data/branch.json --package A --version 1.0.0 --stage 4 --reverse D --max-depth 3
.\python_run.bat main.py --test --repository data/cycle.json --package A --version 1.0.0 --max-depth 10 --png output/cycle.png
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

Офлайн-тесты и генерация PNG проверены. Сетевой запрос Python в текущей среде
блокируется Windows 10013, поэтому реальный запуск API не подтвержден.
Установленного .NET SDK здесь нет; фактическое сравнение с dotnet не выполнено.
Для реального прогона используйте REAL_EXAMPLES.bat при доступном интернете.

Программа объединяет группы зависимостей всех платформ .NET, если не задан
точный --framework. Это может отличаться от зависимостей конкретного проекта.
Полного разрешения глобальных конфликтов версий и совместимости фреймворков нет.
Поддерживаются точные версии и обычные интервалы NuGet, не плавающие версии.

Независимое сравнение (нужен .NET SDK):

```powershell
dotnet new console -n NuGetComparison -f net8.0
cd NuGetComparison
dotnet add package Microsoft.Extensions.Logging --version 8.0.0
dotnet list package --include-transitive
```

Сравните список с вершинами графа. В Visual Studio можно также раскрыть
Solution Explorer -> Dependencies -> Packages. Зафиксируйте реальные отличия.
Наш анализатор не вызывает dotnet: эти команды нужны только для сравнения.

## Git и сдача

Исходное задание: PDF «ИКБО-12-25 (1).pdf», стр. 50–52.
Нужны README, история этапов и публичный Git-репозиторий; Word-отчет не нужен.
История локальных этапов сохранена. Автор коммитов технический:
Student <student@localhost>. Публикация и защита на занятии не выполнены.
Создайте пустой публичный репозиторий и подставьте свой адрес:

```powershell
git remote add origin https://github.com/YOUR_LOGIN/YOUR_REPO.git
git push -u origin master
```

ZIP включает .git, чтобы сохранить историю.

## Источники

- https://learn.microsoft.com/nuget/api/package-base-address-resource
- https://learn.microsoft.com/nuget/reference/nuspec
- https://learn.microsoft.com/nuget/concepts/package-versioning
