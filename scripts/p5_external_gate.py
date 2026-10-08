#!/usr/bin/env python3
"""ISL P5 portable conformance gate for independently supplied command-line runtimes.

Standard-library only. It never imports spectral_public, calls the bundled Node
implementation, or uses reference code to compute expected values. The runner
executes only an explicit locally trusted command provided by its caller.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / 'conformance/p5/MANIFEST.json'
ATOL = 2e-12
RTOL = 2e-12


class GateError(ValueError):
    """Malformed public fixtures, unexpected implementation behavior, or config."""


def strict_json(text: str) -> object:
    def no_constant(value: str) -> None:
        raise GateError(f'invalid JSON non-finite numeric constant: {value}')

    def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
        obj: dict = {}
        for k, v in pairs:
            if k in obj:
                raise GateError(f'duplicate JSON key: {k}')
            obj[k] = v
        return obj

    try:
        return json.loads(text, parse_constant=no_constant, object_pairs_hook=unique_pairs)
    except json.JSONDecodeError as exc:
        raise GateError(f'output must be one strict JSON value: {exc}') from exc


def matches(expected: object, observed: object, path: str = '$') -> None:
    """Exact types/order/keys except finite JSON numbers within P4 tolerance."""
    if isinstance(expected, bool) or isinstance(observed, bool):
        if type(expected) is not type(observed) or expected != observed:
            raise GateError(f'{path}: boolean mismatch')
    elif type(expected) in (int, float) and type(observed) in (int, float):
        if not (math.isfinite(expected) and math.isfinite(observed)
                and math.isclose(expected, observed, rel_tol=RTOL, abs_tol=ATOL)):
            raise GateError(f'{path}: numeric mismatch {expected!r} != {observed!r}')
    elif isinstance(expected, dict) and isinstance(observed, dict):
        if expected.keys() != observed.keys():
            raise GateError(f'{path}: JSON keys differ ({set(expected) ^ set(observed)})')
        for key in expected:
            matches(expected[key], observed[key], f'{path}.{key}')
    elif isinstance(expected, list) and isinstance(observed, list):
        if len(expected) != len(observed):
            raise GateError(f'{path}: array length differs')
        for index, (x, y) in enumerate(zip(expected, observed)):
            matches(x, y, f'{path}[{index}]')
    elif type(expected) is not type(observed) or expected != observed:
        raise GateError(f'{path}: value mismatch {expected!r} != {observed!r}')


def load_manifest() -> dict:
    data = strict_json(MANIFEST_PATH.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('profile') != 'isl-external-conformance/0.5':
        raise GateError('invalid P5 manifest profile')
    paths = data.get('sha256')
    if not isinstance(paths, dict) or len(paths) < 10:
        raise GateError('P5 manifest must pin public fixture bytes')
    public_fixture_paths = {p.relative_to(ROOT).as_posix() for folder, pattern in (
        ('conformance/positive', '*.isl'), ('conformance/positive', '*.expected.json'),
        ('conformance/invalid', '*.isl'))
        for p in (ROOT / folder).glob(pattern)}
    public_fixture_paths.update(('examples/p3_corpus.json', 'examples/p3_query.json',
                                 'conformance/p4/p3-exact.expected.json',
                                 'conformance/p4/p3-evidence.expected.json',
                                 'conformance/p4/p3-compact.expected.json'))
    if set(paths) != public_fixture_paths:
        raise GateError('manifest fixture set differs from the frozen public fixture set')
    for name, digest in paths.items():
        if (not isinstance(name, str) or name.startswith('/') or '..' in Path(name).parts
                or not isinstance(digest, str) or len(digest) != 64):
            raise GateError('invalid P5 manifest path or digest')
        path = ROOT / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise GateError(f'fixture hash mismatch: {name}')
    return data


@dataclass(frozen=True)
class Case:
    name: str
    profile: str
    accepted: bool
    artifacts: dict[str, bytes]
    expected: dict | None = None


def json_bytes(data: object) -> bytes:
    return (json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',', ':')) + '\n').encode('utf-8')


def fixed_cases() -> list[Case]:
    cases = []
    for file in sorted((ROOT / 'conformance/positive').glob('*.isl')):
        expected = strict_json(file.with_suffix('.expected.json').read_text(encoding='utf-8'))
        cases.append(Case('positive/' + file.stem, 'p1', True, {'source': file.read_bytes()}, expected))
    for file in sorted((ROOT / 'conformance/invalid').glob('*.isl')):
        cases.append(Case('invalid/' + file.stem, 'p1', False, {'source': file.read_bytes()}))
    corpus = (ROOT / 'examples/p3_corpus.json').read_bytes()
    query = (ROOT / 'examples/p3_query.json').read_bytes()
    cases.append(Case('p3/exact-golden', 'p3', True, {'corpus': corpus, 'query': query},
                      strict_json((ROOT / 'conformance/p4/p3-exact.expected.json').read_text(encoding='utf-8'))))
    for style in ('compact', 'evidence'):
        cases.append(Case('p3/' + style + '-golden', 'controlled-' + style, True,
                          {'corpus': corpus, 'query': query},
                          strict_json((ROOT / f'conformance/p4/p3-{style}.expected.json').read_text(encoding='utf-8'))))
    return cases


def interval(a: float, b: float) -> dict:
    return {'lower': a, 'upper': b}


def p1_seeded(seed: int, count: int) -> list[Case]:
    """Independent numerical oracle for the public tiny P1 operator subset."""
    rng = random.Random(seed)
    cases = []
    for n in range(count):
        axes = [f'a{k}' for k in range(2 + n % 3)]
        records = {}
        lines = ['isl 0.1;', *(f'axis {a};' for a in axes)]
        for record in ('alpha', 'beta', 'gamma'):
            values = {}
            body = [f'  text "合成語句 {n} {record} 星 ✨";', f'  context "seed-{seed}-{n}";',
                    '  provenance "P5 synthesized; not empirical";']
            for a in axes:
                lo = round(rng.random() * 0.8, 4)
                hi = round(lo + rng.random() * (1 - lo), 4)
                values[a] = (lo, hi)
                body.append(f'  {a} = [{lo:.4f}, {hi:.4f}];')
            records[record] = values
            lines.append('record ' + record + ' {\n' + '\n'.join(body) + '\n}')
        threshold = round(0.2 + (n % 5) * 0.15, 2)
        lines.extend([
            'let intersection = intersect(alpha.a0, beta.a0);', 'print intersection;',
            'let unioned = union(alpha.a0, beta.a0);', 'print unioned;',
            f'let blended = blend(alpha.a1, gamma.a1, 0.35);', 'print blended;',
            'let similarity = cosine(alpha, beta);', 'print similarity;',
            f'let selected = filter(a0, lower >= {threshold:.2f});', 'print selected;'
        ])
        a, b = records['alpha']['a0'], records['beta']['a0']
        lo, hi = max(a[0], b[0]), min(a[1], b[1])
        shared = interval(lo, hi) if lo <= hi else None
        first, second = sorted((a, b))
        unioned = ([interval(*first), interval(*second)] if first[1] < second[0]
                   else [interval(first[0], max(first[1], second[1]))])
        a1, g1 = records['alpha']['a1'], records['gamma']['a1']
        blended = interval(0.35*a1[0] + 0.65*g1[0], 0.35*a1[1] + 0.65*g1[1])
        va = [(records['alpha'][axis][0] + records['alpha'][axis][1])/2 for axis in axes]
        vb = [(records['beta'][axis][0] + records['beta'][axis][1])/2 for axis in axes]
        dot = sum(u*v for u, v in zip(va, vb))
        norm = math.sqrt(sum(u*u for u in va)*sum(v*v for v in vb))
        similarity = dot/norm
        selected = [record for record in ('alpha','beta','gamma') if records[record]['a0'][0] >= threshold]
        outputs = [
            {'name':'intersection','type':'interval-or-empty','value':shared},
            {'name':'unioned','type':'interval-set','value':unioned},
            {'name':'blended','type':'interval','value':blended},
            {'name':'similarity','type':'heuristic-similarity','value':similarity},
            {'name':'selected','type':'record-selection','value':selected},
        ]
        expected = {'profile':'isl-language/0.1', 'axes':sorted(axes), 'records':3,'outputs':outputs}
        cases.append(Case(f'seeded/p1-{n:03d}', 'p1', True,
                          {'source': ('\n'.join(lines)+'\n').encode('utf-8')}, expected))
    return cases


def p3_expected(corpus: list[dict], query: dict) -> dict:
    """Independent exhaustive numeric oracle; no runtime package imports."""
    axes = query['axes']
    lookup = {r['record_id']: r for r in corpus}
    reference = lookup[query['reference_id']]
    scoped = [r for r in corpus if r['context'] == query['context'] and set(r['axes']) == set(axes)]
    ref_vector = [(reference['axes'][a]['lower']+reference['axes'][a]['upper'])/2 for a in sorted(axes)]
    eligible = []
    for row in scoped:
        if query['exclude_reference'] and row['record_id'] == query['reference_id']:
            continue
        if any((row['axes'][p['axis']][p['endpoint']] < p['threshold'] if p['operator'] == '>='
                else row['axes'][p['axis']][p['endpoint']] > p['threshold']) for p in query['predicates']):
            continue
        vector = [(row['axes'][a]['lower']+row['axes'][a]['upper'])/2 for a in sorted(axes)]
        norm = math.sqrt(sum(a*a for a in ref_vector)*sum(b*b for b in vector))
        if norm == 0:
            continue
        score = sum(a*b for a,b in zip(ref_vector, vector))/norm
        eligible.append((score, row))
    eligible.sort(key=lambda value: (-value[0], value[1]['record_id']))
    hits = []
    for score, row in eligible[:query['max_results']]:
        digest = hashlib.sha256(b'ISL-P3-RECORD-TEXT\0'+row['text'].encode('utf-8')).hexdigest()
        hits.append({'record_id':row['record_id'], 'midpoint_cosine':score,
                     'text':row['text'], 'text_sha256':digest,
                     'context':row['context'], 'provenance':row['provenance'],
                     'axes':{a:row['axes'][a] for a in axes}})
    return {'profile':'isl-retrieval-results/0.3', 'method':'exact','parameters':None,
            'scope':{'context':query['context'],'axes':axes},'reference_id':query['reference_id'],
            'predicates':query['predicates'],'max_results':query['max_results'],
            'excluded_reference':query['exclude_reference'], 'scope_count':len(scoped),
            'candidate_count':len(scoped),'matched_count':len(eligible),'hits':hits,
            'boundary':'numerical heuristic; no logical entailment, truth, calibrated probability, or exact source recovery'}


def p3_seeded(seed: int, count: int) -> list[Case]:
    rng = random.Random(seed + 873)
    cases = []
    for n in range(count):
        axes = ['z','x'] if n % 2 else ['x','z']
        scope = f'p5-synthetic/context-{n}'
        corpus = []
        for k in range(6 + n % 5):
            coordinates = {}
            for a in axes:
                lo = round(0.05 + rng.random()*0.83, 4)
                hi = round(lo + rng.random()*(1-lo), 4)
                coordinates[a] = interval(lo,hi)
            if k == 4 and n % 3 == 0:
                coordinates = {a:interval(0.0,0.0) for a in axes}
            if k == 5 and n % 3 == 1:
                coordinates = dict(reversed(list(coordinates.items())))
            corpus.append({'profile':'spectrum-public/0.1','record_id':f'r{n:02d}-{k:02d}',
                           'text':f'合成文字 {n} / {k} 🌙','context':scope,
                           'provenance':'P5 generated synthetic fixtures; no empirical ground truth',
                           'axes':coordinates})
        corpus.append({'profile':'spectrum-public/0.1','record_id':f'r{n:02d}-offscope',
                       'text':'other context','context':'unrelated',
                       'provenance':'P5 synthetic','axes':copy.deepcopy(corpus[1]['axes'])})
        query = {'profile':'isl-retrieval-query/0.3','context':scope,'axes':axes,
                 'reference_id':corpus[0]['record_id'],'predicates':[{'axis':'x',
                   'endpoint':'upper' if n%2 else 'lower','operator':'<=' if n%2 else '>=',
                   'threshold':round(0.25 + n%4*.15,2)}],
                 'max_results':2+n%4,'exclude_reference':n%2==0}
        expected = p3_expected(corpus,query)
        cases.append(Case(f'seeded/p3-{n:03d}','p3',True,
                          {'corpus':json_bytes(corpus),'query':json_bytes(query)},expected))
    return cases


def p3_bad_cases() -> list[Case]:
    corpus = strict_json((ROOT/'examples/p3_corpus.json').read_text(encoding='utf-8'))
    query = strict_json((ROOT/'examples/p3_query.json').read_text(encoding='utf-8'))
    cases = []
    for name, transform in (
        ('invalid-profile', lambda q: q.update({'profile':'unknown'})),
        ('missing-reference', lambda q: q.update({'reference_id':'missing'})),
        ('nonfinite-threshold', lambda q: q['predicates'][0].update({'threshold':2.0})),
        ('invalid-predicate-axis', lambda q: q['predicates'][0].update({'axis':'missing'})),
        ('boolean-limit', lambda q: q.update({'max_results':True})),
        ('unknown-field', lambda q: q.update({'undocumented':'no'})),
    ):
        q=copy.deepcopy(query);transform(q)
        cases.append(Case('rejected/p3-'+name,'p3',False,
                          {'corpus':json_bytes(corpus),'query':json_bytes(q)}))
    c=copy.deepcopy(corpus);c.append(copy.deepcopy(c[0]))
    cases.append(Case('rejected/p3-duplicate-id','p3',False,
                      {'corpus':json_bytes(c),'query':json_bytes(query)}))
    cases.append(Case('rejected/p3-malformed-json','p3',False,
                      {'corpus':json_bytes(corpus),'query':b'{invalid json'}))
    cases.append(Case('rejected/p3-invalid-utf8','p3',False,
                      {'corpus':json_bytes(corpus),'query':b'\xff'}))
    cases.append(Case('rejected/p1-invalid-utf8','p1',False,{'source':b'\xff'}))
    return cases


def prepare_command(template: str, artifacts: dict[str, Path], case: Case) -> list[str]:
    try:
        argv = shlex.split(template, posix=True)
    except ValueError as exc:
        raise GateError(f'invalid command template: {exc}') from exc
    if not argv:
        raise GateError('empty command template')
    placeholders = {'source','corpus','query','style'}
    required = {'p1':{'source'},'p3':{'corpus','query'},
                'controlled-compact':{'corpus','query','style'},
                'controlled-evidence':{'corpus','query','style'}}[case.profile]
    observed = {name for name in placeholders if '{'+name+'}' in template}
    if observed != required:
        raise GateError(f'{case.profile}: template placeholders must be exactly {sorted(required)}, got {sorted(observed)}')
    values = {k:str(v) for k,v in artifacts.items()}
    if case.profile.startswith('controlled'):
        values['style'] = case.profile.removeprefix('controlled-')
    substituted = []
    for token in argv:
        for key, value in values.items():
            token = token.replace('{' + key + '}', value)
        substituted.append(token)
    return substituted


def invoke(template: str, case: Case, temp: Path, timeout: float, cwd: Path) -> dict | None:
    stem = f'item-{hashlib.sha256(case.name.encode("utf-8")).hexdigest()[:12]}'
    artifacts = {}
    for key, content in case.artifacts.items():
        suffix = '.isl' if key == 'source' else '.json'
        path = temp / f'{stem}-{key}{suffix}'
        path.write_bytes(content)
        artifacts[key] = path
    argv = prepare_command(template, artifacts, case)
    try:
        result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                                encoding='utf-8', errors='strict', timeout=timeout, check=False)
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise GateError(f'{case.name}: process failed or timed out: {exc}') from exc
    if len(result.stdout) > 1_000_000 or len(result.stderr) > 1_000_000:
        raise GateError(f'{case.name}: excessive process output')
    if case.accepted:
        if result.returncode != 0:
            raise GateError(f'{case.name}: expected accept, exit={result.returncode}, diagnostic={result.stderr[:300]!r}')
        parsed = strict_json(result.stdout)
        if not isinstance(parsed,dict):
            raise GateError(f'{case.name}: expected object JSON')
        matches(case.expected, parsed)
        return parsed
    if result.returncode != 2:
        raise GateError(f'{case.name}: expected rejected input (exit 2), got {result.returncode}')
    if result.stdout.strip():
        raise GateError(f'{case.name}: rejected input must not emit JSON success to stdout')
    return None


def run_gate(args: argparse.Namespace) -> dict:
    manifest = load_manifest()
    tests = fixed_cases() + p1_seeded(args.seed,args.p1_cases) + p3_seeded(args.seed,args.p3_cases) + p3_bad_cases()
    counts = {'p1_positive':0,'p1_negative':0,'p3_positive':0,'p3_negative':0,'controlled_positive':0}
    workdir = Path(args.workdir).resolve() if args.workdir else ROOT
    if not workdir.is_dir():
        raise GateError(f'workdir does not exist: {workdir}')
    with tempfile.TemporaryDirectory(prefix='isl-p5-external-') as d:
        for case in tests:
            template = (args.run_cmd if case.profile=='p1' else args.retrieve_cmd if case.profile=='p3'
                        else args.controlled_cmd)
            invoke(template, case, Path(d), args.timeout, workdir)
            key = ('p1_' if case.profile == 'p1' else 'p3_' if case.profile=='p3' else 'controlled_')
            key += ('positive' if case.accepted else 'negative')
            counts[key] += 1
    report = {'profile':'isl-external-gate-result/0.5','status':'PASS',
              'manifest_sha256':hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),
              'seed':args.seed, 'counts':counts,'total':len(tests),
              'external_audit_completed':False,
              'scope':'black-box runtime conformance to bounded synthetic P1/P3 profiles only'}
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x',encoding='utf-8') as f:
            json.dump(report,f,ensure_ascii=False,indent=2)
            f.write('\n')
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='ISL P5 independent, offline black-box CLI conformance gate')
    parser.add_argument('--run-cmd',required=True, help='trusted command template, must use {source}')
    parser.add_argument('--retrieve-cmd',required=True,help='trusted command template, must use {corpus} {query}')
    parser.add_argument('--controlled-cmd',required=True,help='trusted command template, must use {corpus} {query} {style}')
    parser.add_argument('--workdir',help='subprocess working directory; defaults to repository root')
    parser.add_argument('--timeout',type=float,default=12.0)
    parser.add_argument('--seed',type=int,default=502026)
    parser.add_argument('--p1-cases',type=int,default=8)
    parser.add_argument('--p3-cases',type=int,default=6)
    parser.add_argument('--report',help='write report to a NEW JSON file (no overwrite)')
    args=parser.parse_args(argv)
    if not math.isfinite(args.timeout) or not 1 <= args.timeout <= 120:
        parser.error('--timeout must be between 1 and 120 seconds')
    if not 0 <= args.seed <= 2**32-1 or not 0 <= args.p1_cases <= 64 or not 0 <= args.p3_cases <= 64:
        parser.error('seed or case counts outside bounds')
    try:
        result=run_gate(args)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (GateError,OSError,UnicodeError) as exc:
        print('ISL P5 conformance FAIL: '+str(exc),file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
