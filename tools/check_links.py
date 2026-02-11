import os
import re
import sys
from urllib.parse import unquote, urljoin, urlparse

ROOT = os.path.dirname(os.path.dirname(__file__))

pattern = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"', re.IGNORECASE)

errors = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    # only check html files
    for fname in [f for f in filenames if f.lower().endswith('.html')]:
        fpath = os.path.join(dirpath, fname)
        rel_dir = os.path.dirname(os.path.relpath(fpath, ROOT))
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        for m in pattern.finditer(data):
            target = m.group(1).strip()
            # ignore external links and anchors
            if target.startswith('#'):
                continue
            parsed = urlparse(target)
            if parsed.scheme in ('http', 'https', 'mailto') or target.startswith('//'):
                continue
            # resolve relative paths
            resolved = os.path.normpath(os.path.join(ROOT, rel_dir, unquote(parsed.path)))
            if not os.path.exists(resolved):
                # try without unquote (maybe file has literal %20 in name)
                alt = os.path.normpath(os.path.join(ROOT, rel_dir, parsed.path))
                suggestion = None
                if os.path.exists(alt):
                    suggestion = alt
                else:
                    # try case-insensitive match in directory
                    dir_to_check = os.path.dirname(resolved)
                    if os.path.isdir(dir_to_check):
                        for cand in os.listdir(dir_to_check):
                            if cand.lower() == os.path.basename(resolved).lower():
                                suggestion = os.path.join(dir_to_check, cand)
                                break
                errors.append((fpath, target, resolved, suggestion))

if not errors:
    print('No missing local targets found.')
    sys.exit(0)

print('Missing local targets:')
for fpath, target, resolved, suggestion in errors:
    print('- In', os.path.relpath(fpath, ROOT))
    print('  ->', target)
    print('  expected at', os.path.relpath(resolved, ROOT))
    if suggestion:
        print('  suggestion:', os.path.relpath(suggestion, ROOT))
    print('')

sys.exit(2)
