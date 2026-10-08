#!/usr/bin/env python3
"""Cross-language ISL Public P4 conformance runner.

This is a black-box oracle comparison; the independent JS implementation
lives in js/isl_public.mjs and does not import/call Python. This harness compares
observable JSON behavior, not diagnostic wording or exact float bit patterns.
"""
from __future__ import annotations
import copy
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from spectral_public.language import run as python_run  # noqa: E402
from spectral_public.core import SpectrumRecord  # noqa: E402
from spectral_public.retrieval import RetrievalQuery, retrieve, controlled_output  # noqa: E402

NODE = shutil.which('node')

class ConformanceError(AssertionError):
    pass


def comparable(a: object, b: object, at: str = '$') -> None:
    if isinstance(a, bool) or isinstance(b, bool):
        if type(a) is not type(b) or a != b:
            raise ConformanceError(f'{at}: boolean mismatch: {a!r} vs {b!r}')
    elif isinstance(a, (float, int)) and isinstance(b, (float, int)):
        if not (math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-12)):
            raise ConformanceError(f'{at}: numeric mismatch: {a!r} vs {b!r}')
    elif isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            raise ConformanceError(f'{at}: differing JSON keys {set(a)^set(b)}')
        for k in a:
            comparable(a[k], b[k], f'{at}.{k}')
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            raise ConformanceError(f'{at}: different list lengths {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)):
            comparable(x, y, f'{at}[{i}]')
    elif a != b or type(a) is not type(b):
        raise ConformanceError(f'{at}: value mismatch {a!r} vs {b!r}')


def invoke_node(command: str, *paths: str) -> tuple[bool, dict | None, str]:
    p = subprocess.run([NODE, str(ROOT / 'js/cli.mjs'), command, *paths],
                       capture_output=True, text=True, encoding='utf-8', timeout=15, cwd=ROOT)
    if p.returncode == 0:
        try:
            return True, json.loads(p.stdout), ''
        except json.JSONDecodeError as exc:
            raise ConformanceError(f'Node emitted non-JSON output: {exc}') from exc
    if p.returncode != 2:
        raise ConformanceError(f'Node unexpected return code {p.returncode}, stderr={p.stderr!r}')
    return False, None, p.stderr.strip()


def sample_programs():
    for file in sorted((ROOT/'conformance/positive').glob('*.isl')):
        yield file.name, file.read_text(encoding='utf-8'), True
    for file in sorted((ROOT/'conformance/invalid').glob('*.isl')):
        yield file.name, file.read_text(encoding='utf-8'), False
    r = random.Random(4132026)
    for i in range(40):
        ax = 2 + i % 4
        axes = [f'a{k}' for k in range(ax)]
        specs = []
        for name in ('first','second','third'):
            co = {}
            for a in axes:
                lo = round(r.random()*0.8, 3)
                hi = min(1.0,round(lo + r.random()*(1-lo), 3))
                co[a] = (lo, hi)
            lines = [f'  text "測試項目 {i}: {name} ✨";', f'  context "synthetic-{i}";', '  provenance "P4 seeded fixture";']
            lines += [f'  {a} = [{lo:.3f}, {hi:.3f}];' for a,(lo,hi) in co.items()]
            specs.append('record '+name+' {\n'+'\n'.join(lines)+'\n}')
        body = '\n'.join(['isl 0.1;', *(f'axis {a};' for a in axes), *specs,
                          'let x = intersect(first.a0, second.a0);', 'print x;',
                          'let y = union(first.a0, third.a0);', 'print y;',
                          f'let z = blend(first.{axes[-1]}, second.{axes[-1]}, 0.35);', 'print z;',
                          'let h = cosine(first, second);','print h;',
                          'let f = filter(a0, lower >= 0.60);','print f;'])
        yield f'seeded-{i}', body, True
    for name, value in [('duplicate-id','axis joy;\naxis joy;'), ('bad-version','isl 0.2;')]:
        yield name, ('isl 0.1;\n'+value+'\n') if name != 'bad-version' else value, False
    yield 'no-axis', 'isl 0.1; record a { text \"x\";context \"x\";provenance \"x\";}', False
    yield 'bad-alpha', 'isl 0.1; axis x; record a {text \"x\";context \"x\";provenance \"x\";x=[0.1,0.3];} let z = blend(a.x,a.x,1.3);print z;', False
    yield 'unpaired-surrogate', 'isl 0.1; axis a; record r { text "\\ud800"; context "c"; provenance "p"; a=[0.2,0.3]; }', False
    yield 'undeclared-axis', 'isl 0.1; axis x; record r { text "a"; context "b"; provenance "c"; y=[0.1,0.3];}', False
    yield 'incompatible-axis', '''isl 0.1; axis x; axis y;
record a {text "a";context "c";provenance "p"; x=[0.1,0.2];y=[0.2,0.3];}
record b {text "b";context "c";provenance "p"; x=[0.2,0.4];y=[0.5,0.6];}
let x = union(a.x,b.y);print x;''', False
    yield 'numeric-nan','isl 0.1; axis x; record a { text "a";context "b";provenance "c";x=[NaN,0.5];}',False


def sample_retrievals():
    corpus=json.loads((ROOT/'examples/p3_corpus.json').read_text(encoding='utf-8'))
    query=json.loads((ROOT/'examples/p3_query.json').read_text(encoding='utf-8'))
    yield 'original',corpus,query,True
    r=random.Random(88120)
    for j in range(27):
        n=5+j
        axes=['x','y','z'][:1+j%3]
        ctx=f'synthetic-context-{j}'
        rows=[]
        for i in range(n):
            aa={}
            for a in axes:
                lo=round(r.random()*0.9,4)
                aa[a]={'lower':lo,'upper':round(lo+r.random()*(1-lo),4)}
            rows.append({'profile':'spectrum-public/0.1','record_id':f'item{i:03d}',
                         'text':f'人工案例 {j}.{i} ✨','context':ctx,'provenance':'p4 seeded', 'axes':aa})
        rows.append({'profile':'spectrum-public/0.1','record_id':'wrong-context',
                     'text':'do not cross scope','context':'other','provenance':'p4 seeded','axes':rows[0]['axes']})
        ref=rows[0]
        q={'profile':'isl-retrieval-query/0.3','context':ctx,'axes':axes,
           'reference_id':ref['record_id'],'predicates':[
               {'axis':axes[0],'endpoint':'lower','operator':'>=','threshold':round(0.1+(j%5)*0.14,2)}],
           'max_results':1+(j%7),'exclude_reference':j%2==0}
        yield f'seeded-{j}',rows,q,True
    for name, transform in [
        ('extra-field',lambda d:d.update({'unspecified':'no'})),
        ('missing-ref',lambda d:d.update({'reference_id':'absent'})),
        ('bad-threshold',lambda d:d['predicates'][0].update({'threshold':1.2})),
        ('bad-axis',lambda d:d['predicates'][0].update({'axis':'invalid'})),
        ('bool-limit',lambda d:d.update({'max_results':True})),
        ('bad-profile',lambda d:d.update({'profile':'isl-retrieval-query/999'})),
        ('duplicate-axes',lambda d:d.update({'axes':['joy','joy']})),
    ]:
        bad=copy.deepcopy(query);transform(bad)
        yield name,corpus,bad,False
    bad_corpus=copy.deepcopy(corpus)
    bad_corpus.append(copy.deepcopy(corpus[0]))
    yield 'duplicate-corpus-ids',bad_corpus,query,False


def run_suite() -> dict:
    if NODE is None:
        raise RuntimeError('Node.js is required for P4 independent cross-language testing')
    counters={'p1_accept':0,'p1_reject':0,'p3_accept':0,'p3_reject':0,'p3_controlled':0}
    with tempfile.TemporaryDirectory(prefix='isl-p4-conformance-') as temp:
        temp=Path(temp)
        for label,program,should_succeed in sample_programs():
            source=temp/'program.isl';source.write_text(program,encoding='utf-8')
            success,result,err=invoke_node('run',str(source))
            try:py=python_run(program);py_valid=True
            except ValueError:py_valid=False;py=None
            if py_valid!=should_succeed:
                raise ConformanceError(f'P1 fixture {label}: invalid fixture expectation, python success={py_valid}')
            if success!=py_valid:
                raise ConformanceError(f'P1 {label}: Python accepts={py_valid}; JS accepts={success}; {err}')
            if py_valid:
                comparable(py,result);counters['p1_accept']+=1
            else:counters['p1_reject']+=1
        for label,corpus,query,should_succeed in sample_retrievals():
            cp=temp/'corpus.json';qp=temp/'query.json'
            cp.write_text(json.dumps(corpus,ensure_ascii=False),encoding='utf-8')
            qp.write_text(json.dumps(query,ensure_ascii=False),encoding='utf-8')
            success,result,err=invoke_node('retrieve',str(cp),str(qp))
            try:
                source_records=[SpectrumRecord.from_json(x) for x in corpus]
                py=retrieve(source_records,RetrievalQuery.from_json(query),method='exact')
                py_valid=True
            except ValueError:py_valid=False;py=None
            if py_valid!=should_succeed:
                raise ConformanceError(f'P3 fixture {label}: invalid fixture expectation, python success={py_valid}')
            if success!=py_valid:
                raise ConformanceError(f'P3 {label}: Python accepts={py_valid}; JS accepts={success}; {err}')
            if py_valid:
                comparable(py,result);counters['p3_accept']+=1
                for style in ('compact','evidence'):
                    okay,js_out,stderr=invoke_node('controlled-output',str(cp),str(qp),style)
                    if not okay:raise ConformanceError(f'P3 output {label}, {style}: {stderr}')
                    compare=controlled_output(py,style)
                    comparable(compare,js_out)
                    counters['p3_controlled']+=1
            else:counters['p3_reject']+=1
    return counters


if __name__=='__main__':
    report=run_suite()
    print('ISL P4 independent JS vs Python conformance:',json.dumps(report,sort_keys=True))
    print('P4 differential verdict: PASS')
