# Add new photos

Pipeline: drop raw JPG into `raw/` -> `process.py` -> `bake.py` -> publish.

The originals stay untouched in `raw/`. `process.py` writes the publish-ready 4:5 enhanced copy at the project root as `NNN.jpg`. `bake.py` builds the data block. Re-run is idempotent: only changed photos reprocess.

## Filename rule (raws and processed)

Strict: `NNN.jpg`, three-digit zero-padded, lowercase `.jpg`, range `001`-`100`.

| OK | Not OK |
|---|---|
| `001.jpg` | `1.jpg`, `01.jpg`, `001.JPG`, `001.jpeg`, `001.png` |
| `042.jpg` | `42.jpg`, `042 (1).jpg`, `042-tor.jpg` |
| `100.jpg` | `101.jpg`, `100.jpg.jpg` |

Rename in Explorer or:

```powershell
ren IMG_2048.jpg 042.jpg
```

## GPS in EXIF

Photo should carry GPS. Phone camera with location services on does this automatically. DSLR usually does not — add via Lightroom / ExifTool / phone-pair before drop.

Quick check:

```powershell
python -c "from PIL import Image,ExifTags; t=next(k for k,v in ExifTags.TAGS.items() if v=='GPSInfo'); g=Image.open('raw/042.jpg')._getexif().get(t); print('GPS OK' if g else 'NO GPS')"
```

No GPS → `process.py` still produces a clean processed JPG (it doesn't need GPS). `bake.py` then warns and renders the tile as placeholder. Better: add GPS first, then bake.

## Steps

### 1. Copy raw into raw/

```powershell
copy "D:\camera\IMG_2048.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\042.jpg"
```

Multiple at once:

```powershell
copy "D:\camera\IMG_2048.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\042.jpg"
copy "D:\camera\IMG_2049.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\043.jpg"
copy "D:\camera\IMG_2050.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\044.jpg"
```

### 2. (Optional) Caption

Edit `descriptions.txt`. Append a line:

```
042=Schmiedeeisernes Tor, Alt-Saarbrücken
```

Rules:
- One per line. Format `NNN=text`.
- Skip a line → no caption.
- `#` for comments. Blank lines fine.
- UTF-8. Umlauts and ß OK.

### 3. (Optional) Per-photo processing override

Most photos need nothing. Edit `process.txt` only when defaults don't suit a specific photo:

```
042.crop=top         # keep upper portion of tall door
042.rot=1.5          # manual rotation, overrides auto-detect
007.sat=1.3          # boost saturation 30% above default
015.denoise=off      # skip denoise (e.g. photo already very clean)
022.no_rot=1         # skip auto-straighten (vertical-line detect was wrong)
```

Format: `NNN.field=value`. See `process.txt` itself for the full field list.

### 4. Process

```powershell
cd C:\Work\claude_sandbox\100tuerensaarbruecken
python process.py
```

Expected output:

```
OK   042 rot=auto +0.94deg crop=center -> 1280x1600
INFO processed=1 skipped=29 errored=0
```

What happens per photo: EXIF orientation applied → dominant verticals auto-straightened (clamped to ±5°, skipped if scene's near-vertical lines disagree, i.e. low confidence) → centered 4:5 crop → NL-means denoise → unsharp mask → +15% saturation → resized so long edge ≤ 1600 px → saved to `042.jpg` at root with GPS preserved.

Slow: ~3-5 s per photo (denoise is the bottleneck). On re-run, untouched photos are skipped (mtime cache).

Troubleshoot:
- `WARN NNN bad rot value ...` → fix the value in `process.txt`.
- Door appears over-rotated → add `NNN.no_rot=1` in `process.txt` and re-run.
- Want to redo everything: `python process.py --force`.
- Want to redo just one: `python process.py --only 42 --force`.

### 5. Bake

```powershell
python bake.py --inject gallery.html
```

Expected:

```
INFO 30/100 photos present, 30 with GPS
OK   injected into gallery.html
```

Warnings (not errors):
- `WARN NNN.jpg no GPS - shown without map pin` — photo has no GPS EXIF. Tile renders but the `↗` map link is omitted. See `mi12.md` for retroactive injection via ExifTool.
- `WARN NNN.jpg missing - description discarded` — caption set in `descriptions.txt` for slot with no JPG yet.
- `WARN bottom.html missing - footer left empty` — optional footer fragment not present; page still works, footer is hidden via CSS `:empty`.

### 6. Preview locally

Double-click `gallery.html`. Hover the new tile: caption (if any) fades in over the image, `↗` link bottom-right opens OpenStreetMap at the right location. Click image → fade-in lightbox with full caption below; prev/next buttons or arrow keys step through other slots, wrapping at the ends. Empty slots stay silent until hovered, then reveal "noch nicht".

### 7. Publish

GitHub Pages (see `deploy.md`):

```powershell
git add raw/042.jpg 042.jpg gallery.html descriptions.txt process.txt
git commit -m "add photo 042"
git push
```

Live in ~30-60 s.

Netlify drag-drop: re-drag the whole folder.

FTP: upload changed `gallery.html` and the new processed `042.jpg`. The `raw/` directory does not need to ship to the host.

## Replace an existing photo

Same slot, new raw:

```powershell
copy "D:\better\042-redo.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\042.jpg"  # overwrite raw
python process.py                       # detects newer raw, reprocesses 042
python bake.py --inject gallery.html
git add raw/042.jpg 042.jpg gallery.html
git commit -m "redo photo 042"
git push
```

Browser caches by filename. Visitors see new image on next cache miss (instant on hard-refresh, default cache up to ~1 day).

## Tweak processing of an existing photo

```powershell
notepad process.txt                     # edit overrides for slot 042
python process.py                       # re-runs only photos affected
python bake.py --inject gallery.html
git add 042.jpg gallery.html process.txt
git commit -m "retune 042"
git push
```

Editing `process.txt` makes its mtime newer than the processed JPGs, so all relevant slots reprocess on next run. To redo only one slot regardless: `python process.py --only 42 --force`.

## Remove a photo

```powershell
del raw\042.jpg
del 042.jpg
python bake.py --inject gallery.html
git rm raw/042.jpg 042.jpg
git add gallery.html descriptions.txt
git commit -m "remove photo 042"
git push
```

Tile reverts to placeholder.

## Bulk add

Drop all raws at once, one process, one bake, one commit:

```powershell
copy "D:\batch\*.jpg" "C:\Work\claude_sandbox\100tuerensaarbruecken\raw\"
python process.py
python bake.py --inject gallery.html
git add raw\*.jpg *.jpg gallery.html descriptions.txt
git commit -m "add photos batch"
git push
```

`process.py` and `bake.py` are both idempotent. Safe to re-run any time.

## File size

Processed JPGs at 1600 px / quality 88 typically 150-400 KB each. 100 of them ≈ 15-40 MB total. Far under any host quota. Raw originals can be larger but live alongside in `raw/`; ship or skip them as you prefer (they don't need to be hosted, only committed if you want offsite backup).

If a raw is huge (DSLR uncompressed >100 MB) GitHub will reject it on push. Resize the raw before storing it:

```powershell
python -c "from PIL import Image; im=Image.open('raw/042.jpg'); im.thumbnail((4000,4000)); im.save('raw/042.jpg','jpeg',quality=92,exif=im.info.get('exif',b''))"
```

`exif=...` preserves GPS. Then `python process.py --only 42 --force`.
