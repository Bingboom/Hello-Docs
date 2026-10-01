"""Capture and verify the actual local UI price-change run. Does not alter inputs."""
import argparse
import json
import re
import subprocess

import demo


def capture():
    state = demo.read_json(demo.ROOT / '.runtime/state.json', {})
    rows = demo.load_records(demo.ROOT)
    for row in rows:
        item = state[row['record_id']]
        assert item['status'] == 'success'
        assert item['input_sha256'] == demo.input_hash(demo.ROOT, row)
        assert item['pdf_sha256'] == demo.digest((demo.ROOT / item['pdf']).read_bytes())
    return {'captured_at': demo.utc_now(), 'state': state}


def verify():
    root = demo.ROOT
    before = demo.read_json(root / 'evidence/acceptance-before.json', {})
    after = capture()
    unchanged = []
    for key in ('local-300', 'local-1000'):
        assert before['state'][key] == after['state'][key]
        unchanged.append(key)
    old, new = before['state']['local-500'], after['state']['local-500']
    assert old['source']['price_cny'] == '999'
    assert new['source']['price_cny'] == '899'
    assert new['version'] == old['version'] + 1
    assert old['pdf_sha256'] != new['pdf_sha256']
    assert {r['source']['layout'] for r in after['state'].values()} == {'hero', 'split', 'cards'}
    pdf_checks = []
    for item in after['state'].values():
        pdf = root / item['pdf']
        info = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
        assert re.search(r'^Pages:\s+1$', info, re.M)
        size = re.search(r'Page size:\s+([\d.]+) x ([\d.]+) pts', info)
        assert size and abs(float(size[1]) - 419.53) < .5 and abs(float(size[2]) - 595.28) < .5
        text = subprocess.check_output(['pdftotext', '-layout', str(pdf), '-'], text=True)
        assert item['model_id'] in text and '教学虚构产品' in text
        assert re.search(r'¥\s*' + re.escape(item['source']['price_cny']) + r'\b', text)
        assert '@@' not in text and '{{' not in text
        archive = root / 'output/history' / item['model_id'] / f'v{item["version"]}'
        log = (archive / 'poster.log').read_text(errors='replace')
        assert 'Missing character:' not in log and 'Overfull \\hbox' not in log and 'Overfull \\vbox' not in log
        pdf_checks.append({'model_id': item['model_id'], 'layout': item['source']['layout'], 'version': item['version'],
                           'pages': 1, 'size': 'A5', 'price': item['source']['price_cny'], 'sha256': item['pdf_sha256']})
    events = [json.loads(line) for line in (root / 'output/events.jsonl').read_text().splitlines()]
    events = [e for e in events if e['time'] >= before['captured_at']]
    successes = [e for e in events if e['event'] == 'build_succeeded']
    assert len(successes) == 1 and successes[0]['record_id'] == 'local-500'
    assert any(e['event'] == 'data_saved' and e['record_id'] == 'local-500' for e in events)
    report = {'verified_at': demo.utc_now(), 'result': 'pass', 'scope': 'local CSV / XeLaTeX / local metadata only',
              'dingtalk_upload': 'not-performed', 'before': before, 'after': after, 'unchanged_records': unchanged,
              'pdf_checks': pdf_checks, 'events': events,
              'shared_style_sha256': demo.digest((root / 'latex/theme.tex').read_bytes()),
              'shared_components_sha256': demo.digest((root / 'latex/components.tex').read_bytes())}
    demo.save_json(root / 'evidence/acceptance.json', report)
    print(json.dumps({'result': 'pass', 'unchanged': unchanged, 'pdfs': pdf_checks}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['before', 'verify'])
    args = parser.parse_args()
    if args.command == 'before':
        target = demo.ROOT / 'evidence/acceptance-before.json'
        if target.exists():
            raise SystemExit('Baseline already exists; preserve this evidence and use another named run.')
        demo.save_json(target, capture())
        print('Captured real baseline; now change 999 to 899 in the browser.')
    else:
        verify()
