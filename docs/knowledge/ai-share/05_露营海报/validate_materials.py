#!/usr/bin/env python3
"""Read-only checks for sharing-page parity and packaged local links."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from package_materials import public_file
from render_materials import ROOT, SHARE, body_and_nav


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in {'a', 'img', 'link', 'script', 'source'}:
            for key, value in attrs:
                if key in {'href', 'src'} and value:
                    self.links.append(value)


def main():
    html = (SHARE / '00_打开分享.html').read_text('utf-8')
    expected, _ = body_and_nav(SHARE / '分享稿.md')
    assert re.search(r'<main>(.*?)</main>', html, re.S).group(1) == expected
    original_structure = [
        '【产品运营部】AI 使用知识分享', '一、用代码解决工作中的问题',
        '二、从需求到实现', '怎样开始', '三、修改与调试', '四、复用与维护',
        '五、GitHub：借鉴项目与版本管理', '六、让 Agent 调用更多工具：CLI 与 MCP',
        'CLI：通过命令调用工具', 'MCP：连接工具和资料',
    ]
    headings = re.findall(r'<h[123][^>]*>(.*?)</h[123]>', html)
    assert headings[:len(original_structure)] == original_structure, 'Original article structure changed'
    assert headings[len(original_structure)].startswith('附录：')
    for source in ('配图/00-概览-q版.png', '配图/01-场景-露营海报-q版.png'):
        assert f'src="{source}"' in html, f'Missing retained/adapted illustration: {source}'
    missing = []
    count = 0
    references = list((SHARE / '04_参考资料').glob('*.html'))
    paths = [SHARE / '00_打开分享.html', *ROOT.glob('*.html'), *references]
    for page in references:
        source = page.with_suffix('.md')
        if source.exists():
            expected, _ = body_and_nav(source)
            actual = page.read_text('utf-8')
            assert re.search(r'<main>(.*?)</main>', actual, re.S).group(1) == expected, page.name
            assert not re.search(r'学生|家长会|情况卡|家访|按学号', actual), page.name
    for path in paths:
        parser = Links()
        parser.feed(path.read_text('utf-8'))
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (path.parent / unquote(parts.path)).resolve()
            count += 1
            if not target.is_file() or not target.is_relative_to(SHARE) or not public_file(target):
                missing.append(f'{path.name}: {link}')
    if missing:
        raise ValueError('\n'.join(missing))
    assert not any('学生情况卡' in heading for heading in re.findall(r'<h2[^>]*>(.*?)</h2>', html))
    print(f'PASS: Markdown / HTML exact-body parity; {len(paths)} pages, {count} public local links.')


if __name__ == '__main__':
    main()
