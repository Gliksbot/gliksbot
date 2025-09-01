#!/usr/bin/env python3
import argparse, zipfile, os, json, sys, subprocess, time, shutil
from pathlib import Path

def log(event, **kw):
    print(json.dumps({"ts": time.time(), "event": event, **kw}), flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--package', default='/run/pkg.zip')
    args = ap.parse_args()
    work = Path('/run/work')
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.package) as z:
        z.extractall(work)
    manifest = json.loads((work/'manifest.json').read_text())
    log('runner.unpack', files=[p.name for p in work.iterdir()])
    tests_dir = work/'tests'
    if tests_dir.exists():
        log('runner.tests.start')
        proc = subprocess.Popen(['pytest','-q',str(tests_dir)], cwd=str(work), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            log('runner.tests.stdout', text=line.rstrip())
        rc = proc.wait()
        log('runner.tests.exit', code=rc)
        if rc != 0:
            sys.exit(rc)
    entry = manifest.get('entry','skill.py')
    lang = manifest.get('language','python')
    stdin_payload = manifest.get('args', {})
    if lang == 'python':
        target = entry.split(':')[0]
        cmd = ['python', target]
    else:
        cmd = entry.split()
    log('runner.exec.start', cmd=cmd)
    proc = subprocess.Popen(cmd, cwd=str(work), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        proc.stdin.write(json.dumps(stdin_payload))
        proc.stdin.close()
    except Exception:
        pass
    for line in proc.stdout:
        log('runner.exec.stdout', text=line.rstrip())
    rc = proc.wait()
    log('runner.exec.exit', code=rc)
    sys.exit(rc)

if __name__ == '__main__':
    main()

