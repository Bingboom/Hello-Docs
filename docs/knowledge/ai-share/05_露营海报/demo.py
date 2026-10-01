#!/usr/bin/env python3
"""Local teaching app: CSV -> shared LaTeX components -> versioned PDF.

No DingTalk credentials, network uploads or production Auto-Manual imports.
Run: python3 demo.py serve    (browser + 2-second change detector)
     python3 demo.py build    (one explicit build pass)
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile
import threading
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
DATA_LOCK = threading.RLock()
PRODUCT_FIELDS = ('record_id', 'model_id', 'product_name', 'capacity_wh',
                  'rated_power_w', 'weight_kg', 'price_cny', 'asset', 'data_note', 'layout')
COPY_FIELDS = ('model_id', 'tagline', 'introduction_template', 'scene')
LAYOUT_FILES = {'hero': 'layout_hero.tex', 'split': 'layout_split.tex', 'cards': 'layout_cards.tex'}
FIELD_LABELS = {'price_cny': '教学价', 'product_name': '产品名', 'capacity_wh': '容量',
                'rated_power_w': '额定输出', 'weight_kg': '重量', 'tagline': '副标题',
                'introduction_template': '介绍模板', 'scene': '场景', 'asset': '插画', 'layout': '版式'}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode('utf-8')
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def read_json(path, default):
    return json.loads(path.read_text('utf-8')) if path.exists() else default


def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def read_csv(path, fields):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(f'{path.name}: 表头必须是 {",".join(fields)}')
        rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError(f'{path.name}: 存在空表或不完整行')
    return rows


def validate_text(value, limit, label):
    if not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f'{label}: 需要 1–{limit} 个字符，不能含换行或控制字符')


def validate_product(row):
    for key in ('record_id', 'model_id'):
        if not re.fullmatch(r'[A-Za-z0-9-]{1,40}', row[key]):
            raise ValueError(f'{key}: 只允许字母、数字和短横线')
    validate_text(row['product_name'], 12, '产品名')
    for key in ('capacity_wh', 'rated_power_w', 'weight_kg', 'price_cny'):
        try:
            number = Decimal(row[key])
        except InvalidOperation as exc:
            raise ValueError(f'{key}: 必须是数字') from exc
        if not number.is_finite() or number <= 0 or number > 99999:
            raise ValueError(f'{key}: 必须大于 0 且不超过 99999')
        if not re.fullmatch(r'\d{1,5}(\.\d{1,2})?', row[key]):
            raise ValueError(f'{key}: 最多两位小数')
    if not re.fullmatch(r'[A-Za-z0-9-]+\.png', row['asset']):
        raise ValueError('插画必须是 assets 下的 PNG 文件名')
    if row['data_note'] != '教学虚构数据，非真实产品参数':
        raise ValueError('必须保留教学虚构数据标记')
    if row['layout'] not in LAYOUT_FILES:
        raise ValueError('版式必须是 hero、split 或 cards')


def substitute(text, values):
    def replace(match):
        key = match.group(1)
        if key not in values:
            raise ValueError(f'未知内容变量: {key}')
        return values[key]
    result = re.sub(r'\{\{([A-Za-z0-9_]+)\}\}', replace, text)
    if '{{' in result or '}}' in result:
        raise ValueError('内容变量括号不完整')
    return result


def load_records(root):
    with DATA_LOCK:
        products = read_csv(root / 'data/products.csv', PRODUCT_FIELDS)
        copies = read_csv(root / 'data/content.csv', COPY_FIELDS)
    if len({r['model_id'] for r in copies}) != len(copies):
        raise ValueError('内容表存在重复型号')
    if len({r['model_id'] for r in products}) != len(products):
        raise ValueError('产品表存在重复型号')
    if len({r['record_id'] for r in products}) != len(products):
        raise ValueError('产品表存在重复记录 ID')
    copy_map = {r['model_id']: r for r in copies}
    if set(copy_map) != {r['model_id'] for r in products}:
        raise ValueError('产品表与内容表的型号必须一一对应')
    records = []
    for product in products:
        validate_product(product)
        row = {**product, **copy_map[product['model_id']]}
        validate_text(row['tagline'], 18, '副标题')
        validate_text(row['scene'], 8, '场景')
        validate_text(row['introduction_template'], 140, '介绍模板')
        row['introduction'] = substitute(row['introduction_template'], product)
        validate_text(row['introduction'], 90, '介绍正文')
        records.append(row)
    return records


def tex_escape(text):
    replacements = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
                    '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
                    '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(replacements.get(c, c) for c in str(text))


def input_hash(root, row):
    files = [root / 'latex' / n for n in ('poster.tex', 'theme.tex', 'components.tex')]
    files.append(root / 'latex' / LAYOUT_FILES[row['layout']])
    files += [root / 'assets' / row['asset'], Path(__file__)]
    # Metadata lives outside input tables and never participates in this digest.
    content = json.dumps(row, sort_keys=True, ensure_ascii=False).encode('utf-8')
    for path in files:
        content += path.name.encode() + path.read_bytes()
    return digest(content)


def event(root, kind, **details):
    entry = {'time': utc_now(), 'event': kind, **details}
    path = root / 'output/events.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(json.dumps(entry, ensure_ascii=False), flush=True)


def compile_pdf(root, row, version, fingerprint):
    engine = shutil.which('xelatex')
    if not engine:
        raise RuntimeError('缺少 XeLaTeX，请安装 TeX Live 或 MacTeX')
    run_dir = Path(tempfile.mkdtemp(prefix=f'{row["model_id"]}-', dir=root / '.runtime'))
    for name in ('theme.tex', 'components.tex'):
        shutil.copy2(root / 'latex' / name, run_dir / name)
    shutil.copy2(root / 'assets' / row['asset'], run_dir / 'art.png')
    values = {**row, 'version': version, 'build_date': datetime.now().strftime('%Y-%m-%d')}
    for target, source in [('poster.tex', 'poster.tex'), ('layout.tex', LAYOUT_FILES[row['layout']])]:
        tex = (root / 'latex' / source).read_text('utf-8')
        tex = re.sub(r'@@([a-z_]+)@@', lambda m: tex_escape(values[m.group(1)]), tex)
        atomic_write(run_dir / target, tex)
    command = [engine, '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'poster.tex']
    outputs = []
    for _pass in range(2):
        result = subprocess.run(command, cwd=run_dir, capture_output=True, timeout=60)
        outputs.append(result.stdout + result.stderr)
        if result.returncode:
            break
    atomic_write(run_dir / 'command.log', b'\n'.join(outputs))
    pdf = run_dir / 'poster.pdf'
    log = (run_dir / 'poster.log').read_text('utf-8', errors='replace') if (run_dir / 'poster.log').exists() else ''
    if result.returncode or not pdf.exists():
        raise RuntimeError(f'XeLaTeX 编译失败；日志: {run_dir.name}/command.log')
    if 'Missing character:' in log or 'Overfull \\hbox' in log or 'Overfull \\vbox' in log:
        raise RuntimeError(f'排版检查失败（缺字或溢出）；日志: {run_dir.name}/poster.log')
    info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True, check=True)
    if not re.search(r'^Pages:\s+1$', info.stdout, re.M):
        raise RuntimeError('成品必须只有一页')
    subprocess.run(['pdftoppm', '-singlefile', '-scale-to', '1300', '-png', str(pdf), str(run_dir / 'preview')], check=True, capture_output=True, timeout=30)
    save_json(run_dir / 'source.json', {'record': row, 'input_sha256': fingerprint,
                                      'version': version, 'command': command, 'created_at': utc_now()})
    return run_dir


def publish_status(root, state, error=''):
    status = {'mode': 'local-only', 'dingtalk': 'not-connected', 'error': error,
              'records': list(state.values())}
    save_json(root / 'output/status.json', status)
    fields = ('record_id', 'model_id', 'version', 'status', 'updated_at', 'change_summary',
              'pdf', 'pdf_sha256', 'input_sha256', 'error')
    atomic_write(root / 'output/records.csv', csv_bytes(state.values(), fields))


def build_once(root=ROOT, compiler=compile_pdf):
    (root / '.runtime').mkdir(exist_ok=True)
    with (root / '.runtime/build.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return []
        state_path = root / '.runtime/state.json'
        state = read_json(state_path, {})
        try:
            records = load_records(root)
        except (ValueError, OSError) as exc:
            publish_status(root, state, str(exc))
            if read_json(root / '.runtime/error.json', '') != str(exc):
                event(root, 'input_error', error=str(exc))
                save_json(root / '.runtime/error.json', str(exc))
            return []
        save_json(root / '.runtime/error.json', '')
        changed = []
        for row in records:
            key = row['record_id']
            previous = state.get(key, {})
            fingerprint = ''
            try:
                fingerprint = input_hash(root, row)
                current_pdf = root / previous.get('pdf', '.missing')
                intact = current_pdf.is_file() and digest(current_pdf.read_bytes()) == previous.get('pdf_sha256')
                if fingerprint == previous.get('input_sha256') and intact:
                    if previous.get('status') != 'success':
                        previous.update(status='success', error='')
                    continue
                if fingerprint == previous.get('failed_sha256') and time.time() < previous.get('retry_after', 0):
                    continue
                version = previous.get('version', 0) + 1
                old_row = previous.get('source', {})
                differences = [f'{FIELD_LABELS.get(k,k)}：{old_row[k]} → {v}'
                               for k, v in row.items() if k != 'introduction' and k in old_row and old_row[k] != v]
                summary = '；'.join(differences) or ('首次生成' if not previous.get('version') else '样式、插画或构建器更新 / 文件修复')
                event(root, 'build_started', record_id=key, model_id=row['model_id'], version=version,
                      input_sha256=fingerprint, change_summary=summary)
                state[key] = {**previous, 'record_id': key, 'model_id': row['model_id'], 'status': 'building', 'error': ''}
                publish_status(root, state)
                run_dir = compiler(root, row, version, fingerprint)
                latest = {r['record_id']: r for r in load_records(root)}
                if key not in latest or input_hash(root, latest[key]) != fingerprint:
                    state[key] = {**previous, 'record_id': key, 'model_id': row['model_id'], 'status': 'pending'}
                    event(root, 'superseded', record_id=key)
                    continue
                destination = root / 'output/history' / row['model_id'] / f'v{version}'
                destination.parent.mkdir(parents=True, exist_ok=True)
                # Keep every attempted/versioned bundle; never replace an existing archive.
                if destination.exists():
                    raise RuntimeError(f'历史版本已存在: {destination.name}，请检查本地状态')
                shutil.copytree(run_dir, destination)
                pdf_rel = f'output/pdf/{row["model_id"]}.pdf'
                atomic_write(root / pdf_rel, (run_dir / 'poster.pdf').read_bytes())
                atomic_write(root / f'output/previews/{row["model_id"]}.png', (run_dir / 'preview.png').read_bytes())
                state[key] = {'record_id': key, 'model_id': row['model_id'], 'version': version,
                              'status': 'success', 'updated_at': utc_now(), 'change_summary': summary,
                              'pdf': pdf_rel, 'pdf_sha256': digest((root / pdf_rel).read_bytes()),
                              'input_sha256': fingerprint, 'source': row, 'error': ''}
                event(root, 'build_succeeded', **{k: state[key][k] for k in ('record_id','model_id','version','pdf','pdf_sha256','input_sha256','change_summary')})
                changed.append(key)
            except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
                state[key] = {**previous, 'record_id': key, 'model_id': row['model_id'],
                              'status': 'failed', 'error': str(exc), 'failed_sha256': fingerprint,
                              'retry_after': time.time() + 30}
                event(root, 'build_failed', record_id=key, error=str(exc), previous_pdf_preserved=bool(previous.get('pdf')))
            finally:
                save_json(state_path, state)
                publish_status(root, state)
        publish_status(root, state)
        save_json(state_path, state)
        return changed


def update_product(root, record_id, changes, expected_hash):
    allowed = {'price_cny', 'product_name', 'capacity_wh', 'rated_power_w', 'weight_kg'}
    if not changes or set(changes) - allowed:
        raise ValueError('只允许修改产品数据字段')
    with DATA_LOCK:
        path = root / 'data/products.csv'
        if digest(path.read_bytes()) != expected_hash:
            raise ValueError('数据已被其他窗口修改，请刷新后重试')
        rows = read_csv(path, PRODUCT_FIELDS)
        match = [r for r in rows if r['record_id'] == record_id]
        if len(match) != 1:
            raise ValueError('记录 ID 必须唯一且存在')
        match[0].update({k: str(v) for k, v in changes.items()})
        validate_product(match[0])
        atomic_write(path, csv_bytes(rows, PRODUCT_FIELDS))
    # Deliberately no build call here. The independent worker detects this write.
    event(root, 'data_saved', record_id=record_id, changed_fields=list(changes))


def serve(root, port, interval):
    token = secrets.token_urlsafe(24)
    stop = threading.Event()
    def worker():
        while not stop.is_set():
            try:
                build_once(root)
            except Exception as exc:
                event(root, 'worker_error', error=str(exc))
            stop.wait(interval)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def reply(self, code, body, content_type='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def host_ok(self):
            return self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}

        def do_GET(self):
            if not self.host_ok():
                return self.reply(403, {'error': '仅允许本机访问'})
            path = unquote(urlparse(self.path).path)
            if path == '/api/state':
                error = ''
                try:
                    rows = load_records(root)
                except (ValueError, OSError) as exc:
                    rows, error = [], str(exc)
                status = read_json(root / 'output/status.json', {'records': []})
                logs = root / 'output/events.jsonl'
                events = [json.loads(line) for line in logs.read_text('utf-8').splitlines()[-20:]] if logs.exists() else []
                return self.reply(200, {'products': rows, 'status': status, 'error': error,
                                        'events': events, 'interval': interval, 'token': token,
                                        'csv_hash': digest((root / 'data/products.csv').read_bytes())})
            relative = 'web/index.html' if path == '/' else path.lstrip('/')
            target = (root / relative).resolve()
            if not target.is_relative_to(root) or relative.split('/')[0] not in {'web','assets','output','data','latex'}:
                return self.reply(404, {'error': '文件不存在'})
            if not target.is_file():
                return self.reply(404, {'error': '文件不存在'})
            mime = mimetypes.guess_type(target.name)[0] or 'text/plain'
            self.reply(200, target.read_bytes(), mime)

        def do_POST(self):
            if (not self.host_ok() or self.headers.get('X-Demo-Token') != token
                    or self.headers.get('Content-Type') != 'application/json'):
                return self.reply(403, {'error': '本地请求校验失败'})
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 10000:
                    raise ValueError('请求大小不合法')
                payload = json.loads(self.rfile.read(size))
                path = urlparse(self.path).path
                if path != '/api/product':
                    return self.reply(404, {'error': '接口不存在'})
                update_product(root, payload['record_id'], payload['changes'], payload['csv_hash'])
                self.reply(200, {'saved': True, 'message': '已保存 CSV，等待自动检测'})
            except (ValueError, KeyError, TypeError) as exc:
                self.reply(400, {'error': str(exc)})

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print(f'LOCAL ONLY: http://127.0.0.1:{port} (每 {interval} 秒检测输入；未连接钉钉)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        thread.join(timeout=65)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'serve'])
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--interval', type=float, default=2)
    args = parser.parse_args()
    if args.interval < 1:
        parser.error('--interval must be at least 1 second')
    if args.command == 'build':
        build_once()
        status = read_json(ROOT / 'output/status.json', {})
        raise SystemExit(1 if status.get('error') or any(r['status'] != 'success' for r in status.get('records', [])) else 0)
    serve(ROOT, args.port, args.interval)
