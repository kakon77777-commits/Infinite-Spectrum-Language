/**
 * ISL P4 independent JavaScript/Node reference.
 * Implements the public P1 .isl 0.1 grammar and P3 exhaustive retrieval profile.
 * No Python runtime or dependency and no access to internal language systems.
 * All scores are numerical annotations, never logical entailment or proof.
 */
import { createHash } from 'node:crypto';

export class ISLPublicError extends Error {
  constructor(message) { super(message); this.name = 'ISLPublicError'; }
}
function fail(message) { throw new ISLPublicError(message); }
const IDENT = /^[A-Za-z_][A-Za-z_0-9]*$/;
const REQUIRED_FIELDS = ['text', 'context', 'provenance'];
const OPS = new Set(['intersect', 'union', 'blend', 'cosine', 'filter']);
const RESERVED = new Set([...OPS, ...REQUIRED_FIELDS]);
const has = (o, key) => Object.prototype.hasOwnProperty.call(o, key);
function isPlain(o) { return o !== null && typeof o === 'object' && !Array.isArray(o) && (Object.getPrototypeOf(o) === Object.prototype || Object.getPrototypeOf(o) === null); }
function exactFields(o, expected, label) {
  if (!isPlain(o) || Object.keys(o).length !== expected.length || expected.some(k => !has(o,k))) fail(`${label}: invalid fields`);
  return o;
}
function validString(s, label, max = 100000) {
  if (typeof s !== 'string' || !s.trim() || [...s].length > max || /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(s)) fail(`${label}: expected bounded, valid UTF-8 text`);
  return s;
}
function unitNumber(n, label = 'spectrum coordinate') {
  if (typeof n !== 'number' || !Number.isFinite(n) || n < 0 || n > 1) fail(`${label}: must be finite in [0,1]`);
  return n;
}
function interval(value) {
  exactFields(value, ['lower', 'upper'], 'interval');
  const lo = unitNumber(value.lower), hi = unitNumber(value.upper);
  if (lo > hi) fail('interval lower > upper');
  return { lower: lo, upper: hi };
}
function intersect(a,b) {
  const lo=Math.max(a.lower,b.lower),hi=Math.min(a.upper,b.upper);
  return lo<=hi?{lower:lo,upper:hi}:null;
}
function union(a,b) {
  const [x,y] = a.lower < b.lower || (a.lower===b.lower && a.upper<=b.upper)?[a,b]:[b,a];
  return x.upper < y.lower ? [x,y] : [{lower:x.lower,upper:Math.max(x.upper,y.upper)}];
}
function blend(a,b,alpha) {
  unitNumber(alpha, 'alpha');
  return {lower:alpha*a.lower+(1-alpha)*b.lower,upper:alpha*a.upper+(1-alpha)*b.upper};
}
function midpoint(v) { return (v.lower+v.upper)/2; }
function cosine(a,b) {
  const ak=Object.keys(a.axes).sort(),bk=Object.keys(b.axes).sort();
  if (JSON.stringify(ak)!==JSON.stringify(bk)) fail('cosine: axes differ');
  const x=ak.map(k=>midpoint(a.axes[k])), y=ak.map(k=>midpoint(b.axes[k]));
  const denom=Math.sqrt(x.reduce((s,v)=>s+v*v,0)*y.reduce((s,v)=>s+v*v,0));
  if (!denom) fail('cosine: zero midpoint vector');
  return x.reduce((s,v,i)=>s+v*y[i],0)/denom;
}
function tokens(source) {
  if (typeof source !== 'string') fail('source must be a UTF-8 string');
  const result=[]; let pos=0, line=1, col=1;
  const add=(kind,value)=>result.push({kind,value,line,column:col});
  while(pos<source.length) {
    const c=source[pos];
    if (/\s/.test(c)) { if(c==='\n'){line++;col=1;}else col++;pos++;continue; }
    if (c==='#') {while(pos<source.length && source[pos]!=='\n'){pos++;col++;}continue;}
    if(c==='"') {
      let j=pos+1;
      while(j<source.length){
        if(source[j]==='\\'){j+=2;continue;}
        if(source[j]==='"')break;
        if(source[j]==='\n'||source[j]==='\r')fail(`${line}:${col}: unclosed string`);
        j++;
      }
      if(j>=source.length)fail(`${line}:${col}: unclosed string`);
      const raw=source.slice(pos,j+1);let v;
      try{v=JSON.parse(raw);}catch{fail(`${line}:${col}: invalid JSON string`);}
      // JSON.parse admits lone surrogate escapes; Python reference rejects their UTF-8 export.
      if (/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(v)) fail(`${line}:${col}: invalid UTF-8 string`);
      add('STRING',v);col+=raw.length;pos=j+1;continue;
    }
    if (source.startsWith('>=',pos)){add('>=','>=');pos+=2;col+=2;continue;}
    const remaining=source.slice(pos);
    const num=/^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?/.exec(remaining);
    if (num) { add('NUMBER',num[0]);pos+=num[0].length;col+=num[0].length;continue; }
    const ident=/^[A-Za-z_][A-Za-z_0-9]*/.exec(remaining);
    if (ident){add('ID',ident[0]);pos+=ident[0].length;col+=ident[0].length;continue;}
    if ('{}[](),;.='.includes(c)){add(c,c);pos++;col++;continue;}
    fail(`${line}:${col}: unsupported character ${c}`);
  }
  result.push({kind:'EOF',value:'',line,column:col});
  return result;
}
class P1Parser {
  constructor(source){this.ts=tokens(source);this.i=0;}
  get here(){return this.ts[this.i];}
  take(kind,value){const t=this.here;if(t.kind!==kind||(value!==undefined&&t.value!==value))fail(`${t.line}:${t.column}: expected ${kind}${value?' '+value:''}`);this.i++;return t;}
  word(s){return this.take('ID',s);}
  num(){const t=this.take('NUMBER');const n=Number(t.value);unitNumber(n,`${t.line}:${t.column}`);return n;}
  ref(){const name=this.take('ID').value;this.take('.');return [name,this.take('ID').value];}
  call(){const t=this.take('ID');if(!OPS.has(t.value))fail(`${t.line}:${t.column}: unknown operator ${t.value}`);this.take('(');let args;
    if(t.value==='cosine'){const a=this.take('ID').value;this.take(',');args=[a,this.take('ID').value];}
    else if(t.value==='filter'){const a=this.take('ID').value;this.take(',');this.word('lower');this.take('>=');args=[a,this.num()];}
    else{const a=this.ref();this.take(',');const b=this.ref();args=[a,b];if(t.value==='blend'){this.take(',');args.push(this.num());}}
    this.take(')');return {kind:t.value,args,line:t.line};
  }
  record(){const t=this.word('record');const name=this.take('ID').value;this.take('{');const meta=Object.create(null),axes=Object.create(null);
    while(this.here.kind!=='}'){
      if(this.here.kind==='EOF')fail(`${this.here.line}: record unclosed`);
      const k=this.take('ID').value;
      if(REQUIRED_FIELDS.includes(k)){
        if(has(meta,k))fail(`duplicate metadata ${k}`);
        meta[k]=validString(this.take('STRING').value,k,Number.MAX_SAFE_INTEGER);
      }else{
        this.take('=');this.take('[');const lower=this.num();this.take(',');const upper=this.num();this.take(']');
        if(has(axes,k))fail(`duplicate record axis ${k}`);axes[k]=interval({lower,upper});
      }
      this.take(';');
    }
    this.take('}');if(REQUIRED_FIELDS.some(k=>!has(meta,k)))fail(`${t.line}: missing record metadata`);
    return {type:'record',name,meta,axes,line:t.line};
  }
  parse(){this.word('isl');this.take('NUMBER','0.1');this.take(';');const statements=[];
    while(this.here.kind!=='EOF'){
      const t=this.here;if(t.kind!=='ID')fail(`${t.line}: statement expected`);
      if(t.value==='axis'){this.word('axis');const name=this.take('ID').value;this.take(';');statements.push({type:'axis',name,line:t.line});}
      else if(t.value==='record')statements.push(this.record());
      else if(t.value==='let'){this.word('let');const name=this.take('ID').value;this.take('=');const call=this.call();this.take(';');statements.push({type:'let',name,call,line:t.line});}
      else if(t.value==='print'){this.word('print');const name=this.take('ID').value;this.take(';');statements.push({type:'print',name,line:t.line});}
      else fail(`${t.line}: unknown statement ${t.value}`);
    }
    return statements;
  }
}
export function runP1(source){
  const statements=new P1Parser(source).parse();const axisSet=new Set(),records=new Map(),bindings=new Map(),seen=new Set(),output=[];let started=false;
  function axisOf([r,a]){if(!records.has(r)||!has(records.get(r).axes,a))fail(`unavailable record axis ${r}.${a}`);return records.get(r).axes[a];}
  for(const s of statements){
    if(s.type==='axis'){
      if(started||axisSet.has(s.name)||REQUIRED_FIELDS.includes(s.name))fail(`${s.line}: invalid or repeated axis ${s.name}`);
      axisSet.add(s.name);
    }else if(s.type==='record'){
      started=true;
      if(seen.has(s.name)||axisSet.has(s.name)||OPS.has(s.name))fail('duplicate/reserved record name');
      if(!axisSet.size||Object.keys(s.axes).length!==axisSet.size||Object.keys(s.axes).some(k=>!axisSet.has(k)))fail('record axes differ from declarations');
      records.set(s.name,{...s.meta,axes:s.axes});seen.add(s.name);
    }else if(s.type==='let'){
      started=true;if(seen.has(s.name)||axisSet.has(s.name)||OPS.has(s.name))fail('duplicate/reserved binding name');
      let kind,value;const [a,b,c]=s.call.args;
      if(['intersect','union','blend'].includes(s.call.kind)){
        if(a[1]!==b[1])fail('incompatible axes');
        const x=axisOf(a),y=axisOf(b);
        if(s.call.kind==='intersect'){kind='interval-or-empty';value=intersect(x,y);}
        else if(s.call.kind==='union'){kind='interval-set';value=union(x,y);}
        else{kind='interval';value=blend(x,y,c);}
      }else if(s.call.kind==='cosine'){
        if(!records.has(a)||!records.has(b))fail('unknown cosine record');
        kind='heuristic-similarity';value=cosine(records.get(a),records.get(b));
      }else{
        if(!axisSet.has(a))fail('undeclared filter axis');
        kind='record-selection';value=[...records].filter(([,r])=>r.axes[a].lower>=b).map(([id])=>id);
      }
      bindings.set(s.name,{kind,value});seen.add(s.name);
    }else{
      started=true;if(!bindings.has(s.name))fail('unbound print');
      const {kind,value}=bindings.get(s.name);output.push({name:s.name,type:kind,value});
    }
  }
  return {profile:'isl-language/0.1',axes:[...axisSet].sort(),records:records.size,outputs:output};
}

