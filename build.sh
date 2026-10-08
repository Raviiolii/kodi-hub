#!/usr/bin/env bash
# VillaHub repo builder: empaqueta los addons y regenera el indice.
# Uso: ./build.sh   (luego: git add -A && git commit -m "vX" && git push)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p repo

for src in src/*/; do
  id="$(basename "$src")"
  ver="$(python3 - "$src/addon.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
print(ET.parse(sys.argv[1]).getroot().get('version'))
PY
)"
  mkdir -p "repo/$id"
  rm -f "repo/$id/$id-"*.zip
  (cd src && zip -qr "../repo/$id/$id-$ver.zip" "$id" -x "*/__pycache__/*" "*.pyc" "*.pyo")
  echo "built $id v$ver"
done

python3 - <<'PY'
import glob, hashlib
out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<addons>']
for f in sorted(glob.glob('src/*/addon.xml')):
    body = open(f, encoding='utf-8').read()
    body = body.split('?>', 1)[1].strip()
    out.append(body)
out.append('</addons>')
data = '\n'.join(out) + '\n'
open('repo/addons.xml', 'w', encoding='utf-8').write(data)
open('repo/addons.xml.md5', 'w').write(hashlib.md5(data.encode('utf-8')).hexdigest())
print('repo/addons.xml + .md5 regenerados')
PY
