import json
import math
from collections import deque
from pathlib import Path
import shutil
import subprocess


def dot_graph(graph):
    quote = lambda n: json.dumps(f'{n[0]}@{n[1]}', ensure_ascii=False)
    lines = ['digraph Dependencies {', '  rankdir=LR;',
             '  graph [bgcolor="white", pad="0.4", nodesep="0.35", ranksep="0.8", dpi=160];',
             '  node [shape=box, style="rounded,filled", fillcolor="white", color="#4b555b", fontname="Arial", fontsize=12, margin="0.16,0.10"];',
             '  edge [color="#4b555b", arrowsize=0.7];']
    root = next(iter(graph), None)
    for node, children in sorted(graph.items()):
        style = ' [fillcolor="#a8d6ce"]' if node == root else ''
        lines.append(f'  {quote(node)}{style};')
        lines.extend(f'  {quote(node)} -> {quote(child)};' for child in sorted(children))
    return '\n'.join(lines + ['}'])


def save_png(graph, dot, path):

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    executable = shutil.which('dot')
    if executable:
        try:
            subprocess.run([executable, '-Tpng', '-o', str(target)],
                           input=dot.encode('utf-8'), check=True, timeout=60,
                           capture_output=True)
            return
        except (subprocess.SubprocessError, OSError) as error:
            raise ValueError(f'Graphviz не смог создать PNG: {error}') from error
    draw_png(graph, target)


def draw_png(graph, path):

    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as error:
        raise ValueError('Для PNG установите Pillow: python -m pip install -r requirements.txt') from error
    if not graph:
        raise ValueError('Нельзя нарисовать пустой граф')
    scale = 2
    def font(size):
        for name in ('C:/Windows/Fonts/arial.ttf', 'DejaVuSans.ttf'):
            try:
                return ImageFont.truetype(name, size * scale)
            except OSError:
                pass
        return ImageFont.load_default(size=size * scale)
    title_font, version_font = font(19), font(15)
    measure = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    
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
    columns = {}
    for node, level in levels.items():
        columns.setdefault(level, []).append(node)
    columns = {k: sorted(v) for k, v in sorted(columns.items())}
    box_widths = {n: max(105, math.ceil(measure.textlength(n[0], font=title_font)/scale)+36,
                         math.ceil(measure.textlength(n[1], font=version_font)/scale)+36) for n in levels}
    widths = {k: max(box_widths[n] for n in nodes) for k, nodes in columns.items()}
    margin, box_height, row_gap, column_gap = 70, 66, 38, 140
    height = max(280, margin*2 + max(len(v) for v in columns.values())*(box_height+row_gap)-row_gap)
    width = margin*2 + sum(widths.values()) + column_gap*(len(columns)-1)
    if width*height > 30_000_000:
        raise ValueError('Картинка слишком большая; уменьшите --max-depth или используйте фильтр')
    image = Image.new('RGB', (width*scale, height*scale), 'white')
    draw = ImageDraw.Draw(image)
    boxes, x = {}, margin
    for level, nodes in columns.items():
        column_height = len(nodes)*(box_height+row_gap)-row_gap
        y = (height-column_height)/2
        for node in nodes:
            w = box_widths[node]
            left = x+(widths[level]-w)/2
            boxes[node] = (left, y, left+w, y+box_height)
            y += box_height+row_gap
        x += widths[level]+column_gap
    ink = '#49545b'
    def curve(points):
        a,b,c,d = points
        samples = []
        for i in range(81):
            t = i/80
            u = 1-t
            samples.append(((u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0])*scale,
                            (u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1])*scale))
        draw.line(samples, fill=ink, width=2*scale)
        end, before = samples[-1], samples[-4]
        angle = math.atan2(end[1]-before[1], end[0]-before[0])
        length, spread = 11*scale, .40
        arrow = [end, (end[0]-length*math.cos(angle-spread),end[1]-length*math.sin(angle-spread)),
                 (end[0]-length*math.cos(angle+spread),end[1]-length*math.sin(angle+spread))]
        draw.polygon(arrow, fill=ink)
    for parent, children in graph.items():
        l,t,r,b = boxes[parent]
        for child in sorted(children):
            cl,ct,cr,cb = boxes[child]
            if levels[child] > levels[parent]:
                start,end = (r,(t+b)/2),(cl,(ct+cb)/2)
                mid = (r+cl)/2
                curve((start,(mid,start[1]),(mid,end[1]),end))
            elif parent == child:
                curve(((r-25,t),(r+70,t-55),(l-35,t-55),(l+25,t)))
            else:
                start,end = ((l+r)/2,t),((cl+cr)/2,ct)
                top = max(12,min(t,ct)-48)
                curve((start,(start[0],top),(end[0],top),end))
    root = next(iter(graph))
    for node, box in boxes.items():
        l,t,r,b = box
        rectangle = tuple(round(v*scale) for v in box)
        draw.rounded_rectangle(rectangle, radius=14*scale,
                               fill='#a8d6ce' if node == root else '#ffffff', outline=ink, width=2*scale)
        center = (l+r)/2*scale
        draw.text((center,(t+11)*scale),node[0],font=title_font,fill='#222c32',anchor='mt')
        draw.text((center,(t+37)*scale),node[1],font=version_font,fill='#67727a',anchor='mt')
    image.resize((width,height),Image.Resampling.LANCZOS).save(path,format='PNG')
