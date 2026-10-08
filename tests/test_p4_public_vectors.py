"""Frozen public conformance observations for P3 exact-scan and output."""
import json
from pathlib import Path
import unittest

from spectral_public.core import SpectrumRecord
from spectral_public.retrieval import RetrievalQuery, retrieve, controlled_output

ROOT = Path(__file__).resolve().parent.parent


class P4PublicVectorTests(unittest.TestCase):
    def test_exact_retrieval_golden(self):
        rows = [SpectrumRecord.from_json(r) for r in json.loads((ROOT/'examples/p3_corpus.json').read_text(encoding='utf-8'))]
        query = RetrievalQuery.from_json(json.loads((ROOT/'examples/p3_query.json').read_text(encoding='utf-8')))
        result = retrieve(rows, query, method='exact')
        target = json.loads((ROOT/'conformance/p4/p3-exact.expected.json').read_text(encoding='utf-8'))
        self.assertEqual(result, target)

    def test_controlled_output_golden(self):
        rows = [SpectrumRecord.from_json(r) for r in json.loads((ROOT/'examples/p3_corpus.json').read_text(encoding='utf-8'))]
        query = RetrievalQuery.from_json(json.loads((ROOT/'examples/p3_query.json').read_text(encoding='utf-8')))
        result = retrieve(rows, query, method='exact')
        for style in ('compact', 'evidence'):
            with self.subTest(style=style):
                target = json.loads((ROOT/f'conformance/p4/p3-{style}.expected.json').read_text(encoding='utf-8'))
                self.assertEqual(controlled_output(result, style), target)


if __name__ == '__main__':
    unittest.main()
