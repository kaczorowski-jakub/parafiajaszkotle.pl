#!/usr/bin/env python3
"""Jednorazowe przeniesienie i angielskie nazwy plików/katalogów."""
from __future__ import annotations
import json, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# old relative path -> new relative path (only existing files are moved)
FILE_MAP = {
    # documents
    'assets/dokumenty/60rocznicaoredzie.pdf': 'assets/documents/60th-anniversary-address.pdf',
    'assets/dokumenty/arytul-oltarz.pdf': 'assets/documents/altar-article.pdf',
    'assets/dokumenty/regulamin-cmentarza-parafilanego-w-jaszkotlu-01.02.21.pdf': 'assets/documents/jaszkotle-cemetery-regulations-2021-02-01.pdf',
    'assets/dokumenty/standardy_ochrony_maloletnich.pdf': 'assets/documents/standards-for-protection-of-minors.pdf',
    # main / former logo
    'assets/img/logo/cropped-church-1-32x32.jpg': 'assets/img/main/site-favicon.jpg',
    'assets/img/logo/cropped-main-1.png': 'assets/img/main/site-logo.png',
    'assets/img/logo/herb_archidiecezji_wroclawskiej-198x300.jpg': 'assets/img/main/wroclaw-archdiocese-arms-198x300.jpg',
    'assets/img/logo/herb_archidiecezji_wroclawskiej-300x455.jpg': 'assets/img/main/wroclaw-archdiocese-arms-300x455.jpg',
    'assets/img/logo/herb_archidiecezji_wroclawskiej-scaled.jpg': 'assets/img/main/wroclaw-archdiocese-arms.jpg',
    'assets/img/logo/logosamorzel100px.png': 'assets/img/main/eagle-guard-logo.png',
    'assets/img/logo/niezbednik-katolika.png': 'assets/img/main/catholic-handbook.png',
    'assets/img/logo/orla-straz.png': 'assets/img/main/eagle-guard.png',
    'assets/img/logo/polski-lad-logo-300x200.webp': 'assets/img/main/polish-deal-logo-300x200.webp',
    'assets/img/logo/polski-lad-logo.webp': 'assets/img/main/polish-deal-logo.webp',
    'assets/img/logo/wojownicy-maryi.png': 'assets/img/main/warriors-of-mary.png',
    # icons (only those with Polish names; others move with the directory)
    'assets/img/ikony/intencje.png': 'assets/img/icons/mass-intentions.png',
    'assets/img/ikony/polska_kontur.png': 'assets/img/icons/poland-outline.png',
    'assets/img/ikony/polska_na_skale.png': 'assets/img/icons/poland-on-the-rock.png',
    # communities
    'assets/img/wspolnoty/ojciec-pio.jpg': 'assets/img/communities/padre-pio.jpg',
    'assets/img/wspolnoty/zywy-rozaniec.jpg': 'assets/img/communities/living-rosary.jpg',
    # gallery church
    'assets/img/galeria/kosciol/kosciol-3.jpg': 'assets/img/gallery/church/church-3.jpg',
    'assets/img/galeria/kosciol/kosciol-4.jpg': 'assets/img/gallery/church/church-4.jpg',
    'assets/img/galeria/kosciol/kosciol-5.jpg': 'assets/img/gallery/church/church-5.jpg',
    # gallery altar
    'assets/img/galeria/remont-oltarza/oltarz-2024.jpg': 'assets/img/gallery/altar-renovation/altar-2024.jpg',
    'assets/img/galeria/remont-oltarza/thumbs/thumbs-oltarz-2024.jpg': 'assets/img/gallery/altar-renovation/thumbs/thumbs-altar-2024.jpg',
    # year images: live vs archive
    'assets/img/wpisy/2024/mapka-1024x626.png': 'assets/img/main/cemetery-map.png',
    'assets/img/wpisy/2025/kep-logo-1.jpg': 'assets/img/main/kep-logo.jpg',
    'assets/img/wpisy/2024/faustyna.jpg': 'archive/img/posts/2024/faustina.jpg',
    'assets/img/wpisy/2025/img-20250121-wa0005-724x1024.jpg': 'archive/img/posts/2025/img-20250121-wa0005-724x1024.jpg',
    # 2026 post images with Polish names
    'assets/img/wpisy/2026/rekolekcje-adwentowe-2026.jpg': 'assets/img/posts/2026/advent-retreat-2026.jpg',
    'assets/img/wpisy/2026/meskie-poruszenie_plakat-pielgrzymka-maj-2026-final-kopia-1086x1536-1-724x1024.png': 'assets/img/posts/2026/mens-movement-pilgrimage-poster-may-2026.png',
    'assets/img/wpisy/2026/baner-na-strone-poprawna-kolejnosc-miast-1024x576.png': 'assets/img/posts/2026/pilgrimage-banner-towns.png',
    'assets/img/wpisy/2026/konfesjonal_przed-690x1024.jpg': 'assets/img/posts/2026/confessional-before.jpg',
    'assets/img/wpisy/2026/328337_wqmm_jozefitki_83.jpg.webp': 'assets/img/posts/2026/josephites-328337.webp',
}

