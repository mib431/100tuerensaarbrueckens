# DNS — register and maintain a domain (GitHub Pages hosting)

Target setup: domain `100tuerensaarbrueckens.de` pointed at GitHub Pages, with HTTPS enforced. Same procedure works for any name; only the registrar UI varies.

## 1. Register `100tuerensaarbrueckens.de`

**.de policy:** registry is **DENIC**. .de domains require a German postal contact (admin-c). Most registrars handle this transparently if you live in Germany — they use your address.

### Cheapest registrars for .de

| Registrar | .de price/year | Notes |
|---|---|---|
| **Hetzner** | ~3.90 EUR | Cheapest, German company, no upsell |
| INWX | ~5.00 EUR | DNS console nice, German |
| Strato | ~6.00 EUR | First-year discount, then ~12 EUR |
| IONOS | ~6.00 EUR (promo) → ~15 | Heavy upsell |
| Namecheap (intl.) | ~10 USD | Works, but pricier than DE registrars |
| Porkbun | ~10 EUR | Decent intl. option |

**Recommended: Hetzner** for cost + simplicity. Account → Domains → search `100tuerensaarbrueckens.de` → buy → pay (SEPA, card, PayPal).

### Wire DNS to GitHub Pages

GitHub Pages serves the apex domain via 4 A records + 4 AAAA; subdomain `www` via CNAME.

In Hetzner DNS console (or whatever registrar):

| Type | Name | Value | TTL |
|---|---|---|---|
| A | @ | `185.199.108.153` | 3600 |
| A | @ | `185.199.109.153` | 3600 |
| A | @ | `185.199.110.153` | 3600 |
| A | @ | `185.199.111.153` | 3600 |
| AAAA | @ | `2606:50c0:8000::153` | 3600 |
| AAAA | @ | `2606:50c0:8001::153` | 3600 |
| AAAA | @ | `2606:50c0:8002::153` | 3600 |
| AAAA | @ | `2606:50c0:8003::153` | 3600 |
| CNAME | www | `<user>.github.io.` | 3600 |

