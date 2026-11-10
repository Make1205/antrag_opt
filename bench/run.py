#!/usr/bin/env python3
"""Offline benchmark orchestrator; Python 3.8+ standard library only."""
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / 'bench'
SETS = json.loads((BENCH / 'inventory.json').read_text())
FLAGS = ['-O3', '-march=native', '-DNDEBUG', '-std=gnu11']
REF = ['-include', 'bench/config_ref.h', '-fno-tree-vectorize', '-fno-tree-slp-vectorize']
PAPER = {'1s': 'n=512, q=3329; 768/591', '3s': 'n=768, q=3329; 1152/883',
         '5s': 'n=1024, q=3329; 1536/1176'}
ENV = dict(os.environ, LANG='C', LC_ALL='C')
# Use the system compiler and its normal include/library search paths.
for name in ('CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH',
             'GCC_EXEC_PREFIX', 'COMPILER_PATH', 'LD_LIBRARY_PATH'):
    ENV.pop(name, None)
GCC = '/usr/bin/gcc'

def call(args, cwd=ROOT, logfile=None):
    p = subprocess.run([str(a) for a in args], cwd=str(cwd), env=ENV,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if logfile:
        with logfile.open('a') as f:
            f.write('$ ' + ' '.join(str(a) for a in args) + '\n' + p.stdout)
    if p.returncode:
        raise RuntimeError('Command failed (%s): %s\n%s' % (p.returncode, args, p.stdout[-6000:]))
    return p.stdout

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def build(row, variant, out):
    stage = out / 'work' / (row['parameter_set'] + '-' + variant)
    stage.mkdir(parents=True)
    for d in ('antrag', 'falcon', 'ntru', 'tests'):
        shutil.copytree(ROOT / d, stage / d,
                        ignore=shutil.ignore_patterns('*.o', '*.d', '*.sage.py'))
    shutil.copytree(BENCH / 'params' / row['parameter_set'], stage / 'gen')
    (stage / 'bench').mkdir()
    for n in ('driver.c', 'config_ref.h', 'cpucycles.c', 'cpucycles.h', 'speed_print.c', 'speed_print.h'):
        shutil.copy2(BENCH / n, stage / 'bench' / n)
    flags = FLAGS + (REF if variant == 'ref' else [])
    log = out / (row['parameter_set'] + '-' + variant + '-build.log')
    sources = sorted(str(p.relative_to(stage)) for d in ('antrag','falcon','ntru')
                     for p in (stage/d).glob('*.c') if p.name not in ('main.c','cpucycles.c'))
    objects = []
    for s in sources + ['bench/driver.c', 'bench/cpucycles.c', 'bench/speed_print.c']:
        obj = s.replace('/', '_') + '.o'
        call([GCC] + flags + ['-c', s, '-o', obj], stage, log)
        objects.append(obj)
    call([GCC] + objects + ['-lm','-lgmp','-o','driver'], stage, log)
    # Existing meaningful unit tests, for both configurations and every set.
    for name, deps in [('ntt', []), ('poly', objects[:-3]),
                       ('rns', objects[:-3])]:
        call([GCC]+flags+['tests/'+name+'_test.c']+deps+['-lm','-lgmp','-o',name+'_test'], stage, log)
        call([stage/(name+'_test')], stage, out/'selftests.log')
    return stage / 'driver'

def main():
    if sys.version_info < (3,8):
        raise RuntimeError('Python 3.8+ required')
    if not Path(GCC).is_file():
        raise RuntimeError('System /usr/bin/gcc and GMP development headers/library required')
    if not sys.platform.startswith('linux') or os.uname().machine != 'x86_64':
        raise RuntimeError('The requested RDTSC/AVX2 benchmark requires Linux x86-64')
    cpuinfo = Path('/proc/cpuinfo').read_text()
    features = set(re.search(r'^flags\s*:\s*(.*)$',cpuinfo,re.M)[1].split())
    if not {'avx2','fma'} <= features:
        raise RuntimeError('Host must support AVX2 and FMA to test both builds')
    # Pin timing and correctness children; compilation also inherits affinity.
    allowed = sorted(os.sched_getaffinity(0))
    cpu = int(os.environ.get('BENCH_CPU', allowed[0]))
    if cpu not in allowed:
        raise RuntimeError('BENCH_CPU is outside the allowed CPU set')
    os.sched_setaffinity(0,{cpu})
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    out = BENCH/'results'/stamp
    out.mkdir(parents=True)
    print('Results:',out,flush=True)
    metadata = {'commit':call(['git','rev-parse','HEAD']).strip(),
                'status':call(['git','status','--porcelain']).strip(),
                'cpu':re.search(r'^model name\s*:\s*(.*)$',cpuinfo,re.M)[1],
                'gcc':call([GCC,'--version']).splitlines()[0], 'cpu_affinity':cpu,
                'flags':{'ref':FLAGS+REF,'avx2':FLAGS},
                'link_flags':['-lm','-lgmp'], 'iterations':10001,
                'timing_source_commit':'bba9534a3c5cbef66481cd6518d786e23ae601b5',
                'parameters':SETS}
    metadata['source_sha256'] = {str(p.relative_to(ROOT)):sha(p)
        for d in ('antrag','falcon','ntru','tests') for p in sorted((ROOT/d).glob('*'))
        if p.suffix in ('.c','.h')}
    metadata['bench_sha256'] = {str(p.relative_to(ROOT)):sha(p)
        for p in sorted(BENCH.glob('*')) if p.is_file()}
    (out/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    manifest = json.loads((BENCH/'params.sha256.json').read_text())
    for path, expected in manifest.items():
        if sha(BENCH/path) != expected:
            raise RuntimeError('Generated parameter header checksum mismatch: '+path)
    binaries = {}
    for row in SETS:
        for variant in ('ref','avx2'):
            key=(row['parameter_set'],variant)
            print('Build + unit tests:',*key,flush=True)
            binaries[key]=build(row,variant,out)
    # Finish all correctness checks before starting any performance run.
    correctness=[]
    for row in SETS:
        name=row['parameter_set']; files={}
        size=row['pk']+row['sk']+row['sig']
        for v in ('ref','avx2'):
            f=out/'work'/(name+'-'+v+'.vectors'); files[v]=f
            call([binaries[name,v],'generate',f],logfile=out/'correctness.log')
            if f.stat().st_size != 100*size:
                raise RuntimeError('Wrong vector count/size')
        a=files['ref'].read_bytes(); b=files['avx2'].read_bytes()
        equal={k:0 for k in ('pk','sk','sig')}
        for i in range(100):
            off=i*size
            for k in ('pk','sk','sig'):
                n=row[k]; equal[k]+=int(a[off:off+n]==b[off:off+n]); off+=n
        for v,other in [('ref','avx2'),('avx2','ref')]:
            call([binaries[name,v],'check',files[other]],logfile=out/'correctness.log')
        correctness.append({'set':name,'cases':100,'equal':equal,
                            'cross_verified_each_direction':100,
                            'foreign_sk_verified_each_direction':100})
        print('Correctness:',name,equal,'cross 100/100 both directions',flush=True)
    (out/'correctness.json').write_text(json.dumps(correctness,indent=2)+'\n')
    results=[]; lengths=[]
    for row in SETS:
        for v in ('ref','avx2'):
            name=row['parameter_set']
            print('Timing (10001 operations each):',name,v,flush=True)
            text=call([binaries[name,v],'time'],logfile=out/(name+'-'+v+'-timing.log'))
            meta=re.search(r'META (\d+) (\d+) (\d+) (\d+) (\d+)',text)
            if list(map(int,meta.groups())) != [row[k] for k in ('n','q','pk','sk','sig')]:
                raise RuntimeError('Runtime parameter metadata mismatch')
            for op in ('KeyGen','Sign','Verify','ExpandedSign'):
                m=re.search(r'^'+op+r'\nmedian: (\d+) cycles/ticks',text,re.M)
                if not m: raise RuntimeError('Missing timing '+op)
                results.append(dict(row,build=v,operation=op,median_cycles=int(m[1]),
                                    kcycles=int(m[1])/1000,iterations=10001))
            if name in PAPER:
                text=call([binaries[name,v],'length'],logfile=out/'lengths.log')
                total,count,lo,hi,attempts=map(int,re.search(r'LENGTH (\d+) (\d+) (\d+) (\d+) (\d+)',text).groups())
                lengths.append({'set':name,'build':v,'count':count,'mean':total/count,
                                'min':lo,'max':hi,'attempts':attempts,'rejected':attempts-count})
        # Save partial numerical evidence after each completed parameter set.
        (out/'timings.json').write_text(json.dumps(results,indent=2)+'\n')
    (out/'lengths.json').write_text(json.dumps(lengths,indent=2)+'\n')
    with (out/'bench.csv').open('w',newline='') as f:
        fields=['parameter_set','n','q','pk','sk','sig','build','operation','iterations','median_cycles','kcycles']
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(results)
    lookup={(r['parameter_set'],r['build'],r['operation']):r['kcycles'] for r in results}
    s='# Antrag cloud benchmark\n\nCloud numbers validate the workflow only; exclude them from paper results.\n\n'
    s+='Code commit: `'+metadata['commit']+'`.\n\n'
    s+='CPU: '+metadata['cpu']+'; pinned logical CPU '+str(cpu)+'.\n\nGCC: '+metadata['gcc']+'.\n\n'
    for v in ('ref','avx2'):
        s+=v+' flags: `'+ ' '.join(metadata['flags'][v])+'`; link: `-lm -lgmp`.\n\n'
    s+='Native hardware double/libm in both builds. Ref disables explicit SIMD and compiler loop/SLP vectorization. AVX2 enables upstream AVX2/FMA.\n\n'
    s+='Each operation executes 10001 times, yielding 10002 RDTSC timestamps and 10001 adjacent intervals. The unchanged Dilithium printer subtracts counter overhead and takes the median. Units: thousand cycles (TSC ticks). Message: 32 bytes.\n\n'
    s+='| Parameter set | q | pk | sig (fixed) | Paper sizes (pk/sig) | ref KeyGen/Sign/Verify | AVX2 KeyGen/Sign/Verify |\n|---|---:|---:|---:|---|---|---|\n'
    for r in SETS:
        name=r['parameter_set']; trip=[]
        for v in ('ref','avx2'):
            trip.append('/'.join('%.3f'%lookup[name,v,op] for op in ('KeyGen','Sign','Verify')))
        s+='| %s (n=%d) | %d | %d | %d | %s | %s | %s |\n'%(name,r['n'],r['q'],r['pk'],r['sig'],PAPER.get(name,'--'),*trip)
    s+='\nExpanded-key Sign includes signature encoding and encoding retries, excluding byte-secret-key decoding.\n\n| Set | ref | AVX2 |\n|---|---:|---:|\n'
    for r in SETS:
        name=r['parameter_set']; s+='| %s | %.3f | %.3f |\n'%(name,lookup[name,'ref','ExpandedSign'],lookup[name,'avx2','ExpandedSign'])
    s+='\nUnpadded lengths include the salt and final partial data byte, excluding whole padding bytes. Each mean uses 10000 successfully encoded, verified signatures. One fixed-seed key per build/set; rejected encodings are counted separately.\n\n| Set | Build | Mean bytes | Min/max | Encoding rejects |\n|---|---|---:|---|---:|\n'
    for r in lengths:s+='| %s | %s | %.4f | %d/%d | %d |\n'%(r['set'],r['build'],r['mean'],r['min'],r['max'],r['rejected'])
    s+='\nCorrectness: existing NTT/poly/RNS unit tests passed for all 20 builds. No upstream KAT exists. Fixed-seed vectors and cross-verification results:\n\n| Set | Equal pk/sk/sig (of 100) | Cross Verify ref←AVX2 / AVX2←ref |\n|---|---|---|\n'
    for r in correctness:
        s+='| %s | %d/%d/%d | 100/100 |\n'%(r['set'],r['equal']['pk'],r['equal']['sk'],r['equal']['sig'])
    s+='\nFMA can change floating-point expanded-key material and signatures. Byte differences are retained in correctness.json; every foreign signature and foreign serialized secret key was verified, and changed messages were rejected.\n\n'
    s+='Paper comparisons are user-supplied Table 2 / Table 3(b) values. 1s and 5s also differ in q. Removing padding changes length only; it does not make their parameters match the paper.\n\n'
    s+='KeyGen includes pk/sk encoding. Sign includes byte-sk decoding, signing, signature encoding and retry after encoding overflow. Verify includes byte-pk and signature decoding. The repository byte-sk already serializes expanded material; decode_sk restores that material. Algorithm source is unchanged; configuration and driver are external. See metadata.json for source hashes and worktree status.\n'
    (out/'SUMMARY.md').write_text(s)
    print('PASS. Summary:',out/'SUMMARY.md',flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        print('FAILED:',e,file=sys.stderr,flush=True)
        sys.exit(1)