const RAW_PROFILE='spectrum-public/0.1', QUERY_PROFILE='isl-retrieval-query/0.3';
function rawRecord(obj){
  exactFields(obj,['profile','record_id','text','context','provenance','axes'],'record');
  if(obj.profile!==RAW_PROFILE)fail('invalid record profile');
  for(const k of ['record_id','text','context','provenance'])validString(obj[k],k,k==='record_id'?256:100000);
  if(!isPlain(obj.axes)||Object.keys(obj.axes).length<1||Object.keys(obj.axes).length>256)fail('invalid axes');
  for(const [key,val] of Object.entries(obj.axes)){if(!IDENT.test(key))fail('invalid axis name');interval(val);}
  return obj;
}
function parsedQuery(obj){
  exactFields(obj,['profile','context','axes','reference_id','predicates','max_results','exclude_reference'],'query');
  if(obj.profile!==QUERY_PROFILE)fail('invalid query profile');
  validString(obj.context,'context',4096);validString(obj.reference_id,'reference_id',256);
  if(!Array.isArray(obj.axes)||obj.axes.length<1||obj.axes.length>256||new Set(obj.axes).size!==obj.axes.length||obj.axes.some(x=>typeof x!=='string'||!IDENT.test(x)))fail('invalid axes list');
  if(!Array.isArray(obj.predicates)||obj.predicates.length>64)fail('invalid predicates');
  for(const p of obj.predicates){
    exactFields(p,['axis','endpoint','operator','threshold'],'predicate');
    if(!obj.axes.includes(p.axis)||!['lower','upper'].includes(p.endpoint)||!['>=','<='].includes(p.operator))fail('invalid predicate');
    unitNumber(p.threshold,'threshold');
  }
  if(!Number.isInteger(obj.max_results)||obj.max_results<1||obj.max_results>100||typeof obj.exclude_reference!=='boolean')fail('invalid query limits');
  return obj;
}
function textSha(text){return createHash('sha256').update('ISL-P3-RECORD-TEXT\0','utf8').update(text,'utf8').digest('hex');}
export function retrieveExact(corpus, query){
  if(!Array.isArray(corpus)||corpus.length<1||corpus.length>100000)fail('corpus size invalid');
  const lookup=new Map();for(const row of corpus){rawRecord(row);if(lookup.has(row.record_id))fail('duplicate ID');lookup.set(row.record_id,row);}
  const q=parsedQuery(query),reference=lookup.get(q.reference_id);
  if(!reference)fail('no reference record');
  const matchingAxes=r=>Object.keys(r.axes).length===q.axes.length&&q.axes.every(a=>has(r.axes,a));
  if(reference.context!==q.context||!matchingAxes(reference))fail('reference scope mismatched');
  if(q.axes.every(a=>midpoint(reference.axes[a])===0))fail('zero reference vector');
  const scoped=[...lookup.values()].filter(r=>r.context===q.context&&matchingAxes(r));
  const matches=[];
  for(const row of scoped){
    if(q.exclude_reference&&row.record_id===q.reference_id)continue;
    if(!q.predicates.every(p=>p.operator==='>='?row.axes[p.axis][p.endpoint]>=p.threshold:row.axes[p.axis][p.endpoint]<=p.threshold))continue;
    if(q.axes.every(a=>midpoint(row.axes[a])===0))continue;
    const score=cosine(reference,row);matches.push({score,row});
  }
  matches.sort((a,b)=> b.score-a.score||(a.row.record_id<b.row.record_id?-1:a.row.record_id>b.row.record_id?1:0));
  const hits=matches.slice(0,q.max_results).map(({score,row})=>({
    record_id:row.record_id,midpoint_cosine:score,text:row.text,text_sha256:textSha(row.text),
    context:row.context,provenance:row.provenance,
    axes:Object.fromEntries(q.axes.map(a=>[a,row.axes[a]]))
  }));
  return {
    profile:'isl-retrieval-results/0.3',method:'exact',parameters:null,
    scope:{context:q.context,axes:q.axes},reference_id:q.reference_id,
    predicates:q.predicates,max_results:q.max_results,excluded_reference:q.exclude_reference,
    scope_count:scoped.length,candidate_count:scoped.length,matched_count:matches.length,
    hits,boundary:'numerical heuristic; no logical entailment, truth, calibrated probability, or exact source recovery'
  };
}
export function controlledOutput(result,style='evidence'){
  if(!isPlain(result)||result.profile!=='isl-retrieval-results/0.3'||!['evidence','compact'].includes(style)||!Array.isArray(result.hits)||result.hits.length>100)fail('malformed retrieval result');
  const keys=['record_id','midpoint_cosine','text','text_sha256','context','provenance','axes'];
  for(const h of result.hits){exactFields(h,keys,'hit');if(typeof h.record_id!=='string'||typeof h.text!=='string'||typeof h.text_sha256!=='string'||textSha(h.text)!==h.text_sha256)fail('invalid source text digest');}
  const text=style==='compact'?`Numerical candidates: ${result.hits.length?result.hits.map(x=>x.record_id).join(', '):'none'}`:
    ['ISL P3 numerical candidates (not logical conclusions):',...result.hits.map(h=>`[${h.record_id}] midpoint cosine=${h.midpoint_cosine.toFixed(6)}; source_provenance=${h.provenance}; stored_text=${JSON.stringify(h.text)}`),...(result.hits.length?[]:['No matching records.'])].join('\n');
  return {profile:'isl-controlled-output/0.3',style,kind:'deterministic-template',text,
    references:result.hits.map(h=>({record_id:h.record_id,text_sha256:h.text_sha256,provenance:h.provenance})),
    model_generated:false,exact_source_recovery:false,
    boundary:'references point to stored fields, not a byte-exact reconstruction of original source artifacts'};
}
