/** P5 tests of CLI reject contract. No data leaves the local process. */
import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve} from 'node:path';

const ROOT=resolve(import.meta.dirname,'../..');
const CLI=join(ROOT,'js/cli.mjs');

test('invalid UTF-8 .isl bytes reject without successful output',()=>{
 const temp=mkdtempSync(join(tmpdir(),'isl-p5-invalid-'));
 try {
  const input=join(temp,'invalid.isl');writeFileSync(input,Buffer.from([0xff]));
  const p=spawnSync(process.execPath,[CLI,'run',input],{cwd:ROOT,encoding:'utf8'});
  assert.equal(p.status,2);assert.equal(p.stdout,'');
 }finally{rmSync(temp,{recursive:true,force:true});}
});

test('invalid UTF-8 query bytes reject without successful output',()=>{
 const temp=mkdtempSync(join(tmpdir(),'isl-p5-invalid-'));
 try {
  const input=join(temp,'invalid.json');writeFileSync(input,Buffer.from([0xff]));
  const p=spawnSync(process.execPath,[CLI,'retrieve',join(ROOT,'examples/p3_corpus.json'),input],{cwd:ROOT,encoding:'utf8'});
  assert.equal(p.status,2);assert.equal(p.stdout,'');
 }finally{rmSync(temp,{recursive:true,force:true});}
});

test('nonexistent input is infrastructure rejection, not JSON success',()=>{
 const p=spawnSync(process.execPath,[CLI,'run','this-path-does-not-exist.isl'],{cwd:ROOT,encoding:'utf8'});
 assert.equal(p.status,2);assert.equal(p.stdout,'');
});
