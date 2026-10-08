import json
from pathlib import Path
import unittest
from spectral_public import (Interval, SpectrumRecord, SpectrumError, intersection,union,blend,midpoint_cosine,exact_axis_filter)

class TestIntervalCore(unittest.TestCase):
    def setUp(self):
        self.p = Path(__file__).resolve().parents[1]
        self.records = [SpectrumRecord.from_json(x) for x in json.loads((self.p/'examples/records.json').read_text(encoding='utf-8'))]

    def test_example(self): self.assertEqual(len(self.records),2)
    def test_reject_invalid_bounds(self):
        for pair in [(-1,1),(0,1.01),(.8,.7),(float('nan'),.5)]:
            with self.assertRaises(SpectrumError): Interval(*pair)
    def test_reject_bool(self):
        with self.assertRaises(SpectrumError): Interval(True,1)
    def test_intersect(self): self.assertEqual(intersection(Interval(.2,.5),Interval(.4,.9)),Interval(.4,.5))
    def test_intersection_empty(self): self.assertIsNone(intersection(Interval(.2,.3),Interval(.4,.5)))
    def test_union_disjoint_preserved(self): self.assertEqual(union(Interval(.1,.2),Interval(.8,.9)),[Interval(.1,.2),Interval(.8,.9)])
    def test_union_touching_merged(self): self.assertEqual(union(Interval(.1,.2),Interval(.2,.9)),[Interval(.1,.9)])
    def test_blend(self): self.assertEqual(blend(Interval(.2,.4),Interval(.6,.8),.5),Interval(.4,.6000000000000001))
    def test_blend_reject_weight(self):
        with self.assertRaises(SpectrumError): blend(Interval(0,1),Interval(0,1),1.1)
    def test_cosine_symmetric(self): self.assertAlmostEqual(midpoint_cosine(*self.records),midpoint_cosine(*self.records[::-1]))
    def test_cosine_requires_same_axes(self):
        a=self.records[0]; b=SpectrumRecord('id','text','ctx','prov',{'other':Interval(.5,.8)})
        with self.assertRaises(SpectrumError): midpoint_cosine(a,b)
    def test_exact_query(self): self.assertEqual([r.record_id for r in exact_axis_filter(self.records,'joy',.7)],['toy-001'])
    def test_zero_vector_cosine_rejected(self):
        r=SpectrumRecord('id','text','ctx','prov',{'z':Interval(0,0)})
        with self.assertRaises(SpectrumError): midpoint_cosine(r,r)
    def test_no_unknown_record_fields(self):
        raw=json.loads((self.p/'examples/records.json').read_text(encoding='utf-8'))[0]
        raw['secret']='noise'
        with self.assertRaises(SpectrumError): SpectrumRecord.from_json(raw)

if __name__=='__main__': unittest.main()