# Directory prefix replacements for files not listed above (English already, or camera names).
# Longest prefixes first.
DIR_PREFIXES = [
    ('assets/img/galeria/wszystkich-swietych-2026/', 'assets/img/gallery/all-saints-2026/'),
    ('assets/img/galeria/remont-konfesjonalu/', 'assets/img/gallery/confessional-renovation/'),
    ('assets/img/galeria/remont-oltarza/', 'assets/img/gallery/altar-renovation/'),
    ('assets/img/galeria/kosciol/', 'assets/img/gallery/church/'),
    ('assets/img/galeria/', 'assets/img/gallery/'),
    ('assets/img/ikony/', 'assets/img/icons/'),
    ('assets/img/wspolnoty/', 'assets/img/communities/'),
    ('assets/img/logo/', 'assets/img/main/'),
    ('assets/img/wpisy/', 'assets/img/posts/'),
    ('assets/dokumenty/', 'assets/documents/'),
]


def new_path_for(old: str) -> str:
    if old in FILE_MAP:
        return FILE_MAP[old]
    for a, b in DIR_PREFIXES:
        if old.startswith(a):
            return b + old[len(a):]
    return old


def move_assets() -> dict[str, str]:
    moved = {}
    # collect all files under assets (and nothing else yet)
    files = [p for p in (ROOT / 'assets').rglob('*') if p.is_file()]
    # plan
    plans = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        dest = new_path_for(rel)
        if dest != rel:
            plans.append((rel, dest))
            moved[rel] = dest
    # detect collisions
    dests = [d for _, d in plans]
    if len(dests) != len(set(dests)):
        raise SystemExit('destination collision in asset moves')
    for rel, dest in plans:
        src = ROOT / rel
        dst = ROOT / dest
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists() and dst.resolve() != src.resolve():
            raise SystemExit(f'would overwrite {dest}')
        shutil.move(str(src), str(dst))
        print(f'moved {rel} -> {dest}')
    # remove now-empty old dirs
    for old in [
        'assets/dokumenty',
        'assets/img/logo', 'assets/img/ikony', 'assets/img/wspolnoty',
        'assets/img/galeria/wszystkich-swietych-2026/thumbs',
        'assets/img/galeria/wszystkich-swietych-2026',
        'assets/img/galeria/remont-konfesjonalu/thumbs',
        'assets/img/galeria/remont-konfesjonalu',
        'assets/img/galeria/remont-oltarza/thumbs',
        'assets/img/galeria/remont-oltarza',
        'assets/img/galeria/kosciol',
        'assets/img/galeria',
        'assets/img/wpisy/2024', 'assets/img/wpisy/2025', 'assets/img/wpisy/2026',
        'assets/img/wpisy',
        'assets/img/posts/2024', 'assets/img/posts/2025',  # emptied by special moves
    ]:
        d = ROOT / old
        if d.is_dir() and not any(d.rglob('*')):
            d.rmdir()
            # rmdir only if empty; parents may need a second pass
            print('removed empty', old)
    # rmdir parents if empty
    for old in ['assets/img/wpisy', 'assets/img/galeria', 'assets/img/posts/2024', 'assets/img/posts/2025']:
        d = ROOT / old
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            print('removed empty', old)
    return moved


def update_manifest(moved: dict[str, str]):
    path = ROOT / 'data' / 'asset-manifest.json'
    data = json.loads(path.read_text())
    n = 0
    for url, rel in list(data.items()):
        # exact move
        if rel in moved:
            data[url] = moved[rel]
            n += 1
            continue
        # prefix rewrite for leftover (including unused _nieuzywane paths in data)
        new = new_path_for(rel)
        # also translate unused dir names in manifest values
        new = (new
               .replace('assets/img/_nieuzywane/wpisy/', 'assets/img/_unused/posts/')
               .replace('assets/img/_nieuzywane/galeria/', 'assets/img/_unused/gallery/')
               .replace('assets/img/_nieuzywane/ikony/', 'assets/img/_unused/icons/')
               .replace('assets/img/_nieuzywane/logo/', 'assets/img/_unused/main/')
               .replace('assets/img/_nieuzywane/dokumenty/', 'assets/img/_unused/documents/')
               .replace('assets/img/_nieuzywane/', 'assets/img/_unused/'))
        if new != rel:
            data[url] = new
            n += 1
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    print('manifest paths updated:', n)


def update_links():
    path = ROOT / 'data' / 'links.json'
    data = json.loads(path.read_text())
    for item in data:
        icon = item.get('icon') or ''
        if icon:
            item['icon'] = new_path_for(icon)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('links.json icons updated')


def snapshot_old_html_paths() -> list[str]:
    old = []
    for folder in ['posts', 'pages', 'categories']:
        d = ROOT / folder
        if d.is_dir():
            for p in sorted(d.glob('*.html')):
                old.append(f'{folder}/{p.name}')
    arch = ROOT / 'archiwum' / 'posts'
    if arch.is_dir():
        for p in sorted(arch.glob('*.html')):
            old.append(f'archiwum/posts/{p.name}')
    return old


def main():
    old_html = snapshot_old_html_paths()
    (ROOT / 'data' / 'legacy-html-paths.json').write_text(
        json.dumps(old_html, ensure_ascii=False, indent=1) + '\n')
    print('snapshotted old html paths:', len(old_html))
    moved = move_assets()
    update_manifest(moved)
    update_links()
    print('asset moves:', len(moved))


if __name__ == '__main__':
    main()
