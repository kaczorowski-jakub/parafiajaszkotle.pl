#!/usr/bin/env python3
"""Pobierz publiczne obrazy i załączniki do lokalnego archiwum (uporządkowane katalogi)."""
import concurrent.futures, hashlib, json, re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
import requests
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://parafiajaszkotle.pl'

ICONS = {
    'news.png','intencje.png','bible.png','gallery.png','schedule.png',
    'hiking_9241479.png','funeral.png','cemetery.png','bus.png','priest.png',
    'preaching_4794074.png','warning.png','zakat.png','three-wise-men.png',
    'pray_10291961.png','jesus_3697178.png','cross.png','drums.png',
    'reading_7242466.png','learning_12251733.png','calendar_1581943.png',
    'ascension.png','polska_na_skale.png',
}
LOGO_EXACT = {
    'cropped-main-1.png','cropped-church-1-32x32.jpg','main.png',
    'arch-wro.png','kep-logo.jpg','kep_logo.png','logosamorzel100px.png',
}
LOGO_PREFIXES = ('herb_archidiecezji', 'cropped-church', 'cropped-cropped-church', 'cropped-jaszkotle', 'polski-lad-logo')
KOSCIOL_PREFIXES = ('kosciol-', 'jaszkotle_', 'jaszkotle-', 'inside_1', 'church.')
DOC_EXT = {'.pdf', '.docx', '.doc', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'}
TR = str.maketrans({'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z','Ą':'a','Ć':'c','Ę':'e','Ł':'l','Ń':'n','Ó':'o','Ś':'s','Ź':'z','Ż':'z'})

def clean_name(name: str) -> str:
    name = name.translate(TR).lower()
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'[^a-z0-9._\-]+', '-', name)
    name = re.sub(r'-{2,}', '-', name).strip('-')
    return name or 'plik'

def canonical(url):
    url = url.replace('http://llfzztv.cluster029.hosting.ovh.net', BASE).replace('https://llfzztv.cluster029.hosting.ovh.net', BASE)
    if url.startswith('//'): url = 'https:' + url
    if url.startswith('/wp-content/'): url = BASE + url
    p = urlsplit(url)
    if p.hostname in ('parafiajaszkotle.pl', 'www.parafiajaszkotle.pl'):
        return urlunsplit(('https', 'parafiajaszkotle.pl', p.path, '', ''))
    return url

def local_asset(url):
    p = urlsplit(canonical(url))
    return p.hostname == 'parafiajaszkotle.pl' and p.path.startswith('/wp-content/')

def classify_rel(url: str) -> str:
    path = urlsplit(canonical(url)).path
    name = clean_name(unquote(path.rsplit('/', 1)[-1]))
    m = re.match(r'^/wp-content/gallery/([^/]+)/(?:(thumbs)/)?(.+)$', path)
    if m:
        g = clean_name(m.group(1))
        if m.group(2):
            return f'assets/img/galeria/{g}/thumbs/{clean_name(m.group(3))}'
        return f'assets/img/galeria/{g}/{clean_name(m.group(3))}'
    orig_l = unquote(path.rsplit('/', 1)[-1]).lower()
    if Path(name).suffix.lower() in DOC_EXT:
        return f'assets/dokumenty/{name}'
    if orig_l in ICONS or name in ICONS:
        return f'assets/img/ikony/{name}'
    if orig_l in LOGO_EXACT or name in LOGO_EXACT or any(orig_l.startswith(p) for p in LOGO_PREFIXES):
        return f'assets/img/logo/{name}'
    if any(orig_l.startswith(p) for p in KOSCIOL_PREFIXES) or orig_l == 'church.jpg':
        return f'assets/img/galeria/kosciol/{name}'
    ym = re.match(r'^/wp-content/uploads/(\d{4})/\d{2}/', path)
    if ym:
        return f'assets/img/wpisy/{ym.group(1)}/{name}'
    return f'assets/img/wpisy/inne/{name}'

def collect():
    urls=set()
    for typ in ['posts','pages']:
        for item in json.loads((ROOT/'data'/f'{typ}.json').read_text()):
            soup = BeautifulSoup(item['content']['rendered'], 'html.parser')
            for tag in soup.find_all(True):
                for attr in ['src','href','poster']:
                    url=tag.get(attr, '')
                    if local_asset(url) or (tag.name in ('img','source') and attr == 'src' and url.startswith(('https://','http://'))):
                        urls.add(canonical(url))
                for part in tag.get('srcset','').split(','):
                    if part.strip():
                        url=part.strip().split()[0]
                        if local_asset(url): urls.add(canonical(url))
    for media in json.loads((ROOT/'data/media.json').read_text()):
        urls.add(canonical(media['source_url']))
    for images in json.loads((ROOT/'data/galleries.json').read_text()).values():
        for image in images:
            urls.update(canonical(image[k]) for k in ('image','thumbnail'))
    urls.update(BASE+u for u in [
        '/wp-content/uploads/2024/07/cropped-main-1.png',
        '/wp-content/uploads/2024/07/cropped-church-1-32x32.jpg',
        '/wp-content/uploads/2024/07/jaszkotle_4.jpg',
    ])
    return sorted(urls)

def main():
    manifest_path=ROOT/'data/asset-manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    def download(url):
        if url in manifest:
            existing = ROOT / manifest[url]
            if existing.exists():
                return url, manifest[url]
        rel = classify_rel(url)
        path = ROOT / rel
        owners = [u for u,r in manifest.items() if r == rel and u != url]
        if path.exists() and owners:
            h = hashlib.sha256(url.encode()).hexdigest()[:12]
            path = path.with_name(f'{path.stem}-{h}{path.suffix}')
            rel = path.relative_to(ROOT).as_posix()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            r=requests.get(url,timeout=(15,90)); r.raise_for_status()
            if 'text/html' in r.headers.get('content-type',''):
                raise ValueError('HTML zamiast pliku')
            path.write_bytes(r.content)
        return url, rel
    failures={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs={pool.submit(download,url):url for url in collect()}
        for i,f in enumerate(concurrent.futures.as_completed(jobs),1):
            url=jobs[f]
            try:
                u,rel=f.result(); manifest[u]=rel
            except Exception as e:
                failures[url]=str(e)
            if i%25==0:
                print(f'{i}/{len(jobs)} plików; błędy: {len(failures)}', flush=True)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/asset-errors.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n')
    print(f'Pobrano: {len(manifest)}, niepowodzenia: {len(failures)}', flush=True)

if __name__=='__main__':
    main()
