"""
bake.py — extract EXIF GPS from 001.jpg..100.jpg and merge optional descriptions.txt
into a JS data block for gallery.html.

Usage:
    python bake.py                       # print data block to stdout
    python bake.py --inject gallery.html # inject between /*BEGIN*/.../*END*/ markers
    python bake.py --dir path/to/photos  # use a different photo directory

Requires: Pillow  (pip install Pillow)
"""
import sys
import json
import re
from pathlib import Path

try:
    from PIL import Image, ExifTags
except ImportError:
    sys.stderr.write("ERROR: Pillow not installed. Run: pip install Pillow\n")
    sys.exit(2)

GPS_TAG = next(k for k, v in ExifTags.TAGS.items() if v == 'GPSInfo')


def dms_to_decimal(triple, ref):
    d = float(triple[0]) + float(triple[1]) / 60 + float(triple[2]) / 3600
    return -d if ref in ('S', 'W') else d


def read_gps(path):
    try:
        img = Image.open(path)
    except Exception as e:
        print(f'ERR  {path.name}: cannot open ({e})', file=sys.stderr)
        return None
    exif = img._getexif() or {}
    gps = exif.get(GPS_TAG)
    if not gps or 1 not in gps or 2 not in gps or 3 not in gps or 4 not in gps:
        return None
    try:
        lat = round(dms_to_decimal(gps[2], gps[1]), 6)
        lon = round(dms_to_decimal(gps[4], gps[3]), 6)
    except Exception as e:
        print(f'ERR  {path.name}: bad GPS data ({e})', file=sys.stderr)
        return None
    return {'lat': lat, 'lon': lon}


def load_descriptions(root):
    f = root / 'descriptions.txt'
    if not f.exists():
        return {}
    out = {}
    for ln, raw in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            print(f'WARN descriptions.txt:{ln} no `=`', file=sys.stderr)
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        if not re.fullmatch(r'\d{1,3}', key):
            print(f'WARN descriptions.txt:{ln} bad key {key!r}', file=sys.stderr)
            continue
        n = int(key)
        if not 1 <= n <= 100:
            print(f'WARN descriptions.txt:{ln} key {n} out of 1..100', file=sys.stderr)
            continue
        if n in out:
            print(f'WARN descriptions.txt:{ln} duplicate key {n:03d}', file=sys.stderr)
        out[n] = val.strip()
    return out


def build(root):
    descs = load_descriptions(root)
    used_descs = set()
    data = []
    present = 0
    for i in range(1, 101):
        p = root / f'{i:03d}.jpg'
        if not p.exists():
            if i in descs:
                print(f'WARN {p.name} missing - description discarded', file=sys.stderr)
            data.append(None)
            continue
        present += 1
        gps = read_gps(p)
        entry = gps if gps is not None else {}
        if gps is None:
            print(f'WARN {p.name} no GPS - shown without map pin', file=sys.stderr)
        if i in descs:
            entry['desc'] = descs[i]
            used_descs.add(i)
        data.append(entry)
    for k in sorted(descs.keys() - used_descs):
        if not (root / f'{k:03d}.jpg').exists():
            continue
        # description was assigned (entry exists for present file). only warn if file missing -- handled above.
    with_gps = sum(1 for d in data if d and 'lat' in d)
    print(f'INFO {present}/100 photos present, {with_gps} with GPS', file=sys.stderr)
    return data


def render_block(data):
    return 'const DATA=' + json.dumps(data, separators=(',', ':'), ensure_ascii=False) + ';'


def load_bottom(root):
    """Return contents of bottom.html or empty string with warning if absent."""
    f = root / 'bottom.html'
    if not f.exists():
        print('WARN bottom.html missing - footer left empty', file=sys.stderr)
        return ''
    return f.read_text(encoding='utf-8').strip()


def inject(target, replacements):
    """replacements: list of (begin_marker, end_marker, content) tuples."""
    p = Path(target)
    if not p.exists():
        print(f'ERR  target {target} does not exist', file=sys.stderr)
        sys.exit(1)
    src = p.read_text(encoding='utf-8')
    for begin, end, content in replacements:
        pattern = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.S)
        if not pattern.search(src):
            print(f'ERR  markers {begin} .. {end} not found in {target}', file=sys.stderr)
            sys.exit(1)
        src = pattern.sub(lambda _m: begin + content + end, src)
    p.write_text(src, encoding='utf-8')
    print(f'OK   injected into {target}', file=sys.stderr)


def parse_args(argv):
    args = {'dir': '.', 'inject': None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        elif a == '--inject':
            i += 1
            if i >= len(argv):
                print('ERR  --inject needs a path', file=sys.stderr); sys.exit(2)
            args['inject'] = argv[i]
        elif a == '--dir':
            i += 1
            if i >= len(argv):
                print('ERR  --dir needs a path', file=sys.stderr); sys.exit(2)
            args['dir'] = argv[i]
        else:
            print(f'ERR  unknown arg: {a}', file=sys.stderr); sys.exit(2)
        i += 1
    return args


def main():
    args = parse_args(sys.argv[1:])
    root = Path(args['dir'])
    if not root.is_dir():
        print(f'ERR  not a directory: {root}', file=sys.stderr); sys.exit(1)
    data = build(root)
    block = render_block(data)
    bottom = load_bottom(root)
    if args['inject']:
        inject(args['inject'], [
            ('/*BEGIN*/', '/*END*/', block),
            ('<!--BEGIN_BOTTOM-->', '<!--END_BOTTOM-->', bottom),
        ])
    else:
        print(block)


if __name__ == '__main__':
    main()
