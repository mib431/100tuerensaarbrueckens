# Deploy via GitHub Pages (free personal account)

Static-only site. No build, no Actions needed. Repo + Pages toggle = live URL.

## One-time setup

### 1. Create repo

Pick one of two URL patterns:

| Repo name | Live URL | Notes |
|---|---|---|
| `<username>.github.io` | `https://<username>.github.io/` | "User site". Root path. One per account. |
| Any other name, e.g. `tueren` | `https://<username>.github.io/tueren/` | "Project site". Subpath. Unlimited. |

Project site recommended unless you want this as your main personal page.

On github.com → **New repository** → name it → **Public** (private repos need GH Pro for Pages) → no README, no .gitignore, no license → **Create**.

### 2. Install Python deps (one-time)

`process.py` needs Pillow + OpenCV. `bake.py` needs only Pillow.

```powershell
cd C:\Work\claude_sandbox\100tuerensaarbruecken
pip install -r requirements.txt
```

### 3. Push files

In `C:\Work\claude_sandbox\100tuerensaarbruecken`:

```powershell
git init
git add gallery.html bake.py process.py descriptions.txt process.txt requirements.txt raw\.gitkeep
git commit -m "initial: gallery + processing pipeline"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

(Create the empty `raw\.gitkeep` file first to track the empty directory: `New-Item raw\.gitkeep -ItemType File`.)

First push prompts for auth. Use a **Personal Access Token** (classic, scope `repo`) as password, not your account password. Generate at github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token. Save it in your password manager.

Alternative: install **GitHub CLI** (`winget install GitHub.cli`), then `gh auth login` once and skip token juggling.

### 4. Add photos

Drop raws into `raw/`, run process, run bake, commit. See `add_new.md` for the full procedure. Short version:

```powershell
copy <wherever>\001.jpg raw\
copy <wherever>\005.jpg raw\
python process.py
python bake.py --inject gallery.html
git add raw\001.jpg raw\005.jpg 001.jpg 005.jpg gallery.html
git commit -m "add photos 001, 005"
git push
```

Repeat each time you have new photos.

### 5. Enable Pages

GitHub repo page → **Settings** → **Pages** (left sidebar) → **Build and deployment**:
- Source: **Deploy from a branch**
- Branch: **main**, folder **/ (root)** → **Save**

Wait ~1 minute. URL appears at top of Pages settings: `https://<username>.github.io/<repo>/`. Refresh to confirm green checkmark.

### 6. Verify

Open `https://<username>.github.io/<repo>/gallery.html` in browser. Expect:
- Tiles render in a 4:5-portrait grid. Present photos show enhanced (straightened, denoised, sharpened, slightly more saturated). Missing show "noch nicht da".
- Click image → lightbox shows the full 4:5 processed photo.
- Click 📍 → Google Maps at correct GPS.

If 404: Pages may still be building. Wait, hard-refresh.

## Daily updates

```powershell
copy <new>\042.jpg raw\
python process.py
python bake.py --inject gallery.html
git add raw\042.jpg 042.jpg gallery.html
git commit -m "add photo 042"
git push
```

GH Pages rebuilds automatically on push. New photo live in ~30-60 s.

## Quotas (free account, public repo)

- Repo soft cap 1 GB. Processed JPGs at 1600 px / quality 88 are typically 150-400 KB each → 100 of them ≈ 15-40 MB. Raws may be larger but still well under quota.
- Pages bandwidth 100 GB/month. Photos cached by browser, won't blow it.
- Pages build limit 10/hour. Far below normal use.

## Excluding raws from the deployed site

Raws don't need to be served — only the processed root JPGs are referenced by `gallery.html`. Two options:

1. **Commit raws but don't worry** — GH Pages serves the whole repo. Raws are technically reachable at `/<repo>/raw/042.jpg` but nobody links to them. Cheapest path.
2. **Keep raws out of the deployed branch** — create a separate `raws` branch that holds them for backup, and have `main` (deployed) carry only processed JPGs + scripts. More setup, marginal benefit.

For 100 doors, option 1 is fine.

## Custom domain (optional)

Settings → Pages → Custom domain → enter `tueren.example.com` → Save. Then add a DNS CNAME from `tueren.example.com` to `<username>.github.io`. Wait for HTTPS cert (automatic, ~10 min). Free.

## Make repo public-readable but commits private

Not possible on free tier — public repos are fully public, including history. If photos must be hidden until publish, keep them out of git, host them separately on an asset host (R2 / Bunny), and change the `src="${n}.jpg"` prefix in `gallery.html` JS to point at that bucket.
