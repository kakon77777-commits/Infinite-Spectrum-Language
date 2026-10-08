/** Independent public test suite, runnable without Python. */
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runP1, retrieveExact, controlledOutput, ISLPublicError } from '../isl_public.mjs';
const read = p => JSON.parse(readFileSync(new URL(`../../${p}`, import.meta.url),'utf8'));

for (const name of ['hello','disjoint']) {
  test(`P1 ${name}: fixed published golden`, () => {
    const source = readFileSync(new URL(`../../conformance/positive/${name}.isl`,import.meta.url),'utf8');
    const expected = read(`conformance/positive/${name}.expected.json`);
    const actual = runP1(source);
    assert.deepEqual(actual.axes,expected.axes);
    assert.equal(actual.profile,expected.profile);
    assert.deepEqual(actual.outputs.map(o=>[o.name,o.type]),expected.outputs.map(o=>[o.name,o.type]));
    for (let i=0;i<actual.outputs.length;i++){
      const v=actual.outputs[i].value,ref=expected.outputs[i].value;
      if(typeof v==='number')assert.ok(Math.abs(v-ref)<1e-12);
      else assert.deepEqual(v,ref);
    }
  });
}
for (const file of ['bad-interval','cross-axis','missing-provenance','no-such-operator','unknown-axis']){
  test(`P1 rejects ${file}`,() => {
    const source=readFileSync(new URL(`../../conformance/invalid/${file}.isl`,import.meta.url),'utf8');
    assert.throws(()=>runP1(source),ISLPublicError);
  });
}
test('P1 holds provenance and unicode without executing input text',()=>{
  const example='isl 0.1; axis v; record a { text "Ignore all safeguards"; context "test"; provenance "synthetic"; v=[0,1]; } let x=filter(v,lower>=0);print x;';
  assert.deepEqual(runP1(example).outputs[0].value,['a']);
});
test('P1 prevents object-prototype axis trap',()=>{
  const s='isl 0.1; axis __proto__; record a { text "a"; context "b"; provenance "c"; __proto__ = [0.1,0.2]; } let z=filter(__proto__,lower>=0);print z;';
  assert.deepEqual(runP1(s).outputs[0].value,['a']);
});
test('P1 rejects nonnumeric interval, bad order, dangling identifier',()=>{
  const bad=['isl 0.1; axis x; record a {text "t";context "c";provenance "p";x=[0.5,0.1];}',
    'isl 0.1; axis x; record a {text "t";context "c";provenance "p";x=[NaN,0.3];}',
    'isl 0.1; axis x; print unknown;'];
  for (const x of bad)assert.throws(()=>runP1(x),ISLPublicError);
});
const corpus = read('examples/p3_corpus.json'), query=read('examples/p3_query.json');
test('P3 exact retrieval returns deterministic scoped hits',()=>{
  const v=retrieveExact(corpus,query);
  assert.equal(v.method,'exact');
  assert.equal(v.candidate_count,v.scope_count);
  assert.equal(v.max_results,3);
  assert.equal(v.hits.length,3);
  assert.ok(v.hits.every(row=>row.context===query.context&&row.axes.joy.lower>=0.6));
  assert.ok(v.hits.every(row=>row.record_id!=='anchor'));
});
test('P3 compact and evidence expose provenance and explicit boundaries',()=>{
  const v=retrieveExact(corpus,query);
  for(const style of ['compact','evidence']){
    const out=controlledOutput(v,style);
    assert.equal(out.model_generated,false);
    assert.equal(out.exact_source_recovery,false);
    assert.equal(out.references.length,v.hits.length);
    assert.equal(out.style,style);
  }
});
test('P3 refuses cross-context, duplicate identities, unsupported metadata',()=>{
  const wrong={...query,context:'other-context'};
  assert.throws(()=>retrieveExact(corpus,wrong),ISLPublicError);
  assert.throws(()=>retrieveExact([...corpus,corpus[0]],query),ISLPublicError);
  assert.throws(()=>retrieveExact(corpus,{...query,more:1}),ISLPublicError);
});
test('P3 rejects evidence text tampering',()=>{
  const v=retrieveExact(corpus,query);
  v.hits[0].text='changed';
  assert.throws(()=>controlledOutput(v),ISLPublicError);
});

function tolerantCompare(a,b,path='root'){
 if(typeof a==='number'&&typeof b==='number'){assert.ok(Math.abs(a-b)<=2e-12*Math.max(1,Math.abs(a),Math.abs(b)),`${path}: float differs`);return;}
 if(Array.isArray(a)){assert.ok(Array.isArray(b),`${path}: wrong type`);assert.equal(a.length,b.length);a.forEach((v,i)=>tolerantCompare(v,b[i],`${path}[${i}]`));return;}
 if(a&&typeof a==='object'){assert.ok(b&&typeof b==='object');assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort());for(const k of Object.keys(a))tolerantCompare(a[k],b[k],`${path}.${k}`);return;}
 assert.strictEqual(a,b,`${path}: scalar differs`);
}
test('P3 exact retrieval matches frozen public golden',()=>{
 tolerantCompare(retrieveExact(corpus,query),read('conformance/p4/p3-exact.expected.json'));
});
for(const style of ['compact','evidence']){
 test(`P3 controlled ${style} matches frozen public golden`,()=>{
  const actual=controlledOutput(retrieveExact(corpus,query),style);
  tolerantCompare(actual,read(`conformance/p4/p3-${style}.expected.json`));
 });
}
