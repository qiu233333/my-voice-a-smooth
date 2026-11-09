from pathlib import Path
import json
import sys
from voice_core import ROOT, sha256

manifest=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
failures=[]
for entry in manifest['files']:
    path=ROOT/entry['path']
    if not path.is_file() or path.stat().st_size!=entry['bytes'] or sha256(path)!=entry['sha256']:
        failures.append(entry['path'])
print(json.dumps({'ok':not failures,'checked_files':len(manifest['files']),'failures':failures},ensure_ascii=False))
sys.exit(1 if failures else 0)
