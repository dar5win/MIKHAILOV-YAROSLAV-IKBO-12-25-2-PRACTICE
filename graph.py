"""DFS со стеком вместо рекурсии."""


def build_graph(repository, root, max_depth, excluded=''):
    graph, best = {root: set()}, {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if node in best and best[node] <= depth:
            continue
        best[node] = depth
        graph.setdefault(node, set())
        if depth >= max_depth:
            continue
        children = []
        for name, requirement in repository.dependencies(node):
            if excluded and excluded.casefold() in name.casefold():
                continue
            child = repository.resolve(name, requirement)
            graph[node].add(child)
            graph.setdefault(child, set())
            children.append(child)
            if len(graph) > 2000:
                raise ValueError('Больше 2000 вершин; уменьшите --max-depth')
        for child in reversed(children):
            stack.append((child, depth + 1))
    return graph


def text_graph(graph):
    lines = []
    for node, children in sorted(graph.items()):
        deps = ', '.join(f'{n}@{v}' for n, v in sorted(children)) or '(нет раскрытых зависимостей)'
        lines.append(f'{node[0]}@{node[1]} -> {deps}')
    return '\n'.join(lines)
