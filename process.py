"""
process.py — pre-build pipeline for the 100-doors gallery.

Reads raw/NNN.jpg, applies EXIF orientation, auto-straightens dominant verticals,
crops to a fixed aspect ratio (4:5 by default) centered, denoises (NL-means),
sharpens, bumps saturation, downsizes to LONG_EDGE px, and writes NNN.jpg
at project root with GPS EXIF preserved and orientation tag cleared.

Usage:
    python process.py                 # process new/changed raws (default)
    python process.py --force         # reprocess everything
    python process.py --only 042 7    # only specified slot numbers
    python process.py --dry-run       # log actions, write nothing
    python process.py --raw raw       # raw input dir (default: raw)
    python process.py --out .         # output dir (default: project root, i.e. .)

Requires:
    pip install Pillow opencv-python numpy
"""
from __future__ import annotations

import sys
import re
from pathlib import Path

try:
    import numpy as np
    import cv2
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
except ImportError as e:
    sys.stderr.write(f"ERROR: missing dependency ({e}). Run: pip install -r requirements.txt\n")
    sys.exit(2)

# ---- global config -----------------------------------------------------------
TILE_RATIO = (4, 5)  # width, height
LONG_EDGE = 1600
JPEG_QUALITY = 88
SHARPEN = dict(radius=2, percent=120, threshold=3)
SATURATION = 1.15
DENOISE = dict(h=5, hColor=5, templateWindowSize=7, searchWindowSize=21)
SKEW_CLAMP_DEG = 5.0
SKEW_MIN_LINES = 8
SKEW_MAX_DEV_FROM_VERTICAL = 7.0   # degrees: only consider lines within this band
SKEW_MAX_IQR_DEG = 1.5             # skip if line angles disagree more than this (low confidence)
SKEW_DEADBAND_DEG = 0.4            # skip rotation if |correction| below this (avoid interpolation cost for marginal tilt)
ORIENTATION_TAG = 0x0112


# ---- sidecar parsing ---------------------------------------------------------
_TRUE = {'1', 'true', 'yes', 'on'}
_FALSE = {'0', 'false', 'no', 'off'}


def parse_overrides(path: Path) -> dict[int, dict]:
    """Read process.txt → {slot_number: {field: value}}."""
    if not path.exists():
        return {}
    out: dict[int, dict] = {}
    text = path.read_text(encoding='utf-8')
    for ln, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            print(f'WARN process.txt:{ln} no `=`', file=sys.stderr)
            continue
        key, _, val = line.partition('=')
        key = key.strip()
        val = val.strip()
        m = re.fullmatch(r'(\d{1,3})\.([a-z_]+)', key)
        if not m:
            print(f'WARN process.txt:{ln} bad key {key!r} (expect NNN.field)', file=sys.stderr)
            continue
        n = int(m.group(1))
        field = m.group(2)
        if not 1 <= n <= 100:
            print(f'WARN process.txt:{ln} slot {n} out of 1..100', file=sys.stderr)
            continue
        out.setdefault(n, {})[field] = val
    return out


def get_field(over: dict, name: str, default):
    return over.get(name, default)


# ---- pipeline steps ----------------------------------------------------------
def detect_vertical_skew(pil_img: Image.Image) -> float:
    """Return degrees of CCW correction needed (clamped to ±SKEW_CLAMP_DEG)."""
    gray = np.array(pil_img.convert('L'))
    h, w = gray.shape
    edges = cv2.Canny(gray, 80, 200)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 360,
        threshold=80,
        minLineLength=h // 4,
        maxLineGap=20,
    )
    if lines is None:
        return 0.0
    angles = []
    for x1, y1, x2, y2 in lines[:, 0]:
        dy = y2 - y1
        if dy == 0:
            continue  # horizontal line — ignore
        # angle from vertical: 0 = perfectly vertical, +/-90 = horizontal.
        a = np.degrees(np.arctan2(x2 - x1, dy))
        if abs(a) <= SKEW_MAX_DEV_FROM_VERTICAL:
            angles.append(a)
    if len(angles) < SKEW_MIN_LINES:
        return 0.0
    arr = np.asarray(angles)
    # Confidence gate: dominant verticals must agree. If lines disagree (high IQR),
    # the scene likely has perspective / non-parallel features and median is misleading.
    iqr = float(np.percentile(arr, 75) - np.percentile(arr, 25))
    if iqr > SKEW_MAX_IQR_DEG:
        return 0.0
    # Sign convention: +atan2(dx,dy) is the line's lean (↘ when positive).
    # PIL rotate(+a) is CCW which would *worsen* a ↘ lean, so correction is the negation.
    correction = -float(np.median(arr))
    if abs(correction) < SKEW_DEADBAND_DEG:
        return 0.0
    return max(-SKEW_CLAMP_DEG, min(SKEW_CLAMP_DEG, correction))


