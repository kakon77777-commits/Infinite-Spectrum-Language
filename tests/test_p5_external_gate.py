"""P5 runner self-tests; no network and no model dependency."""
import copy
import json
import math
import unittest
import shlex
import sys
from pathlib import Path

from scripts import p5_external_gate as gate
from spectral_public.language import run
from spectral_public.core import SpectrumRecord
from spectral_public.retrieval import RetrievalQuery, retrieve


class ExternalGateTests(unittest.TestCase):
    def test_fixture_hashes_pass(self):
        pinned=gate.load_manifest()
        self.assertGreaterEqual(len(pinned['sha256']), 10)
        self.assertFalse(pinned['independent_external_audit_completed'])

    def test_manifest_tampering_is_rejected(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            target=Path(d)/'MANIFEST.json'
            original=gate.load_manifest()
            manipulated=copy.deepcopy(original)
            key=next(iter(manipulated['sha256']))
            manipulated['sha256'][key]='0'*64
            target.write_text(json.dumps(manipulated),encoding='utf-8')
            with patch.object(gate,'MANIFEST_PATH',target), self.assertRaises(gate.GateError):
                gate.load_manifest()

    def test_manifest_unpinned_case_rejected(self):
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as d:
            target=Path(d)/'MANIFEST.json'
            manipulated=copy.deepcopy(gate.load_manifest())
            manipulated['sha256']['conformance/invalid/unpinned.isl']='0'*64
            target.write_text(json.dumps(manipulated),encoding='utf-8')
            with patch.object(gate,'MANIFEST_PATH',target), self.assertRaises(gate.GateError):
                gate.load_manifest()

    def test_fixed_reference_cases_count(self):
        fixtures=gate.fixed_cases()
        self.assertEqual(sum(case.profile == 'p1' and case.accepted for case in fixtures),2)
        self.assertEqual(sum(case.profile.startswith('controlled') for case in fixtures),2)
        self.assertEqual(sum(case.profile == 'p3' and case.accepted for case in fixtures),1)

    def test_comparison_nonfinite_rejected(self):
        with self.assertRaises(gate.GateError):
            gate.matches(1.0,float('nan'))
        with self.assertRaises(gate.GateError):
            gate.matches(1.0,float('inf'))

    def test_bool_is_not_number(self):
        with self.assertRaises(gate.GateError):
            gate.matches(True,1)
        with self.assertRaises(gate.GateError):
            gate.matches(0,False)

    def test_float_tolerance(self):
        gate.matches({'a':0.42},{'a':0.42 + 1e-13})
        with self.assertRaises(gate.GateError):
            gate.matches(0.42,0.4201)

    def test_key_sets_array_order_and_types(self):
        with self.assertRaises(gate.GateError):
            gate.matches({'a':1},{'a':1,'b':2})
        with self.assertRaises(gate.GateError):
            gate.matches(['a','b'],['b','a'])
        with self.assertRaises(gate.GateError):
            gate.matches('1',1)

    def test_strict_json(self):
        self.assertEqual(gate.strict_json('{"a":true}'),{'a':True})
        for raw in ['{"a":1,"a":2}', '{"a":NaN}','{not json}', '[1,2] trailing']:
            with self.subTest(raw=raw),self.assertRaises(gate.GateError):
                gate.strict_json(raw)

    def test_command_template_has_required_placeholders(self):
        case=gate.fixed_cases()[0]
        artifacts={'source':Path('/tmp/isl-test-source.isl')}
        self.assertEqual(gate.prepare_command('python run.py {source}',artifacts,case),
                         ['python','run.py','/tmp/isl-test-source.isl'])
        for command in ['python run.py', 'python run.py {query}', 'python run.py {source} {query}']:
            with self.subTest(command=command), self.assertRaises(gate.GateError):
                gate.prepare_command(command,artifacts,case)

    def test_fake_success_backend_cannot_pass(self):
        from tempfile import TemporaryDirectory
        case = next(c for c in gate.fixed_cases() if c.profile == 'p1' and c.accepted)
        fake_code = "print('{}')"
        command = f'{shlex.quote(sys.executable)} -c {shlex.quote(fake_code)} {{source}}'
        with TemporaryDirectory() as d, self.assertRaises(gate.GateError):
            gate.invoke(command, case, Path(d), 10.0, gate.ROOT)

    def test_seeded_p1_oracle_vs_python(self):
        for c in gate.p1_seeded(777,10):
            with self.subTest(case=c.name):
                observed=run(c.artifacts['source'].decode('utf-8'))
                gate.matches(c.expected,observed)

    def test_seeded_p3_oracle_vs_python(self):
        for c in gate.p3_seeded(919,10):
            with self.subTest(case=c.name):
                corpus=json.loads(c.artifacts['corpus'])
                query=json.loads(c.artifacts['query'])
                actual=retrieve([SpectrumRecord.from_json(row) for row in corpus],
                                RetrievalQuery.from_json(query),method='exact')
                gate.matches(c.expected,actual)

    def test_generated_cases_reproducible(self):
        a=gate.p1_seeded(12,3)+gate.p3_seeded(12,3)
        b=gate.p1_seeded(12,3)+gate.p3_seeded(12,3)
        self.assertEqual(a,b)
        c=gate.p1_seeded(13,3)+gate.p3_seeded(13,3)
        self.assertNotEqual(a,c)

    def test_rejected_cases_have_no_success_expected(self):
        for case in gate.p3_bad_cases():
            self.assertFalse(case.accepted)
            self.assertIsNone(case.expected)
        self.assertTrue(any(case.artifacts.get('query')==b'\xff' for case in gate.p3_bad_cases()))


if __name__ == '__main__':
    unittest.main()
