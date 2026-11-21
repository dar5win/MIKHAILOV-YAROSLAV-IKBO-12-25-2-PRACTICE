import json
import re
from http.client import IncompleteRead, RemoteDisconnected
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import xml.etree.ElementTree as ET


def version_key(value):

    core, _, pre = value.split('+', 1)[0].partition('-')
    if not re.fullmatch(r'\d+(?:\.\d+){0,3}', core):
        raise ValueError(f'Неподдерживаемая версия: {value}')
    nums = tuple(int(x) for x in core.split('.'))
    nums += (0,) * (4 - len(nums))
    identifiers = tuple((0, int(x)) if x.isdigit() else (1, x.lower()) for x in pre.split('.'))
    return nums, not bool(pre), identifiers if pre else ()


def satisfies(version, requirement):

    r = requirement.strip()
    v = version_key(version)
    if not r or r == '(,)':
        return True
    if r[0] not in '[(':
        return v >= version_key(r)
    if r[-1:] not in '])':
        raise ValueError(f'Поврежденный диапазон версий: {r}')
    body = r[1:-1]
    if ',' not in body:
        if r[0] != '[' or r[-1] != ']':
            raise ValueError(f'Поврежденный диапазон версий: {r}')
        return v == version_key(body)
    low, high = (s.strip() for s in body.split(',', 1))
    return ((not low or (v >= version_key(low) if r[0] == '[' else v > version_key(low)))
            and (not high or (v <= version_key(high) if r[-1] == ']' else v < version_key(high))))


def read_url(url):
    request = Request(url, headers={'User-Agent': 'Student-NuGet-Graph/1.0'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=20) as response:
                return response.read()
        except (URLError, OSError, IncompleteRead, RemoteDisconnected) as error:
            retryable = not isinstance(error, HTTPError) or error.code in (408, 429, 500, 502, 503, 504)
            if not retryable or attempt == 2:
                raise ValueError(f'Не удалось получить {url}: {error}') from error


class NuGetRepository:
    def __init__(self, url, framework=None):
        index = json.loads(read_url(url))
        self.base = next((r['@id'].rstrip('/') + '/' for r in index.get('resources', [])
                          if 'PackageBaseAddress/3.0.0' in r.get('@type', '')), None)
        if not self.base:
            raise ValueError('В индексе нет ресурса PackageBaseAddress/3.0.0')
        self.framework = framework
        self.version_cache = {}
        self.dependency_cache = {}

    def versions(self, name):
        name = name.lower()
        if name not in self.version_cache:
            self.version_cache[name] = json.loads(read_url(f'{self.base}{name}/index.json'))['versions']
        return self.version_cache[name]

    def resolve(self, name, requirement):
        
        candidates = [v for v in self.versions(name)
                      if ('-' in requirement or '-' not in v) and satisfies(v, requirement)]
        if not candidates:
            raise ValueError(f'Нет подходящей версии {name}: {requirement}')
        return name.lower(), min(candidates, key=version_key)

    def exact(self, name, version):
        for v in self.versions(name):
            if version_key(v) == version_key(version):
                return name.lower(), v
        raise ValueError(f'Не найдена точная версия {name} {version}')

    def dependencies(self, node):
        if node in self.dependency_cache:
            return self.dependency_cache[node]
        name, version = node
        tree = ET.fromstring(read_url(f'{self.base}{name}/{version}/{name}.nuspec'))
        
        for element in tree.iter():
            element.tag = element.tag.rsplit('}', 1)[-1]
        container = tree.find('./metadata/dependencies')
        result = []
        if container is not None:
            groups = container.findall('group')
            if self.framework is not None:
                selected = [g for g in groups if g.get('targetFramework', '').casefold() == self.framework.casefold()]
                if groups and not selected:
                    available = ', '.join(g.get('targetFramework', '(общая)') for g in groups)
                    raise ValueError(f'{name}: нет точной группы {self.framework}; есть: {available}')
            else:
                selected = groups
            deps = container.findall('dependency')
            for group in selected:
                deps.extend(group.findall('dependency'))
            for dep in deps:
                item = (dep.attrib['id'], dep.get('version', ''))
                if item not in result:
                    result.append(item)
        self.dependency_cache[node] = result
        return result


class TestRepository:

    def __init__(self, path):
        self.packages = json.loads(Path(path).read_text(encoding='utf-8-sig'))['packages']
        if not isinstance(self.packages, dict) or not self.packages:
            raise ValueError('packages должен быть непустым объектом')
        for name, deps in self.packages.items():
            if not re.fullmatch('[A-Z]+', name) or not isinstance(deps, list):
                raise ValueError('Нужны имена из больших латинских букв и списки зависимостей')
            if any(not isinstance(d, str) or d not in self.packages for d in deps):
                raise ValueError(f'{name}: ссылка на неизвестный пакет')

    def exact(self, name, version):
        if name not in self.packages or version != '1.0.0':
            raise ValueError(f'Не найден пакет {name} {version}')
        return name, version

    def resolve(self, name, requirement):
        return self.exact(name, '1.0.0')

    def dependencies(self, node):
        return [(name, '[1.0.0]') for name in self.packages[node[0]]]
