from collections import deque
import json
import math
from pathlib import Path
import shutil
import subprocess


SCALE = 2
MARGIN = 70
BOX_HEIGHT = 66
ROW_GAP = 38
COLUMN_GAP = 140
MAX_IMAGE_AREA = 30_000_000
CURVE_STEPS = 80
INK = '#49545b'


def quote_node(node):
    return json.dumps(f'{node[0]}@{node[1]}', ensure_ascii=False)


def dot_graph(graph):
    lines = [
        'digraph Dependencies {',
        '  rankdir=LR;',
        '  graph [bgcolor="white", pad="0.4", nodesep="0.35", '
        'ranksep="0.8", dpi=160];',
        '  node [shape=box, style="rounded,filled", fillcolor="white", '
        'color="#4b555b", fontname="Arial", fontsize=12, '
        'margin="0.16,0.10"];',
        '  edge [color="#4b555b", arrowsize=0.7];',
    ]
    root = next(iter(graph), None)
    for node, children in sorted(graph.items()):
        style = ' [fillcolor="#a8d6ce"]' if node == root else ''
        label = quote_node(node)
        lines.append(f'  {label}{style};')
        for child in sorted(children):
            lines.append(f'  {label} -> {quote_node(child)};')
    return '\n'.join(lines + ['}'])


def save_png(graph, dot, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    executable = shutil.which('dot')
    if not executable:
        draw_png(graph, target)
        return
    try:
        subprocess.run(
            [executable, '-Tpng', '-o', str(target)],
            input=dot.encode('utf-8'), check=True, timeout=60,
            capture_output=True,
        )
    except (subprocess.SubprocessError, OSError) as error:
        raise ValueError(f'Graphviz не смог создать PNG: {error}') from error


def load_font(image_font, size):
    for name in ('C:/Windows/Fonts/arial.ttf', 'DejaVuSans.ttf'):
        try:
            return image_font.truetype(name, size * SCALE)
        except OSError:
            pass
    return image_font.load_default(size=size * SCALE)


def graph_levels(graph):
    levels = {}
    for root in graph:
        if root in levels:
            continue
        levels[root] = 0
        queue = deque([root])
        while queue:
            parent = queue.popleft()
            for child in sorted(graph[parent]):
                if child not in levels:
                    levels[child] = levels[parent] + 1
                    queue.append(child)
    return levels


def group_columns(levels):
    columns = {}
    for node, level in levels.items():
        columns.setdefault(level, []).append(node)
    return {level: sorted(nodes) for level, nodes in sorted(columns.items())}


def node_width(measure, node, fonts):
    widths = [
        math.ceil(measure.textlength(text, font=font) / SCALE) + 36
        for text, font in zip(node, fonts)
    ]
    return max(105, *widths)


def column_height(nodes):
    return len(nodes) * (BOX_HEIGHT + ROW_GAP) - ROW_GAP


def place_boxes(columns, box_widths):
    widths = {
        level: max(box_widths[node] for node in nodes)
        for level, nodes in columns.items()
    }
    height = max(280, MARGIN * 2 + max(map(column_height, columns.values())))
    width = MARGIN * 2 + sum(widths.values()) + COLUMN_GAP * (len(columns) - 1)
    if width * height > MAX_IMAGE_AREA:
        raise ValueError(
            'Картинка слишком большая; уменьшите --max-depth '
            'или используйте фильтр'
        )
    boxes, x = {}, MARGIN
    for level, nodes in columns.items():
        y = (height - column_height(nodes)) / 2
        for node in nodes:
            box_width = box_widths[node]
            left = x + (widths[level] - box_width) / 2
            boxes[node] = (left, y, left + box_width, y + BOX_HEIGHT)
            y += BOX_HEIGHT + ROW_GAP
        x += widths[level] + COLUMN_GAP
    return (width, height), boxes


def curve_samples(points):
    a, b, c, d = points
    samples = []
    for index in range(CURVE_STEPS + 1):
        t = index / CURVE_STEPS
        u = 1 - t
        x = u*u*u*a[0] + 3*u*u*t*b[0] + 3*u*t*t*c[0] + t*t*t*d[0]
        y = u*u*u*a[1] + 3*u*u*t*b[1] + 3*u*t*t*c[1] + t*t*t*d[1]
        samples.append((x * SCALE, y * SCALE))
    return samples


def draw_curve(draw, points):
    samples = curve_samples(points)
    draw.line(samples, fill=INK, width=2 * SCALE)
    end, before = samples[-1], samples[-4]
    angle = math.atan2(end[1] - before[1], end[0] - before[0])
    length, spread = 11 * SCALE, 0.40
    arrow = [end]
    for direction in (angle - spread, angle + spread):
        x = end[0] - length * math.cos(direction)
        y = end[1] - length * math.sin(direction)
        arrow.append((x, y))
    draw.polygon(arrow, fill=INK)


def edge_curve(parent_box, child_box, forward, self_loop):
    left, top, right, bottom = parent_box
    cl, ct, cr, cb = child_box
    if forward:
        start = (right, (top + bottom) / 2)
        end = (cl, (ct + cb) / 2)
        mid = (right + cl) / 2
        return start, (mid, start[1]), (mid, end[1]), end
    if self_loop:
        return ((right - 25, top), (right + 70, top - 55),
                (left - 35, top - 55), (left + 25, top))
    start = ((left + right) / 2, top)
    end = ((cl + cr) / 2, ct)
    crest = max(12, min(top, ct) - 48)
    return start, (start[0], crest), (end[0], crest), end


def draw_edges(draw, graph, boxes, levels):
    for parent, children in graph.items():
        for child in sorted(children):
            points = edge_curve(
                boxes[parent], boxes[child], levels[child] > levels[parent],
                parent == child,
            )
            draw_curve(draw, points)


def draw_nodes(draw, boxes, root, fonts):
    title_font, version_font = fonts
    for node, box in boxes.items():
        left, top, right, _ = box
        rectangle = tuple(round(value * SCALE) for value in box)
        draw.rounded_rectangle(
            rectangle, radius=14 * SCALE,
            fill='#a8d6ce' if node == root else '#ffffff',
            outline=INK, width=2 * SCALE,
        )
        center = (left + right) / 2 * SCALE
        draw.text(
            (center, (top + 11) * SCALE), node[0],
            font=title_font, fill='#222c32', anchor='mt',
        )
        draw.text(
            (center, (top + 37) * SCALE), node[1],
            font=version_font, fill='#67727a', anchor='mt',
        )


def draw_png(graph, path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValueError(
            'Для PNG установите Pillow: python -m pip install '
            '-r requirements.txt'
        ) from error
    if not graph:
        raise ValueError('Нельзя нарисовать пустой граф')
    fonts = (load_font(ImageFont, 19), load_font(ImageFont, 15))
    measure = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    levels = graph_levels(graph)
    box_widths = {node: node_width(measure, node, fonts) for node in levels}
    size, boxes = place_boxes(group_columns(levels), box_widths)
    canvas = tuple(value * SCALE for value in size)
    image = Image.new('RGB', canvas, 'white')
    draw = ImageDraw.Draw(image)
    draw_edges(draw, graph, boxes, levels)
    draw_nodes(draw, boxes, next(iter(graph)), fonts)
    image.resize(size, Image.Resampling.LANCZOS).save(path, format='PNG')
