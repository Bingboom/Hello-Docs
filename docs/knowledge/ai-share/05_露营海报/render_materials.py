#!/usr/bin/env python3
"""Generate the sharing HTML from Markdown using installed Pandoc.

This edits only knowledge-content HTML, never the product-manual pipeline.
"""
import hashlib
import html
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
SHARE = ROOT.parent


def refresh_stylesheet(shell):
    version = hashlib.sha256((SHARE / '阅读样式.css').read_bytes()).hexdigest()[:12]
    return re.sub(r'href="((?:\.\./)?阅读样式\.css)(?:\?[^"<>]*)?"',
                  lambda match: f'href="{match.group(1)}?v={version}"', shell)


def render(source):
    return subprocess.run(
        ['pandoc', '--from=markdown', '--to=html5', '--wrap=none', str(source)],
        check=True, capture_output=True, text=True,
    ).stdout


def body_and_nav(source):
    body = render(source)
    section_count = 0

    def heading(match):
        nonlocal section_count
        identity = f's{section_count}'
        section_count += 1
        text = match.group(1)
        return f'<h2 id="{identity}">{text}</h2>'

    body = re.sub(r'<h2[^>]*>(.*?)</h2>', heading, body, flags=re.S)
    # Keep the existing section and Pandoc subsection IDs stable for incoming links.
    headings = [
        f'<a class="toc-level-{level}" href="#{html.escape(identity, quote=True)}">{text}</a>'
        for level, identity, text in re.findall(
            r'<h([23])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h\1>', body, re.S
        )
    ]
    body = re.sub(r'<table([^>]*)>(.*?)</table>',
                  r'<div class="table-scroll"><table\1>\2</table></div>', body, flags=re.S)
    return body, ''.join(headings)


def main():
    main_path = SHARE / '00_打开分享.html'
    original = refresh_stylesheet(main_path.read_text('utf-8'))
    body, nav = body_and_nav(SHARE / '分享稿.md')
    main_html = re.sub(r'<main>.*?</main>', lambda _: '<main>' + body + '</main>', original, flags=re.S)
    main_html = re.sub(r'<nav>.*?</nav>', lambda _: '<nav>' + nav + '</nav>', main_html, flags=re.S)
    main_path.write_text(main_html, 'utf-8')
    head = original.split('</head>')[0]
    head = head.replace('href="阅读样式.css', 'href="../阅读样式.css')
    head += '''<style>
    .material .layout{display:block;max-width:1240px}.material main{padding:32px}
    .poster-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
    .poster-grid figure{margin:0}.poster-grid img{display:block;width:100%;border-radius:12px}
    figcaption{font-size:13px;color:var(--muted);padding:10px 0}
    @media(max-width:650px){.poster-grid{grid-template-columns:1fr}.material main{padding:20px}}
    @media print{.poster-grid{grid-template-columns:repeat(3,minmax(0,1fr))}figure{break-inside:avoid}}
    </style></head>'''
    for source_name, output_name in [('README.md', 'README.html'),
                                     ('演示脚本.md', '演示脚本.html'),
                                     ('素材清单.md', '素材清单.html'),
                                     ('案例入口.md', 'index.html')]:
        source = ROOT / source_name
        material, _ = body_and_nav(source)
        for name in ('README', '演示脚本', '素材清单'):
            material = material.replace(f'href="{name}.md"', f'href="{name}.html"')
        title = html.escape(source.read_text('utf-8').splitlines()[0].lstrip('# '))
        page_head = re.sub(r'<title>.*?</title>', '<title>' + title + '</title>', head)
        page = (page_head + '<body class="reading-guide material">'
                '<header class="topbar"><a href="index.html">小野露营市集 · 分享素材</a>'
                '<a href="../00_打开分享.html">返回分享稿</a></header>'
                '<div class="layout"><main>' + material + '</main></div></body></html>')
        (ROOT / output_name).write_text(page, 'utf-8')
    references = sorted((SHARE / '04_参考资料').glob('*.md'))
    references.append(SHARE / '03_GitHub原例' / '阅读版.md')
    for source in references:
        target = source.with_suffix('.html')
        template = target if target.exists() else SHARE / '04_参考资料' / '05_钉钉MCP.html'
        shell = refresh_stylesheet(template.read_text('utf-8'))
        content, navigation = body_and_nav(source)
        shell = re.sub(r'<main>.*?</main>', lambda _: '<main>' + content + '</main>', shell, flags=re.S)
        shell = re.sub(r'<nav>.*?</nav>', lambda _: '<nav>' + navigation + '</nav>', shell, flags=re.S)
        title = html.escape(source.read_text('utf-8').splitlines()[0].lstrip('# '))
        shell = re.sub(r'<title>.*?</title>', lambda _: '<title>' + title + '</title>', shell)
        target.write_text(shell, 'utf-8')
    print('Generated sharing article, materials, and aligned reference pages.')


if __name__ == '__main__':
    main()