def rotate_image(pil_img: Image.Image, angle_deg: float) -> Image.Image:
    """Rotate counter-clockwise by angle_deg (positive). expand=False keeps dims;
    corners get filled black and are normally cropped away by the 4:5 crop step."""
    if abs(angle_deg) < 0.05:
        return pil_img
    return pil_img.rotate(angle_deg, resample=Image.BICUBIC, expand=False, fillcolor=(0, 0, 0))


def parse_crop_anchor(value: str) -> float | None:
    """Return a fraction in [0, 1]. None on parse error."""
    v = value.strip().lower()
    if v == 'top' or v == 'left':
        return 0.0
    if v == 'center' or v == 'middle':
        return 0.5
    if v == 'bottom' or v == 'right':
        return 1.0
    m = re.fullmatch(r'(\d+(?:\.\d+)?)%?', v)
    if not m:
        return None
    f = float(m.group(1)) / 100.0
    return max(0.0, min(1.0, f))


def crop_to_ratio(pil_img: Image.Image, target_w: int, target_h: int, anchor: float) -> Image.Image:
    """Center-crop to target aspect (target_w:target_h). `anchor` (0..1) shifts the
    crop window: for portrait sources it's vertical (0=top, 1=bottom); for
    landscape it's horizontal (0=left, 1=right)."""
    src_w, src_h = pil_img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    if abs(src_ratio - target_ratio) < 1e-3:
        return pil_img
    if src_ratio > target_ratio:
        # source wider than target → crop horizontally
        new_w = int(round(src_h * target_ratio))
        max_off = src_w - new_w
        x0 = int(round(max_off * anchor))
        return pil_img.crop((x0, 0, x0 + new_w, src_h))
    else:
        # source taller than target → crop vertically
        new_h = int(round(src_w / target_ratio))
        max_off = src_h - new_h
        y0 = int(round(max_off * anchor))
        return pil_img.crop((0, y0, src_w, y0 + new_h))


def denoise_image(pil_img: Image.Image) -> Image.Image:
    rgb = np.array(pil_img.convert('RGB'))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    out = cv2.fastNlMeansDenoisingColored(bgr, None, **DENOISE)
    out_rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
    return Image.fromarray(out_rgb)


def sharpen_image(pil_img: Image.Image, multiplier: float = 1.0) -> Image.Image:
    if multiplier <= 0:
        return pil_img
    return pil_img.filter(ImageFilter.UnsharpMask(
        radius=SHARPEN['radius'],
        percent=int(round(SHARPEN['percent'] * multiplier)),
        threshold=SHARPEN['threshold'],
    ))


def saturate_image(pil_img: Image.Image, multiplier: float = 1.0) -> Image.Image:
    factor = 1.0 + (SATURATION - 1.0) * multiplier
    if abs(factor - 1.0) < 1e-3:
        return pil_img
    return ImageEnhance.Color(pil_img).enhance(factor)


def downsize(pil_img: Image.Image, long_edge: int) -> Image.Image:
    w, h = pil_img.size
    longest = max(w, h)
    if longest <= long_edge:
        return pil_img
    scale = long_edge / longest
    return pil_img.resize((int(round(w * scale)), int(round(h * scale))), Image.LANCZOS)


