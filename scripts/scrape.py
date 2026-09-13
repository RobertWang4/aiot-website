#!/usr/bin/env python3
"""One-off scraper: recon.org.pl (WordPress + Elementor + Polylang) -> src/content/*.json

Sources:
  * homepage HTML per language  -> top nav + mega menu (10 categories -> services)
  * WP REST API /wp-json/wp/v2/pages -> page content (Elementor rendered HTML), yoast meta
Pairing PL<->EN is positional inside the mega menu (both languages have identical structure).
"""
import json, os, re, sys, hashlib
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup, Tag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "content")
IMG_DIR = os.path.join(ROOT, "public", "img")
BASE = "https://recon.org.pl"
HOME = {"pl": BASE + "/", "en": BASE + "/en/strona-glowna-english/"}
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (content migration script)"
report = {"pages": [], "missing": [], "images_failed": [], "anchors": []}


def get(url, **kw):
    r = S.get(url, timeout=60, **kw)
    r.raise_for_status()
    return r


def norm_path(href):
    """'http://recon.org.pl/en/foo/' or 'recon.org.pl/en/foo' -> '/en/foo/'"""
    if not href:
        return None
    if not re.match(r"^https?://", href):
        if href.startswith("/"):
            href = BASE + href
        elif href.startswith("recon.org.pl"):
            href = "https://" + href
        elif href.startswith("#"):
            return href
        else:
            return None
    u = urlparse(href)
    if "recon.org.pl" not in u.netloc:
        return None
    p = u.path
    if not p.endswith("/"):
        p += "/"
    return p + ("#" + u.fragment if u.fragment else "")


# ---------------------------------------------------------------- API index
def fetch_all_pages():
    pages = {}
    page = 1
    while True:
        r = get(f"{BASE}/wp-json/wp/v2/pages", params={"per_page": 100, "page": page,
                "_fields": "id,slug,link,title,content,yoast_head_json"})
        data = r.json()
        for p in data:
            pages[norm_path(p["link"])] = p
        if page >= int(r.headers.get("x-wp-totalpages", 1)):
            break
        page += 1
    return pages


# ---------------------------------------------------------------- HTML -> blocks
def text(el):
    return " ".join(el.get_text(" ", strip=True).split())


def is_nav_like_list(ul):
    """sidebar 'Offer > category > sibling links' lists: every li is just a link"""
    lis = ul.find_all("li", recursive=False)
    if not lis:
        return False
    for li in lis:
        a = li.find("a")
        if not a or text(a) != text(li):
            return False
    return True


def uploads_urls(el):
    urls = []
    for img in el.find_all("img"):
        src = img.get("data-src") or img.get("src")
        if src and "/wp-content/uploads/" in src:
            urls.append((src, img.get("alt", "")))
    for tag in el.find_all(style=True):
        for m in re.finditer(r"url\(['\"]?([^'\")]+)['\"]?\)", tag["style"]):
            if "/wp-content/uploads/" in m.group(1):
                urls.append((m.group(1), ""))
    for tag in el.find_all(attrs={"data-settings": True}):
        for m in re.finditer(r'https?:[^"\\]+/wp-content/uploads/[^"\\]+', tag["data-settings"]):
            urls.append((m.group(0).replace("\\/", "/"), ""))
    return urls


def download_image(url, lang, slug):
    url = url.replace("\\/", "/")
    name = os.path.basename(urlparse(url).path)
    # strip WP size suffix -300x200.jpg -> .jpg (try original first)
    orig = re.sub(r"-\d+x\d+(\.\w+)$", r"\1", name)
    rel_dir = slug
    os.makedirs(os.path.join(IMG_DIR, rel_dir), exist_ok=True)
    for candidate in (url.replace(name, orig), url):
        fname = os.path.basename(urlparse(candidate).path)
        dest = os.path.join(IMG_DIR, rel_dir, fname)
        if os.path.exists(dest):
            return f"/img/{rel_dir}/{fname}"
        try:
            r = S.get(candidate, timeout=60)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                open(dest, "wb").write(r.content)
                return f"/img/{rel_dir}/{fname}"
        except requests.RequestException:
            pass
    report["images_failed"].append(url)
    return None


