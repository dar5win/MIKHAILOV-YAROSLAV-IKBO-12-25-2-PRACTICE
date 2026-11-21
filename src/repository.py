from http.client import IncompleteRead, RemoteDisconnected
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as etree

from src.cli import TEST_VERSION


REQUEST_ATTEMPTS = 3
REQUEST_TIMEOUT = 20
NUGET_VERSION_PARTS = 4
RETRYABLE_HTTP_CODES = {408, 429, 500, 502, 503, 504}


def version_key(value):
    core, _, pre = value.split('+', 1)[0].partition('-')
    if not re.fullmatch(r'\d+(?:\.\d+){0,3}', core):
        raise ValueError(f'Неподдерживаемая версия: {value}')
    nums = tuple(int(part) for part in core.split('.'))
    nums += (0,) * (NUGET_VERSION_PARTS - len(nums))
    identifiers = tuple(
        (0, int(part)) if part.isdigit() else (1, part.lower())
        for part in pre.split('.')
    )
    return nums, not bool(pre), identifiers if pre else ()


def meets_lower_bound(version, bound, inclusive):
    if not bound:
        return True
    bound = version_key(bound)
    return version >= bound if inclusive else version > bound


def meets_upper_bound(version, bound, inclusive):
    if not bound:
        return True
    bound = version_key(bound)
    return version <= bound if inclusive else version < bound


def satisfies(version, requirement):
    requirement = requirement.strip()
    key = version_key(version)
    if not requirement or requirement == '(,)':
        return True
    if requirement[0] not in '[(':
        return key >= version_key(requirement)
    if requirement[-1:] not in '])':
        raise ValueError(f'Поврежденный диапазон версий: {requirement}')
    body = requirement[1:-1]
    if ',' not in body:
        if requirement[0] != '[' or requirement[-1] != ']':
            raise ValueError(f'Поврежденный диапазон версий: {requirement}')
        return key == version_key(body)
    low, high = (part.strip() for part in body.split(',', 1))
    return (
        meets_lower_bound(key, low, requirement[0] == '[')
        and meets_upper_bound(key, high, requirement[-1] == ']')
    )


def read_url(url):
    request = Request(url, headers={'User-Agent': 'Student-NuGet-Graph/1.0'})
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                return response.read()
        except (URLError, OSError, IncompleteRead, RemoteDisconnected) as error:
            retryable = (
                not isinstance(error, HTTPError)
                or error.code in RETRYABLE_HTTP_CODES
            )
            if not retryable or attempt == REQUEST_ATTEMPTS:
                message = f'Не удалось получить {url}: {error}'
                raise ValueError(message) from error


def find_package_base(index):
    for resource in index.get('resources', []):
        if 'PackageBaseAddress/3.0.0' in resource.get('@type', ''):
            return resource['@id'].rstrip('/') + '/'
    raise ValueError('В индексе нет ресурса PackageBaseAddress/3.0.0')


def select_framework_groups(container, framework, name):
    groups = container.findall('group')
    if framework is None or not groups:
        return groups
    selected = [
        group for group in groups
        if group.get('targetFramework', '').casefold() == framework.casefold()
    ]
    if selected:
        return selected
    available = ', '.join(
        group.get('targetFramework', '(общая)') for group in groups
    )
    raise ValueError(
        f'{name}: нет точной группы {framework}; есть: {available}'
    )


def read_nuspec_dependencies(xml, framework, name):
    tree = etree.fromstring(xml)
    for element in tree.iter():
        element.tag = element.tag.rsplit('}', 1)[-1]
    container = tree.find('./metadata/dependencies')
    if container is None:
        return []
    elements = container.findall('dependency')
    for group in select_framework_groups(container, framework, name):
        elements.extend(group.findall('dependency'))
    return list(dict.fromkeys(
        (element.attrib['id'], element.get('version', ''))
        for element in elements
    ))


class NuGetRepository:
    def __init__(self, url, framework=None):
        self.base = find_package_base(json.loads(read_url(url)))
        self.framework = framework
        self.version_cache = {}
        self.dependency_cache = {}

    def versions(self, name):
        name = name.lower()
        if name not in self.version_cache:
            resource = read_url(f'{self.base}{name}/index.json')
            self.version_cache[name] = json.loads(resource)['versions']
        return self.version_cache[name]

    def resolve(self, name, requirement):
        candidates = [
            version for version in self.versions(name)
            if ('-' in requirement or '-' not in version)
            and satisfies(version, requirement)
        ]
        if not candidates:
            raise ValueError(f'Нет подходящей версии {name}: {requirement}')
        return name.lower(), min(candidates, key=version_key)

    def exact(self, name, version):
        for candidate in self.versions(name):
            if version_key(candidate) == version_key(version):
                return name.lower(), candidate
        raise ValueError(f'Не найдена точная версия {name} {version}')

    def dependencies(self, node):
        if node not in self.dependency_cache:
            name, version = node
            address = f'{self.base}{name}/{version}/{name}.nuspec'
            self.dependency_cache[node] = read_nuspec_dependencies(
                read_url(address), self.framework, name,
            )
        return self.dependency_cache[node]


class TestRepository:
    version = TEST_VERSION

    def __init__(self, path):
        source = Path(path).read_text(encoding='utf-8-sig')
        self.packages = json.loads(source)['packages']
        if not isinstance(self.packages, dict) or not self.packages:
            raise ValueError('packages должен быть непустым объектом')
        for name, dependencies in self.packages.items():
            if not re.fullmatch('[A-Z]+', name):
                raise ValueError('Нужны имена из больших латинских букв')
            if not isinstance(dependencies, list):
                raise ValueError(f'{name}: зависимости должны быть списком')
            if any(not isinstance(dep, str) or dep not in self.packages
                   for dep in dependencies):
                raise ValueError(f'{name}: ссылка на неизвестный пакет')

    def exact(self, name, version):
        if name not in self.packages or version != self.version:
            raise ValueError(f'Не найден пакет {name} {version}')
        return name, version

    def resolve(self, name, requirement):
        return self.exact(name, self.version)

    def dependencies(self, node):
        return [(name, f'[{self.version}]') for name in self.packages[node[0]]]
