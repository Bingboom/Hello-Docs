#!/usr/bin/env python3
"""Freeze accepted PDFs and build a portable, public-safe sharing bundle."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
SHARE = ROOT.parent
# User-approved link displayed in the sharing article; no upload credentials.
PUBLIC_TABLE_URL = ('https://alidocs.dingtalk.com/i/nodes/'
                    'oP0MALyR8k75ewkwSDQoEkxn83bzYmDO?entrance=data&sheetId=e84ttux')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    report = json.loads((ROOT / 'evidence/acceptance.json').read_text('utf-8'))
    assert report['result'] == 'pass'
    destination = ROOT / 'deliverables'
    destination.mkdir(exist_ok=True)
    entries = []
    for check in report['pdf_checks']:
        model = check['model_id']
        pdf = ROOT / 'output/pdf' / f'{model}.pdf'
        if sha(pdf) != check['sha256']:
            raise ValueError(f'{model}: current PDF differs from accepted snapshot')
        entry = dict(check)
        for extension, source in [('pdf', pdf), ('png', ROOT / 'output/previews' / f'{model}.png')]:
            target = destination / f'{model}.{extension}'
            if target.exists() and sha(target) != sha(source):
                raise ValueError(f'Refusing to overwrite a different frozen file: {target.name}')
            shutil.copy2(source, target)
            entry[extension + '_sha256'] = sha(target)
        entries.append(entry)
    manifest = {'scope': 'accepted local teaching snapshot; no DingTalk upload',
                'verified_at': report['verified_at'], 'files': entries}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def public_file(path):
    relative = path.relative_to(SHARE)
    if any(part.startswith('.') or part in {'__pycache__', 'node_modules'} for part in relative.parts):
        return False
    if path.suffix in {'.pyc', '.zip'} or path.name in {'AGENTS.md', 'CLAUDE.md'}:
        return False
    if relative.parts[0] != ROOT.name:
        return True
    inside = path.relative_to(ROOT)
    if inside.parts[0] == 'output' or path.name == '钉钉私有交接.md':
        return False
    if path.name.startswith('dingtalk-'):
        return False
    if inside.parts[0] == 'evidence' and path.suffix == '.png':
        return path.name.startswith(('10-', '11-', '12-', '13-', '15-', '16-', '17-', '18-'))
    return True


def main():
    freeze()
    target = ROOT / '小野露营市集-分享素材包.zip'
    paths = sorted(p for p in SHARE.rglob('*') if p.is_file() and not p.is_symlink() and public_file(p))
    # Fail closed if private coordinates accidentally enter a public text file.
    private_note = ROOT / '钉钉私有交接.md'
    private_markers = []
    if private_note.exists():
        private_markers = [value.encode() for value in re.findall(
            r'https://alidocs\.dingtalk\.com/i/nodes/([A-Za-z0-9]+)', private_note.read_text('utf-8'))]
    for path in paths:
        if path.suffix in {'.md', '.html', '.txt', '.json', '.csv'}:
            payload = path.read_bytes()
            for approved in (PUBLIC_TABLE_URL, PUBLIC_TABLE_URL.replace('&', '&amp;')):
                payload = payload.replace(approved.encode(), b'APPROVED_PUBLIC_TABLE_LINK')
            if any(marker in payload for marker in private_markers):
                raise ValueError(f'Private workspace coordinate in public material: {path.name}')
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, Path('AI分享-露营海报案例') / path.relative_to(SHARE))
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    print(f'{target}\n{len(paths)} files, {target.stat().st_size:,} bytes; '
          'approved table link only; no private bindings or runtime files')


if __name__ == '__main__':
    main()