def html_to_blocks(html, lang, slug, link_map):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "iframe", "form", "button"]):
        t.decompose()
    for ul in soup.find_all(["ul", "ol"]):
        if is_nav_like_list(ul):
            col = ul.find_parent(class_="elementor-column") or ul
            col.decompose()
    blocks, seen = [], set()

    def push(b):
        key = json.dumps(b, ensure_ascii=False, sort_keys=True)
        if key in seen:  # Elementor renders desktop + mobile copies
            return
        seen.add(key)
        blocks.append(b)

    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "img"]):
        if el.find_parent(["ul", "ol"]) and el.name != "img":
            continue
        if el.name == "img":
            src = el.get("data-src") or el.get("src")
            if src and "/wp-content/uploads/" in src:
                local = download_image(src, lang, slug)
                if local:
                    push({"type": "image", "src": local, "alt": el.get("alt", "")})
            continue
        if el.name in ("ul", "ol"):
            if is_nav_like_list(el):
                continue
            items = [text(li) for li in el.find_all("li") if text(li)]
            if items:
                push({"type": "list", "ordered": el.name == "ol", "items": items})
            continue
        t = text(el)
        if not t or t in ("–", "-", "—"):
            continue
        if el.name == "p":
            a = el.find("a")
            if a and text(a) == t:  # "Read more" style link paragraph
                target = link_map.get(norm_path(a.get("href")))
                if target:
                    push({"type": "cta", "label": t, "href": target})
                continue
            push({"type": "paragraph", "text": t})
        else:
            push({"type": "heading", "level": int(el.name[1]), "text": t})
    merged = []
    for b in blocks:
        prev = merged[-1] if merged else None
        if (prev and prev["type"] == "heading" and b["type"] == "heading" and "eyebrow" not in prev
                and prev["text"] == prev["text"].upper() and b["text"] != b["text"].upper()):
            merged[-1] = {"type": "heading", "level": b["level"], "eyebrow": prev["text"], "text": b["text"]}
        else:
            merged.append(b)
    return merged


def page_meta(p, blocks=None):
    y = p.get("yoast_head_json") or {}
    desc = y.get("description") or ""
    if not desc and blocks:
        desc = next((b["text"] for b in blocks if b["type"] == "paragraph"), "")
    if len(desc) > 160:
        desc = desc[:157].rsplit(" ", 1)[0] + "…"
    return {
        "title": BeautifulSoup(p["title"]["rendered"], "html.parser").get_text(),
        "description": desc,
    }


# ---------------------------------------------------------------- menus
def parse_home(lang):
    soup = BeautifulSoup(get(HOME[lang]).text, "html.parser")
    nav = soup.select_one("nav.wpr-nav-menu-container")
    top = []
    for li in nav.select("ul.wpr-nav-menu > li"):
        a = li.find("a")
        if not a or "lang-item" in " ".join(li.get("class", [])) or "pll-parent" in " ".join(li.get("class", [])):
            continue
        top.append({"label": text(a), "path": norm_path(a.get("href"))})
    mega = soup.select_one(".wpr-sub-mega-menu")
    cats, cur = [], None
    for el in mega.find_all(["h5", "a"]):
        if el.name == "h5":
            cur = {"label": text(el), "items": []}
            cats.append(cur)
        elif cur is not None and text(el):
            cur["items"].append({"label": text(el), "path": norm_path(el.get("href"))})
    return top, cats, soup


CATEGORY_IDS = ["machinery", "environment", "parts-processing", "occupational-medicine",
                "employment-agency", "workplace-measurements", "ohs", "fire-safety", "iso", "adr"]


def slug_of(path):
    return path.rstrip("/").split("/")[-1].split("#")[0]


