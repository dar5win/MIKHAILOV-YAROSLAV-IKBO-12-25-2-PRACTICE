"""Вывод Graphviz DOT и автономного SVG-просмотра."""
import html
import json
import math
from pathlib import Path


def dot_graph(graph):
    quote = lambda n: json.dumps(f'{n[0]}@{n[1]}', ensure_ascii=False)
    lines = ['digraph Dependencies {', '  rankdir=LR;', '  node [shape=box];']
    for node, children in sorted(graph.items()):
        lines.append(f'  {quote(node)};')
        lines.extend(f'  {quote(node)} -> {quote(child)};' for child in sorted(children))
    return '\n'.join(lines + ['}'])


def save_html(graph, dot, path):
    nodes = sorted(graph)
    size = max(1000, len(nodes) * 100)
    positions = {n: (size/2 + size*.36*math.cos(i*2*math.pi/len(nodes)), size/2 + size*.36*math.sin(i*2*math.pi/len(nodes))) for i, n in enumerate(nodes)}
    svg = [f'<svg viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg"><defs><marker id="a" markerWidth="10" markerHeight="10" refX="10" refY="3" orient="auto"><path d="M0,0 L0,6 L10,3 z" fill="#75d9c4"/></marker></defs>']
    for parent, children in graph.items():
        x1, y1 = positions[parent]
        for child in sorted(children):
            x2, y2 = positions[child]
            d = math.hypot(x2-x1, y2-y1)
            if d:
                x2 -= (x2-x1)/d*70
                y2 -= (y2-y1)/d*70
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#75d9c4" stroke-width="2" marker-end="url(#a)"/>')
    for name, version in nodes:
        x, y = positions[(name, version)]
        svg.append(f'<circle cx="{x}" cy="{y}" r="68" fill="#233957" stroke="#92a8c9"/><text x="{x}" y="{y}" text-anchor="middle" fill="white" font-size="13"><tspan x="{x}" dy="-4">{html.escape(name)}</tspan><tspan x="{x}" dy="20">{html.escape(version)}</tspan></text>')
    svg.append('</svg>')
    document = '<!doctype html><html lang="ru"><meta charset="utf-8"><title>NuGet — вариант 15</title><style>body{background:#101b2c;color:#edf4ff;font:18px Arial;margin:30px}svg{width:100%;max-height:75vh}pre{white-space:pre-wrap;background:#21334e;padding:20px}</style><h1>Зависимости NuGet</h1><p>Стрелка A → B: пакету A нужен пакет B. На пределе глубины зависимости не раскрываются.</p>' + ''.join(svg) + '<h2>Graphviz DOT</h2><pre>' + html.escape(dot) + '</pre><p>Картинка: автономный SVG-просмотр. Для раскладки Graphviz используйте .dot.</p></html>'
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(document, encoding='utf-8')