# ---- per-photo driver --------------------------------------------------------
def process_one(slot: int, raw_path: Path, out_path: Path, over: dict, dry_run: bool):
    img = Image.open(raw_path)
    raw_exif_bytes = img.info.get('exif')
    img = ImageOps.exif_transpose(img)

    # Rotation
    no_rot_raw = over.get('no_rot')
    no_rot = no_rot_raw is not None and no_rot_raw.lower() in _TRUE
    rot_override = None
    if 'rot' in over:
        try:
            rot_override = float(over['rot'])
        except ValueError:
            print(f'WARN {slot:03d} bad rot value {over["rot"]!r}; ignoring', file=sys.stderr)
    if rot_override is not None:
        angle = rot_override
        rot_source = f'manual {angle:+.2f}deg'
    elif no_rot:
        angle = 0.0
        rot_source = 'disabled'
    else:
        angle = detect_vertical_skew(img)
        rot_source = f'auto {angle:+.2f}deg'
    img = rotate_image(img, angle)

    # Crop
    anchor_raw = over.get('crop', 'center')
    anchor = parse_crop_anchor(anchor_raw)
    if anchor is None:
        print(f'WARN {slot:03d} bad crop value {anchor_raw!r}; using center', file=sys.stderr)
        anchor = 0.5
    img = crop_to_ratio(img, TILE_RATIO[0], TILE_RATIO[1], anchor)

    # Denoise
    denoise_v = over.get('denoise', 'on').lower()
    do_denoise = denoise_v in _TRUE
    if denoise_v not in _TRUE and denoise_v not in _FALSE:
        print(f'WARN {slot:03d} bad denoise value {denoise_v!r}; using on', file=sys.stderr)
        do_denoise = True
    if do_denoise:
        img = denoise_image(img)

    # Sharpen
    try:
        sharp_mult = float(over.get('sharp', 1.0))
    except ValueError:
        print(f'WARN {slot:03d} bad sharp value; using 1.0', file=sys.stderr)
        sharp_mult = 1.0
    img = sharpen_image(img, sharp_mult)

    # Saturate
    try:
        sat_mult = float(over.get('sat', 1.0))
    except ValueError:
        print(f'WARN {slot:03d} bad sat value; using 1.0', file=sys.stderr)
        sat_mult = 1.0
    img = saturate_image(img, sat_mult)

    # Resize
    img = downsize(img, LONG_EDGE)

    w, h = img.size
    print(f'OK   {slot:03d} rot={rot_source} crop={anchor_raw} -> {w}x{h}', file=sys.stderr)

    if dry_run:
        return

    # Save with EXIF (orientation cleared, GPS preserved)
    save_kwargs = dict(format='JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
    exif = img.getexif()
    if not exif and raw_exif_bytes:
        # exif_transpose may have wiped getexif() on some Pillow versions; fallback
        exif = Image.Exif()
        try:
            exif.load(raw_exif_bytes)
        except Exception:
            pass
    if exif:
        exif[ORIENTATION_TAG] = 1
        save_kwargs['exif'] = exif.tobytes()
    img.save(out_path, **save_kwargs)


# ---- mtime cache logic -------------------------------------------------------
def needs_rebuild(raw_path: Path, out_path: Path, sidecar_mtime: float) -> bool:
    if not out_path.exists():
        return True
    out_m = out_path.stat().st_mtime
    raw_m = raw_path.stat().st_mtime
    return raw_m > out_m or sidecar_mtime > out_m


# ---- CLI ---------------------------------------------------------------------
def parse_args(argv: list[str]) -> dict:
    args = {
        'raw_dir': 'raw',
        'out_dir': '.',
        'force': False,
        'dry_run': False,
        'only': None,  # set[int] or None
    }
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        elif a == '--force':
            args['force'] = True
        elif a == '--dry-run':
            args['dry_run'] = True
        elif a == '--raw':
            i += 1
            if i >= len(argv): die('--raw needs a path')
            args['raw_dir'] = argv[i]
        elif a == '--out':
            i += 1
            if i >= len(argv): die('--out needs a path')
            args['out_dir'] = argv[i]
        elif a == '--only':
            args['only'] = set()
            while i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                i += 1
                tok = argv[i]
                if not tok.isdigit():
                    die(f'--only expects integers, got {tok!r}')
                n = int(tok)
                if not 1 <= n <= 100:
                    die(f'--only slot {n} out of 1..100')
                args['only'].add(n)
            if not args['only']:
                die('--only needs at least one slot number')
        else:
            die(f'unknown arg: {a}')
        i += 1
    return args


def die(msg: str):
    print(f'ERR  {msg}', file=sys.stderr)
    sys.exit(2)


def main():
    args = parse_args(sys.argv[1:])
    raw_dir = Path(args['raw_dir'])
    out_dir = Path(args['out_dir'])
    if not raw_dir.is_dir():
        die(f'raw dir not found: {raw_dir}')
    if not out_dir.is_dir():
        die(f'out dir not found: {out_dir}')

    overrides_path = out_dir / 'process.txt'
    overrides = parse_overrides(overrides_path)
    sidecar_mtime = overrides_path.stat().st_mtime if overrides_path.exists() else 0.0

    only = args['only']
    processed = skipped = errored = 0
    for slot in range(1, 101):
        if only and slot not in only:
            continue
        raw_path = raw_dir / f'{slot:03d}.jpg'
        out_path = out_dir / f'{slot:03d}.jpg'
        if not raw_path.exists():
            continue
        over = overrides.get(slot, {})
        if not args['force'] and not needs_rebuild(raw_path, out_path, sidecar_mtime):
            skipped += 1
            continue
        try:
            process_one(slot, raw_path, out_path, over, args['dry_run'])
            processed += 1
        except Exception as e:
            errored += 1
            print(f'ERR  {slot:03d}: {e}', file=sys.stderr)

    summary = f'INFO processed={processed} skipped={skipped} errored={errored}'
    if args['dry_run']:
        summary += ' (dry-run, no files written)'
    print(summary, file=sys.stderr)
    sys.exit(1 if errored else 0)


if __name__ == '__main__':
    main()