(IPs current as of 2026; if GH changes them, check https://docs.github.com/en/pages → "Configuring an apex domain".)

### Tell GitHub the domain

In repo: **Settings → Pages → Custom domain** → enter `100tuerensaarbrueckens.de` → Save. GitHub creates a `CNAME` file in repo root (one line: the domain). Commit it if not auto-committed.

Wait 5–30 min for DNS propagation. Then GitHub auto-provisions a Let's Encrypt cert (~10 min). When ready: tick **"Enforce HTTPS"** in Pages settings.

### Verify

```powershell
nslookup 100tuerensaarbrueckens.de
nslookup www.100tuerensaarbrueckens.de
curl.exe -I https://100tuerensaarbrueckens.de/
```

Expected: A records show GH IPs; HTTPS returns `200 OK`.

## 2. "Support" the domain (ongoing)

| Task | Cadence |
|---|---|
| **Renewal** | Annual. Auto-renew at registrar + ensure card is valid. Calendar reminder 14 days before expiry as backup. .de has only ~30-day grace after expiry; lose it = anyone can grab. |
| **HTTPS cert** | Automatic. Let's Encrypt renews silently via GitHub. Keep "Enforce HTTPS" ticked. |
| **DNS records** | Static once set. Revisit only if GH changes its Pages IPs (rare; check yearly). |
| **WHOIS / contact data** | DENIC requires accurate admin-c. Update at registrar if you move. .de WHOIS is non-public for individuals (privacy automatic). |
| **Email forwarding (optional)** | For `kontakt@100tuerensaarbrueckens.de`, most DE registrars include free forwarding. Add the MX record set the registrar provides. |
| **Monitor uptime (optional)** | UptimeRobot free tier pings every 5 min, emails on outage. Rarely needed for static GH Pages but cert misconfig can break things silently. |

**Backup of domain ownership:** registrar credentials in a password manager + registrar name written down offline. Losing registrar access = losing the domain.

## 3. Alternative names

**Theme axes:**
- count (100, hundert)
- subject (Tür, Türen, Schwelle, Pforte, Tor, Portal, door, doors)
- place (Saarbrücken, Saar, Saarland)
- zen overlay (Schwelle = threshold, Pforte = gate, nirvana, mu, leere)

**Cost note:** generic .de cheapest. Niche TLDs like `.saarland`, `.gallery`, `.photo` cost 5-10× more but read as theme. Pure marketing TLDs (.art, .city) sit in between.

| Name | Zone | Theme | ~Cost/year | Notes |
|---|---|---|---|---|
| **100tuerensaarbrueckens.de** | .de | literal title | ~4 EUR | Long, exact match, SEO-friendly. Current pick. |
| **100tueren.de** | .de | minimalist | ~4 EUR | Short, but ambiguous (which city?). Check availability — likely taken. |
| **hundert-tueren.de** | .de | literal spelled-out | ~4 EUR | Hyphenated, readable, matches "Einhundert" title style. |
| **saartueren.de** | .de | place+subject | ~4 EUR | Compact, regional. |
| **tueren-sb.de** | .de | abbreviation | ~4 EUR | "SB" = local nickname for Saarbrücken. Insider-friendly. |
| **saarbruecker-tueren.de** | .de | adjective+subject | ~4 EUR | Natural German phrasing. |
| **schwellen.de** / **100schwellen.de** | .de | zen (threshold) | ~4 EUR | "Schwelle" = threshold/doorstep. Strong zen pull. Single word likely taken. |
| **pforten.saarland** | .saarland | zen+regional | ~30-40 EUR | Ornate. "Pforte" = portal/gate, archaic-poetic. Regional TLD. |
| **tueren.saarland** | .saarland | place-defining | ~30-40 EUR | Strongest geographic signal. Pricier. |
| **100doors.saarland** | .saarland | English+regional | ~30-40 EUR | Reaches non-German visitors. |
| **tuerensaar.eu** | .eu | regional | ~5-7 EUR | .eu = next cheapest after .de. |
| **doorsofsaarbruecken.com** | .com | English | ~10-12 EUR | International audience. |
| **doors.gallery** | .gallery | medium-themed | ~25-35 EUR | Reads as art project. Generic name → likely taken. |
| **saardoors.art** | .art | art-themed | ~15-20 EUR | Cheaper than .gallery, similar tone. |
| **schwelle.photo** | .photo | medium | ~30-40 EUR | Niche-specific. |

### Recommended pairs

- **Budget + literal:** keep `100tuerensaarbrueckens.de` as primary. Optionally also register `100tueren.de` (~4 EUR more) for typing convenience — redirect to canonical.
- **Budget + zen:** `100schwellen.de` (~4 EUR). Pulls hard on threshold/passage idea, fits the design direction.
- **Splurge + regional + zen:** `pforten.saarland` (~35 EUR). Most poetic, geographically rooted, reads like a curated project not a hobby site.
- **Multi-domain strategy:** own 2-3, redirect all to one canonical. ~10-15 EUR/year total for two .de's plus one .saarland.

## 4. Redirecting an alias domain to canonical

If you register multiple names, pick one as canonical (e.g. `100tuerensaarbrueckens.de`) and redirect the rest. Two ways:

**a. Registrar-level HTTP redirect** (Hetzner, INWX, IONOS all support it). Set `100tueren.de` → 301 redirect → `https://100tuerensaarbrueckens.de`. No DNS to GH needed for the alias. Simplest.

**b. Cloudflare (free) Page Rule.** Useful if you want full control + analytics. Move alias DNS to Cloudflare, add Page Rule: `*100tueren.de/*` → 301 → `https://100tuerensaarbrueckens.de/$2`. Free.

GitHub Pages itself accepts only **one** custom domain per repo, so you can't add aliases as additional `Custom domain` entries.
