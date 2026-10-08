"""Tests for the public, no-network ISL 0.1 language kernel."""
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import unittest

from spectral_public.language import ISLError, Parser, execute, parse, run, run_file, tokenize
from spectral_public.cli import main

BASE = Path(__file__).resolve().parents[1]
HEADER = 'isl 0.1;\naxis joy;\n'
META = 'text "toy"; context "toy"; provenance "manual";'
RECORD = f'record a {{ {META} joy = [0.2,0.5]; }}\n'
SECOND = f'record b {{ {META} joy = [0.4,0.8]; }}\n'


class TestISLLanguage(unittest.TestCase):
    def test_hello(self):
        data = run_file(BASE / 'examples/hello.isl')
        self.assertEqual(data['profile'], 'isl-language/0.1')
        self.assertEqual(data['axes'], ['calm', 'joy'])
        self.assertEqual(data['records'], 2)
        by_name = {out['name']: out for out in data['outputs']}
        self.assertEqual(len(by_name), 5)
        self.assertEqual(by_name['shared']['value'], {'lower': 0.75, 'upper': 0.8})
        self.assertEqual(by_name['strong_joy']['value'], ['morning'])
        self.assertEqual(by_name['combined']['type'], 'interval-set')
        self.assertTrue(0 < by_name['ranking']['value'] <= 1)

    def test_disjoint(self):
        data = run_file(BASE / 'examples/disjoint.isl')
        self.assertIsNone(data['outputs'][0]['value'])
        self.assertEqual(len(data['outputs'][1]['value']), 2)

    def test_tokenizes_utf8_in_quotes(self):
        source = HEADER + 'record a { text "臺灣"; context "測試"; provenance "手工"; joy = [0,1]; }'
        self.assertEqual(run(source)['records'], 1)

    def test_json_escape_in_string(self):
        source = HEADER + 'record a { text "line\\nsecond"; context "toy"; provenance "manual"; joy = [0,1]; }'
        self.assertEqual(run(source)['records'], 1)

    def test_blank_metadata_rejected(self):
        source = HEADER + 'record a { text " "; context "toy"; provenance "manual"; joy = [0,1]; }'
        with self.assertRaisesRegex(ISLError, 'blank'):
            run(source)

    def test_surrogate_rejected(self):
        source = HEADER + 'record a { text "\\ud800"; context "toy"; provenance "manual"; joy = [0,1]; }'
        with self.assertRaisesRegex(ISLError, 'UTF-8'):
            run(source)

    def test_malformed_json_escape_rejected(self):
        source = HEADER + 'record a { text "hello\\x"; context "toy"; provenance "manual"; joy = [0,1]; }'
        with self.assertRaises(ISLError):
            run(source)

    def test_unterminated_string_rejected(self):
        with self.assertRaisesRegex(ISLError, 'unclosed string'):
            tokenize('isl 0.1; text "unfinished\n')

    def test_invalid_character_rejected(self):
        with self.assertRaisesRegex(ISLError, 'unexpected character'):
            run(HEADER + '@;')

    def test_missing_version_rejected(self):
        with self.assertRaises(ISLError):
            parse('axis joy;')

    def test_different_version_rejected(self):
        with self.assertRaisesRegex(ISLError, 'only'):
            parse('isl 1.0;')

    def test_unclosed_record_rejected(self):
        with self.assertRaisesRegex(ISLError, 'unclosed record'):
            parse(HEADER + 'record a { text "a";')

    def test_duplicate_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'duplicate'):
            run(HEADER + 'axis joy;')

    def test_reserved_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'reserved'):
            run('isl 0.1; axis text;')

    def test_duplicate_record_rejected(self):
        with self.assertRaisesRegex(ISLError, 'duplicate'):
            run(HEADER + RECORD + RECORD)

    def test_missing_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'exactly declared axes'):
            run(HEADER + f'record a {{ {META} }}')

    def test_unknown_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'exactly declared axes'):
            run(HEADER + f'record a {{ {META} joy = [0,1]; calm = [0,1]; }}')

    def test_late_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'precede'):
            run(HEADER + RECORD + 'axis calm;')

    def test_invalid_interval_rejected(self):
        with self.assertRaises(ISLError):
            run(HEADER + f'record a {{ {META} joy = [0.8,0.2]; }}')

    def test_excessive_value_rejected(self):
        with self.assertRaisesRegex(ISLError, 'within'):
            run(HEADER + f'record a {{ {META} joy = [0,1.1]; }}')

    def test_unexpected_operator_rejected(self):
        with self.assertRaisesRegex(ISLError, 'unsupported operator'):
            parse(HEADER + 'let x = derive_truth(a,b);')

    def test_nonexistent_reference_rejected(self):
        with self.assertRaisesRegex(ISLError, 'unknown record'):
            run(HEADER + RECORD + 'let x = union(a.joy, b.joy);')

    def test_cross_axis_rejected(self):
        src = 'isl 0.1; axis joy; axis calm; ' + f'record a {{ {META} joy = [0,1]; calm = [0,1]; }}'
        with self.assertRaisesRegex(ISLError, 'same axis'):
            run(src + 'let x = intersect(a.joy,a.calm);')

    def test_filter_missing_axis_rejected(self):
        with self.assertRaisesRegex(ISLError, 'undeclared axis'):
            run(HEADER + RECORD + 'let x = filter(calm, lower >= 0.5);')

    def test_forward_print_rejected(self):
        with self.assertRaisesRegex(ISLError, 'prior'):
            run(HEADER + 'print missing;')

    def test_duplicate_let_rejected(self):
        src = HEADER + RECORD + SECOND
        with self.assertRaisesRegex(ISLError, 'duplicate'):
            run(src + 'let x = union(a.joy,b.joy); let x = union(a.joy,b.joy);')

    def test_filter_exact_boundary(self):
        src = HEADER + RECORD + SECOND + 'let filtered = filter(joy, lower >= 0.4); print filtered;'
        self.assertEqual(run(src)['outputs'][0]['value'], ['b'])

    def test_cosine_rejects_zero_vector(self):
        src = HEADER + f'record a {{ {META} joy = [0,0]; }}' + 'let sim = cosine(a,a);'
        with self.assertRaisesRegex(ISLError, 'undefined cosine'):
            run(src)

    def test_print_order_and_metadata_is_not_exposed(self):
        src = HEADER + RECORD + SECOND + 'let a1 = union(a.joy,b.joy); let b1 = intersect(a.joy,b.joy); print b1; print a1;'
        result = run(src)
        self.assertEqual([o['name'] for o in result['outputs']], ['b1','a1'])
        self.assertNotIn('manual', json.dumps(result))

    def test_no_python_execution(self):
        with self.assertRaises(ISLError):
            run('isl 0.1; __import__("os");')

    def test_lexical_comments(self):
        source = '# comment\n' + HEADER + RECORD + '# comment\n'
        self.assertEqual(run(source)['records'], 1)

    def test_invalid_corpus(self):
        for path in sorted((BASE / 'conformance/invalid').glob('*.isl')):
            with self.subTest(file=path.name):
                with self.assertRaises(ISLError):
                    run_file(path)

    def test_conformance_expected_outputs(self):
        for path in sorted((BASE / 'conformance/positive').glob('*.isl')):
            with self.subTest(file=path.name):
                expected = json.loads(path.with_suffix('.expected.json').read_text(encoding='utf-8'))
                self.assertEqual(run_file(path), expected)

    def test_cli_check_and_run(self):
        for command in ['check','run']:
            with self.subTest(command=command):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main([command, str(BASE/'examples/hello.isl')])
                self.assertEqual(code, 0, stderr.getvalue())
                self.assertTrue(json.loads(stdout.getvalue()))

    def test_cli_rejects_without_traceback(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(['run', str(BASE/'conformance/invalid/unknown-axis.isl')])
        self.assertEqual(code, 2)
        self.assertIn('ISL error', stderr.getvalue())
        self.assertNotIn('Traceback', stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
