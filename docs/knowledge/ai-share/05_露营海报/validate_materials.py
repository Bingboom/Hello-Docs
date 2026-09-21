#!/usr/bin/env python3
"""Read-only checks for sharing-page parity and packaged local links."""
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from package_materials import public_file
from render_materials import ROOT, SHARE, body_and_nav


TOOL_ZIP = SHARE / 'downloads' / 'xiaoye-poster-workbench.zip'
TOOL_ROOT = '小野海报工作台'


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
    html = (SHARE / 'index.html').read_text('utf-8')
    practical_html = (SHARE / 'practical.html').read_text('utf-8')
    legacy_html = (SHARE / '00_打开分享.html').read_text('utf-8')
    assert 'content="0;url=index.html"' in legacy_html, 'Legacy Chinese entry must redirect to index.html'
    expected, expected_nav = body_and_nav(SHARE / '分享稿.md')
    assert re.search(r'<main>(.*?)</main>', html, re.S).group(1) == expected
    assert re.search(r'<nav>(.*?)</nav>', html, re.S).group(1) == expected_nav
    practical_expected, practical_nav = body_and_nav(SHARE / '实用版分享稿.md')
    assert re.search(r'<main>(.*?)</main>', practical_html, re.S).group(1) == practical_expected
    assert re.search(r'<nav>(.*?)</nav>', practical_html, re.S).group(1) == practical_nav
    heading_ids = re.findall(r'<h[23]\b[^>]*\bid="([^"]+)"', expected)
    nav_ids = re.findall(r'href="#([^"]+)"', expected_nav)
    assert nav_ids == heading_ids, 'Every section and subsection must appear in the TOC in order'
    practical_heading_ids = re.findall(r'<h[23]\b[^>]*\bid="([^"]+)"', practical_expected)
    practical_nav_ids = re.findall(r'href="#([^"]+)"', practical_nav)
    assert practical_nav_ids == practical_heading_ids, 'Every practical-page heading must appear in order'
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
    practical_structure = [
        '【产品运营部】AI 使用知识分享：从工作需求做起',
        '一、先从一件具体的工作开始', '二、打开一个空文件夹',
        '三、改一次价，不用重新来', '四、接下来还能往哪儿走',
        '附录：从 GitHub 找参考仓库，做成自己的工具',
        '彩蛋：一句话生成会骑车的鹈鹕',
    ]
    practical_headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', practical_html)
    assert practical_headings == practical_structure, 'Practical story structure changed'
    assert '附录 1：跟着小林' not in practical_html, 'Hands-on steps must stay in the main story'
    egg_position = practical_html.index('彩蛋：一句话生成会骑车的鹈鹕')
    assert practical_html.index('06_动画示例/pelican-bike.html') > egg_position
    for source in ('配图/小野300-Sol-High-实图.png', '配图/01-场景-露营海报-q版.png',
                   '配图/小野500-HTML-实图.png', '配图/小野1000-HTML-实图.png',
                   '配图/钉钉产品与海报-实录.png',
                   '配图/钉钉MCP回读核对-实录.png',
                   '05_露营海报/evidence/18-dingtalk-product-table.png',
                   '06_动画示例/pelican-bike.html'):
        assert f'src="{source}"' in html, f'Missing retained/adapted illustration: {source}'
    exercise_html = (SHARE / '04_参考资料' / '01_完整练习.html').read_text('utf-8')
    for source in ('../配图/HTML工作台-改价899-实录.png',
                   '../配图/小野500-改价899-实图.png',
                   '../配图/HTML工作台2-自动导出-实录.png',
                   '../配图/工作台使用说明-实录.png',
                   '../配图/钉钉产品与海报-实录.png',
                   '../配图/钉钉MCP回读核对-实录.png'):
        assert f'src="{source}"' in exercise_html, f'Missing process evidence: {source}'
    assert TOOL_ZIP.is_file(), 'Missing final workbench download'
    import zipfile
    with zipfile.ZipFile(TOOL_ZIP) as archive:
        assert archive.testzip() is None, 'Workbench ZIP is corrupt'
        names = archive.namelist()
        assert names and all(Path(name).parts[0] == TOOL_ROOT for name in names)
        assert not any(Path(name).is_absolute() or '..' in Path(name).parts for name in names)
        required = {
            f'{TOOL_ROOT}/README.md',
            f'{TOOL_ROOT}/requirements.txt',
            f'{TOOL_ROOT}/启动小野海报工作台.command',
            f'{TOOL_ROOT}/工作台文件/xiaoye_workbench.py',
            f'{TOOL_ROOT}/工作台文件/generate_xiaoye_posters.py',
            f'{TOOL_ROOT}/工作台文件/xiaoye-workbench.html',
            f'{TOOL_ROOT}/工作台文件/xiaoye-poster-products.csv',
        }
        assert required.issubset(names), 'Workbench ZIP is missing required files'
    missing = []
    count = 0
    references = list((SHARE / '04_参考资料').glob('*.html'))
    references.append(SHARE / '03_GitHub原例' / '阅读版.html')
    paths = [SHARE / 'index.html', SHARE / 'practical.html', SHARE / '00_打开分享.html',
             *ROOT.glob('*.html'), *references,
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
            allowed_download = target == TOOL_ZIP.resolve()
            if (not target.is_file() or not target.is_relative_to(SHARE)
                    or (not allowed_download and not public_file(target))):
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
