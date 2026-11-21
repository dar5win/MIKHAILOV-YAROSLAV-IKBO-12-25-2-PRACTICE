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


def reverse_dependencies(graph, target, max_depth):

    reverse = {node: set() for node in graph}
    for parent, children in graph.items():
        for child in children:
            reverse.setdefault(child, set()).add(parent)
    starts = [node for node in reverse if node[0].casefold() == target.casefold()]
    if not starts:
        raise ValueError(f'Пакет {target} отсутствует в исследованном графе')
    result, best = set(), {}
    stack = [(node, 0) for node in starts]
    while stack:
        node, depth = stack.pop()
        if node in best and best[node] <= depth:
            continue
        best[node] = depth
        if node not in starts:
            result.add(node)
        if depth < max_depth:
            stack.extend((parent, depth + 1) for parent in sorted(reverse[node], reverse=True))
    return sorted(result)
