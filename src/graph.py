MAX_GRAPH_NODES = 2000


def add_children(graph, repository, node, excluded):
    children = []
    for name, requirement in repository.dependencies(node):
        if excluded and excluded in name.casefold():
            continue
        child = repository.resolve(name, requirement)
        graph[node].add(child)
        graph.setdefault(child, set())
        children.append(child)
        if len(graph) > MAX_GRAPH_NODES:
            raise ValueError('Больше 2000 вершин; уменьшите --max-depth')
    return children


def build_graph(repository, root, max_depth, excluded=''):
    graph, best = {root: set()}, {}
    stack = [(root, 0)]
    excluded = excluded.casefold()
    while stack:
        node, depth = stack.pop()
        if node in best and best[node] <= depth:
            continue
        best[node] = depth
        if depth >= max_depth:
            continue
        children = add_children(graph, repository, node, excluded)
        for child in reversed(children):
            stack.append((child, depth + 1))
    return graph


def text_graph(graph):
    lines = []
    for node, children in sorted(graph.items()):
        dependencies = ', '.join(f'{n}@{v}' for n, v in sorted(children))
        label = dependencies or '(нет раскрытых зависимостей)'
        lines.append(f'{node[0]}@{node[1]} -> {label}')
    return '\n'.join(lines)


def reverse_edges(graph):
    reverse = {node: set() for node in graph}
    for parent, children in graph.items():
        for child in children:
            reverse.setdefault(child, set()).add(parent)
    return reverse


def reverse_dependencies(graph, target, max_depth):
    reverse = reverse_edges(graph)
    target_name = target.casefold()
    starts = {node for node in reverse if node[0].casefold() == target_name}
    if not starts:
        raise ValueError(f'Пакет {target} отсутствует в исследованном графе')
    best = {}
    stack = [(node, 0) for node in sorted(starts)]
    while stack:
        node, depth = stack.pop()
        if node in best and best[node] <= depth:
            continue
        best[node] = depth
        if depth < max_depth:
            for parent in sorted(reverse[node], reverse=True):
                stack.append((parent, depth + 1))
    return sorted(best.keys() - starts)
