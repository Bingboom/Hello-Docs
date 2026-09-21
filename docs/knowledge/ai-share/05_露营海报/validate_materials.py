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
        if tag in {'a', 'img', 'link', 'script', 'source', 'iframe'}:
            for key, value in attrs:
                if key in {'href', 'src'} and value:
                    self.links.append(value)


def main():
    html = (SHARE / '00_打开分享.html').read_text('utf-8')
    expected, expected_nav = body_and_nav(SHARE / '分享稿.md')
    assert re.search(r'<main>(.*?)</main>', html, re.S).group(1) == expected
    assert re.search(r'<nav>(.*?)</nav>', html, re.S).group(1) == expected_nav
    heading_ids = re.findall(r'<h[23]\b[^>]*\bid="([^"]+)"', expected)
    nav_ids = re.findall(r'href="#([^"]+)"', expected_nav)
    assert nav_ids == heading_ids, 'Every section and subsection must appear in the TOC in order'
    approved_structure = [
        '【产品运营部】AI 使用知识分享', '一、GPT-6 Astra 到底能做到什么？',
        '二、厉害的不只是做出一个动画', '三、放到工作里，能替我们做什么？',
        '四、不会写代码，怎么把它用起来？', '五、从做一次，到以后都能用',
        '六、海报之外，Agent 还能接着做什么？',
        '附录 1：跟着小林，从空文件夹做出一个海报工具',
        '附录 2：从 GitHub 找参考仓库，做成自己的工具',
    ]
    headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', html)
    assert headings == approved_structure, 'Approved story structure changed'
    for source in ('配图/00-概览-q版.png', '配图/01-场景-露营海报-q版.png',
                   '05_露营海报/evidence/13-posters-browser.png',
                   '05_露营海报/evidence/18-dingtalk-product-table.png',
                   '06_动画示例/pelican-bike.html'):
        assert f'src="{source}"' in html, f'Missing retained/adapted illustration: {source}'
    missing = []
    count = 0
    references = list((SHARE / '04_参考资料').glob('*.html'))
    references.append(SHARE / '03_GitHub原例' / '阅读版.html')
    paths = [SHARE / '00_打开分享.html', *ROOT.glob('*.html'), *references,
             SHARE / '06_动画示例' / 'pelican-bike.html']
    for page in references:
        source = page.with_suffix('.md')
        if source.exists():
            expected, expected_nav = body_and_nav(source)
            actual = page.read_text('utf-8')
            assert re.search(r'<main>(.*?)</main>', actual, re.S).group(1) == expected, page.name
            assert re.search(r'<nav>(.*?)</nav>', actual, re.S).group(1) == expected_nav, page.name
            assert not re.search(r'学生|家长会|情况卡|家访|按学号', actual), page.name
    for path in paths:
        parser = Links()
        parser.feed(path.read_text('utf-8'))
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path.resolve()
            count += 1
            if not target.is_file() or not target.is_relative_to(SHARE) or not public_file(target):
                missing.append(f'{path.name}: {link}')
            elif parts.fragment and target.suffix == '.html':
                ids = re.findall(r'\bid=[\"\']([^\"\']+)[\"\']', target.read_text('utf-8'))
                if unquote(parts.fragment) not in ids:
                    missing.append(f'{path.name}: missing anchor {link}')
    if missing:
        raise ValueError('\n'.join(missing))
    assert not any('学生情况卡' in heading for heading in re.findall(r'<h2[^>]*>(.*?)</h2>', html))
    print(f'PASS: Markdown / HTML exact-body parity; {len(paths)} pages, {count} public local links.')


if __name__ == '__main__':
    main()
