import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from src.cli import options
from src.graph import build_graph, reverse_dependencies
from src.repository import TestRepository, NuGetRepository, read_url, satisfies
from src.visualize import dot_graph


class Tests(unittest.TestCase):
    def setUp(self):
        self.repo = TestRepository('data/branch.json')
        self.root = ('A', '1.0.0')

    def names(self, graph):
        return {n[0] for n in graph}

    def test_depth_zero(self):
        graph = build_graph(self.repo, self.root, 0)
        self.assertEqual(graph, {self.root: set()})

    def test_depth_one(self):
        graph = build_graph(self.repo, self.root, 1)
        self.assertEqual(self.names(graph), {'A', 'B', 'C'})

    def test_transitive(self):
        graph = build_graph(self.repo, self.root, 3)
        self.assertEqual(self.names(graph), {'A', 'B', 'C', 'D', 'E'})

    def test_filter(self):
        g = build_graph(self.repo, self.root, 4, 'b')
        self.assertEqual(self.names(g), {'A', 'C', 'D', 'E'})
        self.assertNotIn(('B', '1.0.0'), {x for d in g.values() for x in d})

    def test_cycle(self):
        repo = TestRepository('data/cycle.json')
        g = build_graph(repo, self.root, 100000)
        self.assertEqual(len(g), 4)
        self.assertIn(self.root, g[('C', '1.0.0')])

    def test_shorter_path_reopens_boundary(self):
        class Repo:
            def dependencies(self, node):
                graph = {
                    'A': ['B', 'D'], 'B': ['C'], 'C': ['D'],
                    'D': ['E'], 'E': [],
                }
                return [(name, '') for name in graph[node[0]]]

            def resolve(self, name, requirement):
                return name, '1.0.0'
        self.assertIn(('E', '1.0.0'), build_graph(Repo(), self.root, 3))

    def test_reverse_transitive(self):
        g = build_graph(self.repo, self.root, 3)
        self.assertEqual(self.names(reverse_dependencies(g, 'D', 3)),
                         {'A', 'B', 'C'})
        self.assertEqual(self.names(reverse_dependencies(g, 'D', 1)),
                         {'B', 'C'})

    def test_reverse_cycle_no_self(self):
        g = build_graph(TestRepository('data/cycle.json'), self.root, 10)
        self.assertEqual(self.names(reverse_dependencies(g, 'A', 10)),
                         {'B', 'C'})

    def test_empty(self):
        graph = build_graph(TestRepository('data/empty.json'), self.root, 3)
        self.assertEqual(graph, {self.root: set()})

    def test_intervals(self):
        cases = [
            ('1.0.0', '1.0', True), ('1.9.0', '[1.0,2.0)', True),
            ('2.0.0', '[1.0,2.0)', False), ('1.0.1', '[1.0]', False),
            ('0.9', '(,1.0]', True),
            ('1.0.0-beta.2', '[1.0.0-beta.1,1.0)', True),
        ]
        for version, requirement, result in cases:
            with self.subTest(version=version, requirement=requirement):
                self.assertEqual(satisfies(version, requirement), result)

    def test_nuspec_namespaces_groups(self):
        repo = object.__new__(NuGetRepository)
        repo.base = 'https://example/'
        repo.framework, repo.dependency_cache = None, {}
        xml = (
            b'<package xmlns="urn:test"><metadata><dependencies>'
            b'<group targetFramework="net8">'
            b'<dependency id="B" version="[1.0]"/></group>'
            b'<group targetFramework="net6">'
            b'<dependency id="C" version="2.0"/></group>'
            b'</dependencies></metadata></package>'
        )
        node = ('a', '1.0.0')
        with patch('src.repository.read_url', return_value=xml):
            self.assertEqual(repo.dependencies(node),
                             [('B', '[1.0]'), ('C', '2.0')])
        repo.framework, repo.dependency_cache = 'net8', {}
        with patch('src.repository.read_url', return_value=xml):
            self.assertEqual(repo.dependencies(node), [('B', '[1.0]')])

    def test_invalid_repository_reference(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'bad.json'
            path.write_text(json.dumps({'packages':{'A':['B']}}))
            with self.assertRaises(ValueError):
                TestRepository(path)

    def test_network_retries_transient_errors_only(self):
        url = 'https://example.org/index.json'
        response = io.BytesIO(b'{}')
        events = [URLError(TimeoutError()), response]
        with patch('src.repository.urlopen', side_effect=events) as request:
            self.assertEqual(read_url(url), b'{}')
            self.assertEqual(request.call_count, 2)
        missing = HTTPError(url, 404, 'Not found', None, None)
        with patch('src.repository.urlopen', side_effect=missing) as request:
            with self.assertRaisesRegex(ValueError, '404'):
                read_url(url)
            self.assertEqual(request.call_count, 1)

    def test_cli_errors(self):
        base = ['--package', 'A', '--version', '1.0.0', '--test',
                '--repository', 'data/branch.json']
        invalid = [
            ['--max-depth', '-1'], ['--version', 'blah'], ['--package', '!'],
            ['--repository', 'missing.json'], ['--filter', 'A'],
            ['--framework', ' '], ['--reverse', '!'], ['--stage', '4'],
        ]
        with contextlib.redirect_stderr(io.StringIO()):
            for extra in invalid:
                with self.subTest(extra=extra):
                    with self.assertRaises(SystemExit) as error:
                        options(base + extra)
                    self.assertEqual(error.exception.code, 2)
            with self.assertRaises(SystemExit) as error:
                options(['--package', 'A', '--version', '1.0.0',
                         '--repository', 'not-url'])
            self.assertEqual(error.exception.code, 2)

    def test_dot_contains_shared_edges(self):
        dot = dot_graph(build_graph(self.repo,self.root,3))
        self.assertIn('"B@1.0.0" -> "D@1.0.0";',dot)
        self.assertIn('"C@1.0.0" -> "D@1.0.0";',dot)


if __name__ == '__main__':
    unittest.main()
