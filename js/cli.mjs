#!/usr/bin/env node
/** ISL P4 independent Node.js command surface. No other-language runtime required. */
import { readFileSync } from 'node:fs';
import { TextDecoder } from 'node:util';
import { runP1, retrieveExact, controlledOutput } from './isl_public.mjs';

function usage(){throw new Error('Usage: node js/cli.mjs run <program.isl> | retrieve <corpus.json> <query.json> | controlled-output <corpus.json> <query.json> [compact|evidence]');}
try {
  const [, , command, ...args] = process.argv;
  // Decode input strictly: replacement characters would silently alter source text.
  const utf8 = new TextDecoder('utf-8', {fatal: true});
  const read = filename => utf8.decode(readFileSync(filename));
  let result;
  if(command==='run' && args.length===1){result=runP1(read(args[0]));}
  else if(command==='retrieve' && args.length===2){result=retrieveExact(JSON.parse(read(args[0])),JSON.parse(read(args[1])));}
  else if(command==='controlled-output' && (args.length===2||args.length===3)){
    const retrieval=retrieveExact(JSON.parse(read(args[0])),JSON.parse(read(args[1])));
    result=controlledOutput(retrieval,args[2]??'evidence');
  }else usage();
  process.stdout.write(JSON.stringify(result,null,2)+'\n');
}catch(e){console.error(`ISL JS error: ${e.message}`);process.exitCode=2;}
