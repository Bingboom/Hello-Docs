"""Fast offline behavior tests. Real XeLaTeX acceptance is recorded separately."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import demo


class LocalDemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('data', 'latex'):
            shutil.copytree(demo.ROOT / folder, self.root / folder)
        products = self.root / 'data/products.csv'
        rows = demo.read_csv(products, demo.PRODUCT_FIELDS)
        for row in rows:
            if row['record_id'] == 'local-500':
                row['price_cny'] = '999'
        demo.atomic_write(products, demo.csv_bytes(rows, demo.PRODUCT_FIELDS))
        (self.root / 'assets').mkdir()
        for row in demo.load_records(self.root):
            (self.root / 'assets' / row['asset']).write_bytes(b'fake test image')
        self.calls = []

    def compiler(self, root, row, version, fingerprint):
        self.calls.append(row['record_id'])
        path = Path(tempfile.mkdtemp(dir=root / '.runtime'))
        (path / 'poster.pdf').write_bytes(f'%PDF-test-{row["model_id"]}-{row["price_cny"]}-{version}'.encode())
        (path / 'preview.png').write_bytes(b'fake test preview')
        return path

    def build(self, compiler=None):
        with contextlib.redirect_stdout(io.StringIO()):
            return demo.build_once(self.root, compiler or self.compiler)

    def price(self, value='899'):
        path = self.root / 'data/products.csv'
        with contextlib.redirect_stdout(io.StringIO()):
            demo.update_product(self.root, 'local-500', {'price_cny': value}, demo.digest(path.read_bytes()))

    def state(self):
        return json.loads((self.root / '.runtime/state.json').read_text())

    def test_first_build_and_no_change_skip(self):
        self.assertEqual(len(self.build()), 3)
        self.assertEqual(self.build(), [])
        self.assertEqual(len(self.calls), 3)

    def test_only_changed_product_rebuilt(self):
        self.build()
        before = self.state()
        self.price()
        self.assertEqual(self.build(), ['local-500'])
        after = self.state()
        self.assertEqual(after['local-500']['version'], 2)
        for key in ('local-300', 'local-1000'):
            self.assertEqual(after[key], before[key])
        self.assertIn('999 → 899', after['local-500']['change_summary'])

    def test_failure_preserves_previous_artifact_and_version(self):
        self.build()
        before = self.state()['local-500']
        pdf_before = (self.root / before['pdf']).read_bytes()
        self.price()
        def fail(*_args):
            raise RuntimeError('intentional test failure')
        self.build(fail)
        after = self.state()['local-500']
        self.assertEqual(after['version'], 1)
        self.assertEqual(after['status'], 'failed')
        self.assertEqual((self.root / before['pdf']).read_bytes(), pdf_before)
        self.assertEqual(self.build(fail), [])

    def test_shared_style_updates_all(self):
        self.build()
        with (self.root / 'latex/theme.tex').open('a') as handle:
            handle.write('\n% intentional test change\n')
        self.assertEqual(len(self.build()), 3)

    def test_one_layout_change_does_not_rebuild_other_layouts(self):
        self.build()
        with (self.root / 'latex/layout_split.tex').open('a') as handle:
            handle.write('\n% intentional split layout change\n')
        self.assertEqual(self.build(), ['local-500'])

    def test_three_different_layouts_share_theme(self):
        rows = demo.load_records(self.root)
        self.assertEqual({r['layout'] for r in rows}, {'hero', 'split', 'cards'})
        for row in rows:
            self.assertTrue((self.root / 'latex' / demo.LAYOUT_FILES[row['layout']]).exists())

    def test_metadata_does_not_trigger_build(self):
        self.build()
        (self.root / 'output/records.csv').write_text('modified output metadata')
        self.assertEqual(self.build(), [])

    def test_duplicate_records_rejected(self):
        path = self.root / 'data/products.csv'
        rows = demo.read_csv(path, demo.PRODUCT_FIELDS)
        rows[1]['record_id'] = rows[0]['record_id']
        demo.atomic_write(path, demo.csv_bytes(rows, demo.PRODUCT_FIELDS))
        with self.assertRaisesRegex(ValueError, '重复记录'):
            demo.load_records(self.root)

    def test_missing_or_unknown_variable_fails(self):
        with self.assertRaisesRegex(ValueError, '未知内容变量'):
            demo.substitute('{{no_such_field}}', {'product_name': 'test'})
        with self.assertRaisesRegex(ValueError, '括号'):
            demo.substitute('{{broken', {})

    def test_tex_values_escaped(self):
        self.assertEqual(demo.tex_escape(r'50% & $5_# {x}'), r'50\% \& \$5\_\# \{x\}')
        self.assertIn(r'\textbackslash{}', demo.tex_escape(r'\input'))

    def test_concurrent_edit_rejected(self):
        with self.assertRaisesRegex(ValueError, '其他窗口'):
            demo.update_product(self.root, 'local-500', {'price_cny': '899'}, 'stale')

    def test_invalid_price_never_saved(self):
        before = (self.root / 'data/products.csv').read_bytes()
        for value in ('NaN', '-1', '0', '1e9', '999999', '12.123', ''):
            with self.assertRaises(ValueError):
                self.price(value)
        self.assertEqual((self.root / 'data/products.csv').read_bytes(), before)

    def test_superseded_snapshot_not_published(self):
        self.build()
        self.price('899')
        def change_during_compile(root, row, version, fingerprint):
            result = self.compiler(root, row, version, fingerprint)
            self.price('799')
            return result
        self.assertEqual(self.build(change_during_compile), [])
        self.assertEqual(self.state()['local-500']['version'], 1)
        self.assertEqual(self.build(), ['local-500'])
        self.assertEqual(self.state()['local-500']['source']['price_cny'], '799')

    def test_deleted_pdf_is_regenerated(self):
        self.build()
        (self.root / self.state()['local-500']['pdf']).unlink()
        self.assertEqual(self.build(), ['local-500'])


if __name__ == '__main__':
    unittest.main()