# ---------------------------------------------------------------- home page structured
def parse_home_content(html, lang, link_map):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    lines = [l for l in soup.get_text("\n", strip=True).split("\n") if l.strip()]
    hero_links = [text(a) for a in soup.select(".hero-slide-wrapper a") if text(a)][:2]
    blocks = html_to_blocks(html, lang, "home", link_map)

    def idx(pred, default=-1):
        return next((i for i, l in enumerate(lines) if pred(l)), default)

    # 10 category cards: h4 followed by p
    cards = []
    for i, b in enumerate(blocks):
        if b["type"] == "heading" and b["level"] == 4 and i + 1 < len(blocks) and blocks[i + 1]["type"] == "paragraph":
            cards.append({"title": b["text"], "text": blocks[i + 1]["text"]})
    cards = cards[:10]
    ci = idx(lambda l: cards and l == cards[0]["title"])
    # maturity matrix: 5 x (name, desc, mgmt)
    stages = []
    for i, l in enumerate(lines):
        if re.search(r"Culture$|^Kultura ", l) and len(stages) < 5 and i + 2 < len(lines):
            if any(l == s["name"] for s in stages):
                continue
            stages.append({"name": l, "text": lines[i + 1], "management": lines[i + 2]})
    mi = idx(lambda l: "Matrix" in l or "Matryca" in l)
    phrases = next((b["items"] for b in blocks if b["type"] == "list" and len(b["items"]) >= 10), [])
    # closing band: [EYEBROW] [Headline] [value props...] [chain x6]
    hi = idx(lambda l: "Without Risk" in l or "Bez Ryzyka" in l)
    chain = lines[-6:]
    values, title_parts = [], []
    for l in lines[hi + 1:-6]:
        if l.endswith("."):
            values.append({"title": " ".join(title_parts), "text": l})
            title_parts = []
        else:
            title_parts.append(l)
    hero_p = next((b["text"] for b in blocks if b["type"] == "paragraph"), "")
    h2s = [b["text"] for b in blocks if b["type"] == "heading" and b["level"] == 2]
    return {
        "hero": {"headline": hero_p, "ctas": [{"label": hero_links[0] if hero_links else "", "href": f"/{lang}/about/"},
                                              {"label": hero_links[1] if len(hero_links) > 1 else "", "href": f"/{lang}/services/"}]},
        "asia": {"headline": next((h for h in h2s if "asia" in h.lower() or "azj" in h.lower()), ""),
                 "cta": lines[idx(lambda l: "Learn More" in l)] if idx(lambda l: "Learn More" in l) >= 0 else "",
                 "lines": [h for h in h2s if re.search(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]", h)]},
        "services": {"eyebrow": lines[ci - 2] if ci >= 2 else "", "headline": lines[ci - 1] if ci >= 1 else "", "cards": cards},
        "maturity": {"eyebrow": lines[mi - 1] if mi >= 1 else "", "headline": lines[mi] if mi >= 0 else "",
                     "axis": {"high": "High" if lang == "en" else "Wysokie",
                              "label": "Probability of accidents" if lang == "en" else "Prawdopodobieństwo wypadków",
                              "low": "Low" if lang == "en" else "Niskie"},
                     "stages": stages},
        "noBlame": {"headline": "No-Blame Culture" if lang == "en" else "Kultura Bez Obwiniania", "phrases": phrases},
        "closing": {"eyebrow": lines[hi - 1] if hi >= 1 else "", "headline": lines[hi] if hi >= 0 else "",
                    "values": values, "chain": chain},
        "_blocks": blocks,
    }


# ---------------------------------------------------------------- main
def main():
    os.makedirs(OUT, exist_ok=True)
    print("fetching page index...")
    pages = fetch_all_pages()
    print(f"  {len(pages)} pages in API")

    tops, cats, homes = {}, {}, {}
    for lang in ("pl", "en"):
        tops[lang], cats[lang], homes[lang] = parse_home(lang)
        print(f"  {lang}: {len(tops[lang])} top links, {len(cats[lang])} categories, "
              f"{sum(len(c['items']) for c in cats[lang])} services")

    # service ids shared across languages, positional
    services = {"pl": {}, "en": {}}
    categories_out = {"pl": [], "en": []}
    link_map = {"pl": {}, "en": {}}
    for ci, cid in enumerate(CATEGORY_IDS):
        n = min(len(cats["pl"][ci]["items"]), len(cats["en"][ci]["items"]))
        if len(cats["pl"][ci]["items"]) != len(cats["en"][ci]["items"]):
            report["missing"].append(f"category {cid}: pl={len(cats['pl'][ci]['items'])} en={len(cats['en'][ci]['items'])}")
        for lang in ("pl", "en"):
            cat = {"id": cid, "label": cats[lang][ci]["label"], "services": []}
            for si in range(n):
                item = cats[lang][ci]["items"][si]
                sid = slug_of(cats["en"][ci]["items"][si]["path"]) if "#" not in cats["en"][ci]["items"][si]["path"] \
                    else "anchor-" + cats["en"][ci]["items"][si]["path"].split("#")[1]
                item["id"] = sid
                cat["services"].append(sid)
                services[lang][sid] = {"id": sid, "category": cid, "label": item["label"], "path": item["path"]}
                if "#" not in item["path"]:
                    link_map[lang][item["path"]] = f"/{lang}/services/{sid}/"
            categories_out[lang].append(cat)

    # main pages: resolve by nav order (home, about, services, gallery, clients, contact)
    MAIN_IDS = ["home", "about", "services", "gallery", "clients", "contact"]
    for lang in ("pl", "en"):
        for i, t in enumerate(tops[lang][:6]):
            link_map[lang][t["path"]] = f"/{lang}/" + ("" if MAIN_IDS[i] == "home" else MAIN_IDS[i] + "/")

    for lang in ("pl", "en"):
        ldir = os.path.join(OUT, lang)
        os.makedirs(os.path.join(ldir, "services"), exist_ok=True)
        # --- services detail pages
        for sid, s in services[lang].items():
            if "#" in s["path"]:
                report["anchors"].append(f"{lang}:{sid} -> {s['path']}")
                data = {"id": sid, "category": s["category"], "title": s["label"], "hasPage": False, "blocks": []}
            else:
                p = pages.get(s["path"])
                if not p:
                    report["missing"].append(f"{lang}: no API page for {s['path']}")
                    continue
                blocks = html_to_blocks(p["content"]["rendered"], lang, sid, link_map[lang])
                # drop leading duplicate of page title
                meta = page_meta(p, blocks)
                if blocks and blocks[0]["type"] == "heading" and blocks[0]["text"] == meta["title"]:
                    blocks = blocks[1:]
                data = {"id": sid, "category": s["category"], "menuLabel": s["label"], "hasPage": True,
                        **meta, "sourceUrl": BASE + s["path"], "blocks": blocks}
                report["pages"].append(f"{lang}/services/{sid} ({len(blocks)} blocks)")
            json.dump(data, open(os.path.join(ldir, "services", sid + ".json"), "w"), ensure_ascii=False, indent=2)
        json.dump({"categories": categories_out[lang]}, open(os.path.join(ldir, "services.json"), "w"), ensure_ascii=False, indent=2)

        # --- main pages
        for i, t in enumerate(tops[lang][:6]):
            mid = MAIN_IDS[i]
            p = pages.get(t["path"])
            if not p:
                report["missing"].append(f"{lang}: no API page for main {mid} {t['path']}")
                continue
            if mid == "home":
                data = parse_home_content(p["content"]["rendered"], lang, link_map[lang])
                meta = page_meta(p, data.pop("_blocks"))
                data = {**meta, "sourceUrl": BASE + t["path"], **data}
            else:
                blocks = html_to_blocks(p["content"]["rendered"], lang, mid, link_map[lang])
                data = {**page_meta(p, blocks), "sourceUrl": BASE + t["path"], "blocks": blocks}
            fname = "services-page.json" if mid == "services" else mid + ".json"  # services.json is the category index
            json.dump(data, open(os.path.join(ldir, fname), "w"), ensure_ascii=False, indent=2)
            report["pages"].append(f"{lang}/{mid}")

    # --- site.json
    site = {
        "brand": {"name": "AIoT P.S.A.", "logo": "/img/logo.jpg", "colors": {"navy": "#0B1B4A", "blue": "#2F6BFF"}},
        "contact": {"email": "office@recon.org.pl", "phone": "+48 691 741 999",
                    "address": "ul. Strzelińska 6, 58-100 Świdnica, Poland"},
        "social": {},
        "languages": ["pl", "en"],
        "defaultLanguage": "pl",
        "nav": {lang: [{"id": MAIN_IDS[i], "label": t["label"], "href": link_map[lang][t["path"]]}
                       for i, t in enumerate(tops[lang][:6])] for lang in ("pl", "en")},
    }
    json.dump(site, open(os.path.join(OUT, "site.json"), "w"), ensure_ascii=False, indent=2)

    with open(os.path.join(ROOT, "scripts", "scrape-report.md"), "w") as f:
        f.write("# Scrape report\n\n")
        f.write(f"API pages: {len(pages)}\n\n## Pages written ({len(report['pages'])})\n")
        f.writelines(f"- {p}\n" for p in report["pages"])
        f.write(f"\n## Menu items that are anchors (no detail page) ({len(report['anchors'])})\n")
        f.writelines(f"- {p}\n" for p in report["anchors"])
        f.write(f"\n## Missing / mismatches ({len(report['missing'])})\n")
        f.writelines(f"- {p}\n" for p in report["missing"])
        f.write(f"\n## Images failed ({len(report['images_failed'])})\n")
        f.writelines(f"- {p}\n" for p in report["images_failed"])
    print("done. see scripts/scrape-report.md")


if __name__ == "__main__":
    main()
