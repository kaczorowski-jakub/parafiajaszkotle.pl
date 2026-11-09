#!/usr/bin/env python3
"""Generator statycznej strony; dane edytuje się w data/*.json."""
import html, json, re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
from bs4 import BeautifulSoup
from download_assets import canonical
ROOT=Path(__file__).resolve().parents[1]
BASE='https://parafiajaszkotle.pl'
def load(name): return json.loads((ROOT/'data'/f'{name}.json').read_text())
def esc(s): return html.escape(str(s),quote=True)
def text(s): return BeautifulSoup(s,'html.parser').get_text(' ',strip=True)
POSTS=sorted(load('posts'),key=lambda x:(bool(x.get('sticky')),x['date'],x['id']),reverse=True)
PAGES=load('pages'); CATS=load('categories'); MEDIA={x['id']:x for x in load('media')}
ASSETS=load('asset-manifest'); GALLERIES=load('galleries')
try: GALLERY_ALIASES=load('gallery-aliases')
except FileNotFoundError: GALLERY_ALIASES={}
LINKS_EXT=load('links')
CAT={x['id']:x for x in CATS}; PAGE={x['id']:x for x in PAGES}
def slugify_text(s):
 tr=str.maketrans({'ą':'a','ć':'c','ę':'e','ł':'l','ń':'n','ó':'o','ś':'s','ź':'z','ż':'z','Ą':'a','Ć':'c','Ę':'e','Ł':'l','Ń':'n','Ó':'o','Ś':'s','Ź':'z','Ż':'z'})
 s=BeautifulSoup(s,'html.parser').get_text(' ',strip=True).translate(tr).lower()
 s=re.sub(r'[^a-z0-9]+','-',s).strip('-')
 return s
def clean_slug(x):
 raw=unquote(x.get('slug') or '')
 # WordPress zostawial dlugie lancuchy -2/-3 przy powielanych slugach.
 if re.search(r'(?:-2){3,}', raw) or re.search(r'(?:-3-2){2,}', raw) or len(raw)>80:
  title=x.get('title',{})
  title=title.get('rendered', title) if isinstance(title, dict) else str(title)
  s=slugify_text(title)
  # doklej date zeby uniknac kolizji ogloszen/intencji
  d=(x.get('date') or '')[:10]
  if d: s=f'{s}-{d}' if s else d
 else:
  s=re.sub(r'(?:-[23])+$','',raw)
  s=re.sub(r'-{2,}','-',s)
  s=re.sub(r'[^a-zA-Z0-9_-]','-',s).strip('-').lower()
 return s or str(x['id'])
POSTS_ASC=sorted(POSTS,key=lambda x:(x['date'],x['id']))
POST_NUM={p['id']:i for i,p in enumerate(POSTS_ASC,1)}
def post_path(x):return f"posts/{POST_NUM[x['id']]:04d}-{clean_slug(x)}.html"
def page_path(x):return f"pages/{x['id']}-{clean_slug(x)}.html"
PATHS={**{x['id']:post_path(x) for x in POSTS},**{x['id']:page_path(x) for x in PAGES}}
SKIP_PAGES={1064}
for _sid in list(SKIP_PAGES):
 PATHS.pop(_sid, None)
CATPATH={x['id']:f'categories/{clean_slug(x)}.html' for x in CATS}
LINKS={x['link'].rstrip('/'):PATHS[x['id']] for x in POSTS+PAGES if x['id'] in PATHS}
MONTHS=['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia']
def date(s):
 d=datetime.fromisoformat(s);return f'{d.day} {MONTHS[d.month-1]} {d.year}'
def relative(path,prefix):return prefix+path

def rewrite(url,prefix):
 if not url:return url
 if url.startswith(('#','mailto:','tel:','data:')):return url
 # Repair two malformed legacy WP links in the source.
 url=re.sub(r'(https?://(?:www\.)?parafiajaszkotle\.pl)\?',r'\1/?',url)
 fixed=canonical(url)
 if fixed in ASSETS:return prefix+ASSETS[fixed]
 parsed=urlsplit(url)
 if parsed.hostname and parsed.hostname not in ['parafiajaszkotle.pl','www.parafiajaszkotle.pl','llfzztv.cluster029.hosting.ovh.net']:
  return url
 query=parse_qs(parsed.query)
 for key,mapping in [('p',PATHS),('page_id',PATHS),('cat',CATPATH)]:
  if key in query:
   try:
    target=mapping.get(int(query[key][0]))
    if target:return prefix+target+('#'+parsed.fragment if parsed.fragment else '')
   except ValueError:pass
 normalized=(BASE+parsed.path).rstrip('/')
 if normalized in LINKS:return prefix+LINKS[normalized]+('#'+parsed.fragment if parsed.fragment else '')
 if parsed.path in ['','/','/index.php'] and not parsed.query:return prefix+'index.html'+('#'+parsed.fragment if parsed.fragment else '')
 return url


def asset_path_for_url(url):
 """Lokalna ścieżka z manifestu (bez prefixu ../)."""
 if not url: return ''
 fixed=canonical(url)
 return ASSETS.get(fixed, '')

def is_icon_asset(path):
 """True, gdy asset to ikona z assets/img/ikony/ (lub legacy media z nazwą ikony)."""
 if not path: return False
 p=path.replace('\\','/').lstrip('./')
 if '/ikony/' in p or p.startswith('assets/img/ikony/'): return True
 # fallback: znane ikony po nazwie pliku
 name=p.rsplit('/',1)[-1].lower()
 icon_names={'news.png','intencje.png','bible.png','gallery.png','schedule.png','hiking_9241479.png','funeral.png','cemetery.png','bus.png','priest.png','preaching_4794074.png','warning.png','zakat.png','three-wise-men.png','pray_10291961.png','jesus_3697178.png','cross.png','drums.png','polska_na_skale.png','polska_kontur.png','reading_7242466.png','learning_12251733.png','calendar_1581943.png','ascension.png'}
 return name in icon_names

def strip_duplicate_icon(html_str, icon_path):
 """Usuń z treści pierwszy <img>/<figure> wskazujący tę samą ikonę co wyróżniająca."""
 if not html_str or not icon_path: return html_str
 soup=BeautifulSoup(html_str,'html.parser')
 icon_name=icon_path.rsplit('/',1)[-1].lower()
 for img in soup.find_all('img'):
  src=(img.get('src') or '').split('?')[0]
  if icon_name and src.lower().endswith(icon_name):
   fig=img.find_parent('figure')
   (fig or img).decompose()
   break
 return str(soup)

def categories(item,prefix):
 return ' '.join(f'<a class="tag" href="{prefix+CATPATH[c]}">{esc(CAT[c]["name"])}</a>' for c in item.get('categories',[]) if c in CAT)

def resolve_gallery(item):
 """Zdjęcia NextGEN: po id pozycji, aliasie lub dopasowaniu tytułu do strony-galerii."""
 key=str(item['id'])
 if key in GALLERIES: return GALLERIES[key]
 alias=GALLERY_ALIASES.get(key) or GALLERY_ALIASES.get(item['id'])
 if alias is not None and str(alias) in GALLERIES: return GALLERIES[str(alias)]
 raw=item.get('content',{}).get('rendered','') if isinstance(item.get('content'),dict) else ''
 if 'ngg_shortcode' not in raw: return []
 title=slugify_text(html.unescape(item['title']['rendered'] if isinstance(item['title'],dict) else str(item['title'])))
 if not title: return []
 best=None; best_score=-1
 for pid,imgs in GALLERIES.items():
  page=PAGE.get(int(pid))
  if not page: continue
  pt=slugify_text(html.unescape(page['title']['rendered']))
  score=0
  if pt==title: score=100
  elif pt.startswith(title) or title.startswith(pt): score=80
  elif title in pt or pt in title: score=60
  if score>best_score:
   best_score=score; best=imgs
 return best if best_score>=60 else []

def render_photo_grid(images,title,prefix):
 return '<div class="photo-grid">'+''.join(f'<a class="gallery-photo" href="{esc(rewrite(i["image"],prefix))}" data-lightbox="true"><img loading="lazy" src="{esc(rewrite(i["thumbnail"],prefix))}" alt="{esc(title)} — zdjęcie {n}" width="240" height="160"><span>Zdjęcie {n} <span aria-hidden="true">↗</span></span></a>' for n,i in enumerate(images,1))+'</div>'

def content(item,prefix):
 raw=item['content']['rendered']
 images=resolve_gallery(item)
 title=html.unescape(item['title']['rendered'])
 gallery=render_photo_grid(images,title,prefix) if images else '<p>Galeria jest dostępna w archiwum źródłowym.</p>'
 raw=re.sub(r'ngg_shortcode_\d+_placeholder',gallery,raw)
 soup=BeautifulSoup(raw,'html.parser')
 for tag in soup.find_all(['script','style','form']):tag.decompose()
 for tag in soup.find_all(True):
  for attr in list(tag.attrs):
   if attr.startswith('on') or attr.startswith('data-wp-'):del tag[attr]
  for attr in ['href','src','poster']:
   if tag.get(attr):
    val=tag[attr]
    tag[attr]=rewrite(val,prefix) if not val.lstrip().lower().startswith(('javascript:','vbscript:')) else '#'
  if tag.get('srcset'):
   tag['srcset']=', '.join(' '.join([rewrite(part.strip().split()[0],prefix)]+part.strip().split()[1:]) for part in tag['srcset'].split(',') if part.strip())
  if tag.name=='img':tag['loading']='lazy';tag['decoding']='async'
  if tag.name=='iframe':
   tag['loading']='lazy';tag['title']=tag.get('title','Materiał wideo');tag['referrerpolicy']='strict-origin-when-cross-origin'
  if tag.name=='a' and tag.get('target')=='_blank':tag['rel']='noopener noreferrer'
  if tag.name=='table':
   wrapper=soup.new_tag('div',attrs={'class':'table-scroll','tabindex':'0','role':'region','aria-label':'Tabela — przewiń w poziomie, aby zobaczyć całą treść'})
   tag.wrap(wrapper)
 # Replace WP-only accordion buttons with native accessible details elements.
 for block in soup.select('.wp-block-accordion-item'):
  button=block.select_one('button'); panel=block.select_one('.wp-block-accordion-item__content')
  if panel is None:panel=block.select_one('[role="region"]')
  if button and panel:
   detail=soup.new_tag('details');detail['open']='';summary=soup.new_tag('summary')
   label=button.select_one('.wp-block-accordion-heading__toggle-title');summary.string=(label or button).get_text(' ',strip=True)
   detail.append(summary)
   for child in list(panel.contents):detail.append(child.extract())
   block.replace_with(detail)
  elif button:
   heading=soup.new_tag('h3');heading.string=button.get_text(' ',strip=True).rstrip('+').strip();button.replace_with(heading)
 if item['id']==1061:
  def tile(pid):
   title=html.unescape(PAGE[pid]['title']['rendered'])
   imgs=GALLERIES.get(str(pid),[])
   # pelne zdjecie zamiast nextgen thumbs (niska jakosc / mocno wyciete)
   src=rewrite(imgs[0]['image'],prefix) if imgs else ''
   img=(f'<img loading="lazy" src="{esc(src)}" alt="" width="640" height="400">' if src else '<span class="gallery-tile-fallback" aria-hidden="true"></span>')
   return f'<a class="gallery-tile" href="{prefix+PATHS[pid]}">{img}<span class="gallery-tile-meta"><strong>{esc(title)}</strong><small>Zobacz galerię</small></span></a>'
  church_soup=BeautifulSoup(PAGE[1064]['content']['rendered'],'html.parser')
  church_imgs=[]
  for im in church_soup.find_all('img'):
   src=im.get('src') or ''
   if not src: continue
   full=rewrite(src,prefix)
   if im.get('srcset'):
    parts=[p.strip().split()[0] for p in im['srcset'].split(',') if p.strip()]
    if parts: full=rewrite(parts[-1],prefix)
   n=len(church_imgs)+1
   church_imgs.append(f'<a class="gallery-photo" href="{esc(full)}" data-lightbox="true"><img loading="lazy" src="{esc(full)}" alt="Kościół w Jaszkotlu — zdjęcie {n}" width="240" height="160"></a>')
  church_grid=('<div class="photo-grid">'+''.join(church_imgs)+'</div>') if church_imgs else '<p>Brak lokalnych zdjęć kościoła.</p>'
  return (
   '<section class="gallery-index">'
   '<h2>Wydarzenia</h2>'
   + ''.join(f'<details class="gallery-year" data-year="{y}"'+(' open' if y==str(datetime.now().year) else '')+f'><summary>{y}</summary><div class="gallery-tiles">'+''.join(tile(i) for i in ids)+'</div></details>' for y,ids in [('2026',[1354,1192]),('2025',[1093])]) +
   '<h2>Kościół</h2>'
   '<p>Zdjęcia kościoła parafialnego w Jaszkotlu.</p>'
   f'{church_grid}'
   '</section>'
  )
 return str(soup)

def nav(prefix,current):
 items=[('index.html','Aktualności')]+[(CATPATH[7],'Intencje'),(CATPATH[6],'Ogłoszenia')]+[(PATHS[i],label) for i,label in [(172,'Msze i nabożeństwa'),(1061,'Galeria'),(212,'Dokumenty'),(97,'Cmentarze')]]+[('pages/grupy-i-wspolnoty.html','Grupy i Wspólnoty'),('pages/linki.html','Linki'),(PATHS[90],'Kontakt')]
 return ''.join(f'<a href="{prefix+path}"'+(' aria-current="page"' if current==path else '')+f'>{label}</a>' for path,label in items)

def shell(title,body,path,description='',home=False):
 prefix='' if '/' not in path else '../'
 logo=ASSETS[BASE+'/wp-content/uploads/2024/07/cropped-main-1.png']
 icon=ASSETS[BASE+'/wp-content/uploads/2024/07/cropped-church-1-32x32.jpg']
 return f'''<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} — Parafia Jaszkotle</title><meta name="description" content="{esc(description or 'Aktualności, ogłoszenia i intencje mszalne. Informacje o życiu parafii w Jaszkotlu.')}"><meta name="theme-color" content="#173e36"><link rel="icon" href="{prefix+icon}"><link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/site.js" defer></script></head>
<body><a class="skip" href="#tresc">Przejdź do treści</a><div class="topline"><div class="wrap">Jaszkotle <span aria-hidden="true">·</span> Sadków <a href="{prefix+PATHS[90]}">Kontakt z parafią <span aria-hidden="true">↗</span></a></div></div>
<header class="site-header"><div class="wrap brand-row"><a class="brand" href="{prefix}index.html"><img src="{prefix+logo}" alt="" width="72" height="72"><span>Parafia Jaszkotle<small>Wspólnota, która łączy</small></span></a><a class="header-shortcut" href="{prefix+PATHS[172]}"><span>Msze święte</span><small>Porządek nabożeństw →</small></a></div><nav class="wrap primary-nav" aria-label="Menu główne">{nav(prefix,path)}</nav></header>
<main id="tresc" tabindex="-1">{body}</main>
<footer class="site-footer"><div class="wrap footer-grid"><div><strong>Parafia Jaszkotle</strong><p>Jaszkotle 26, 55-080 Kąty Wrocławskie</p><a href="{prefix+PATHS[90]}">Kontakt i kancelaria →</a></div><div><strong>Życie parafii</strong><a href="{prefix+CATPATH[6]}">Ogłoszenia parafialne</a><a href="{prefix+CATPATH[7]}">Intencje mszalne</a><a href="{prefix+PATHS[1061]}">Galeria</a><a href="{prefix}pages/grupy-i-wspolnoty.html">Grupy i Wspólnoty</a></div><div><strong>Galerie i wydarzenia</strong>{''.join(f'<a href="{prefix+PATHS[i]}">{esc(html.unescape(PAGE[i]["title"]["rendered"]))}</a>' for i in [1354,1192,1093])}</div></div><div class="wrap footer-bottom"><span>© {datetime.now().year} Parafia Jaszkotle · created by Jakub Kaczorowski · <a href="mailto:off.soft.group@gmail.com">off.soft.group@gmail.com</a>, NIP 9491905872</span> <a href="#tresc">Wróć na górę ↑</a></div></footer>
<dialog id="lightbox" aria-label="Podgląd zdjęcia"><button type="button" id="close-lightbox" aria-label="Zamknij zdjęcie">Zamknij ×</button><button type="button" id="prev-lightbox" aria-label="Poprzednie zdjęcie">‹</button><button type="button" id="next-lightbox" aria-label="Następne zdjęcie">›</button><div class="lightbox-stage"><img alt=""></div><span id="lightbox-caption"></span></dialog></body></html>'''

def card(item,prefix):
 title=html.unescape(item['title']['rendered']);excerpt=text(item['excerpt']['rendered']) or text(item['content']['rendered'])
 excerpt=excerpt[:180].rsplit(' ',1)[0]+'…' if len(excerpt)>180 else excerpt
 thumbnail=''
 if item.get('featured_media') in MEDIA:
  media=MEDIA[item['featured_media']]; url=media.get('media_details',{}).get('sizes',{}).get('medium',{}).get('source_url',media['source_url'])
  if canonical(url) not in ASSETS:url=media['source_url']
  thumbnail=f'<a class="post-thumbnail" href="{prefix+PATHS[item["id"]]}" tabindex="-1" aria-hidden="true"><img src="{esc(rewrite(url,prefix))}" loading="lazy" alt="" width="120" height="100"></a>'
 return f'<article class="post-card" data-categories="{esc(" ".join(map(str,item.get("categories",[]))))}" data-title="{esc(title)}"><div class="post-card-content"><div class="post-meta"><time datetime="{item["date"][:10]}">{date(item["date"])}</time>{categories(item,prefix)}</div><h3><a href="{prefix+PATHS[item["id"]]}">{esc(title)}</a></h3><p>{esc(excerpt)}</p><a class="read-more" href="{prefix+PATHS[item["id"]]}">Czytaj więcej <span aria-hidden="true">→</span><span class="sr-only">: {esc(title)}</span></a></div>{thumbnail}</article>'

def sidebar(prefix):
 return f'''<aside class="sidebar" aria-label="Przydatne informacje"><section class="info-card green-card"><span class="eyebrow">ZAPRASZAMY DO WSPÓLNEJ MODLITWY</span><h2>Msze święte</h2><h3>Jaszkotle · niedziele i święta</h3><div class="mass-times">08:00 <span>11:30</span> 17:00</div><p>Pełny porządek mszy świętych i nabożeństw, również w Sadkowie, znajdziesz poniżej.</p><a href="{prefix+PATHS[172]}">Msze i nabożeństwa →</a></section><section class="info-card"><span class="eyebrow">JESTEŚMY BLISKO</span><h2>Kontakt z parafią</h2><p>Jaszkotle 26<br>55-080 Kąty Wrocławskie</p><p><a href="tel:+48713906914">71 390 69 14</a><br><a class="email" href="mailto:jaszkotle@archidiecezja.wroc.pl">jaszkotle@archidiecezja.wroc.pl</a></p><a class="text-link" href="{prefix+PATHS[90]}">Kancelaria parafialna →</a></section></aside>'''

def listing(items,path,category=None):
 prefix='' if path=='index.html' else '../'
 hero=''
 if category is None:
  church=ASSETS[BASE+'/wp-content/uploads/2024/07/jaszkotle_4.jpg']
  hero=f'''<section class="hero"><div class="wrap hero-inner"><div><span class="eyebrow">WITAMY NA STRONIE PARAFII</span><h1>Blisko Boga.<br>Blisko siebie.</h1><p>Życie naszej wspólnoty w Jaszkotlu i Sadkowie.<br>Ogłoszenia, intencje i wszystko, co ważne.</p><a class="button" href="{PATHS[172]}">Msze święte i nabożeństwa <span aria-hidden="true">→</span></a></div><img src="{church}" alt="Kościół w Jaszkotlu" width="640" height="427" fetchpriority="high"></div></section>'''
  quick=[]
  for c,label in [(6,'Najnowsze ogłoszenia'),(7,'Najnowsze intencje')]:
   item=next(x for x in POSTS if c in x.get('categories',[]))
   quick.append(f'<a class="quick-link" href="{PATHS[item["id"]]}"><span>{label}</span><strong>{esc(html.unescape(item["title"]["rendered"]))}</strong><span aria-hidden="true">→</span></a>')
  hero+='<div class="wrap quick-links">'+''.join(quick)+'</div>'
 else:
  hero=f'<div class="wrap breadcrumb"><a href="../index.html">Strona główna</a> / Kategorie</div>'
 chips=[]
 for c in [None]+sorted(CATS,key=lambda x:[6,7,11,1,10,9].index(x['id']) if x['id'] in [6,7,11,1,10,9] else 99):
  ident=c['id'] if c else None;active=ident==category;label=c['name'] if c else 'Wszystkie';count=sum(ident in x.get('categories',[]) for x in POSTS) if c else len(POSTS)
  target=prefix+CATPATH[ident] if c else prefix+'index.html'
  chips.append(f'<a class="filter{ " active" if active else ""}" href="{target}"'+(' aria-current="page"' if active else '')+f'>{esc(label)} <span>{count}</span></a>')
 heading=CAT[category]['name'] if category else 'Życie parafii'
 total_label=(f'{len(items)} najnowszych z {len(POSTS)}' if category is None else f'{len(items)} wpisów')
 body=hero+f'''<div class="wrap main-grid"><section class="archive" aria-labelledby="archive-heading"><div class="section-heading"><div><span class="eyebrow">AKTUALNOŚCI I ARCHIWUM</span><h2 id="archive-heading">{esc(heading)}</h2></div><span class="archive-total">{total_label}</span></div><nav class="filters" aria-label="Kategorie wpisów">{''.join(chips)}</nav><div class="search-control" hidden><label for="search">Szukaj w tytułach wpisów</label><input id="search" type="search" placeholder="Np. ogłoszenia, listopad, 2025…" autocomplete="off"></div><p id="search-status" class="search-status" aria-live="polite"></p><div id="post-list">{''.join(card(x,prefix) for x in items)}</div><div class="pagination" id="pagination" hidden></div><noscript><p>Wyświetlono wszystkie wpisy w tej kategorii. Możesz użyć wyszukiwania w przeglądarce (Ctrl+F).</p></noscript></section>{sidebar(prefix)}</div>'''
 return shell(heading,body,path,home=category is None)

def main():
 for folder in ['posts','pages','categories']:(ROOT/folder).mkdir(exist_ok=True)
 (ROOT/'index.html').write_text(listing(POSTS[:6],'index.html'))
 for cat in CATS:
  path=CATPATH[cat['id']];(ROOT/path).write_text(listing([p for p in POSTS if cat['id'] in p.get('categories',[])],path,cat['id']))
 for group in [POSTS,PAGES]:
  for item in group:
   if item['id'] in SKIP_PAGES: continue
   path=PATHS[item['id']];prefix='../';title=html.unescape(item['title']['rendered']);ispost=item in POSTS
   meta=f'<div class="article-meta">Opublikowano <time datetime="{item["date"][:10]}">{date(item["date"])}</time><div class="article-categories">{categories(item,prefix)}</div></div>' if ispost else ''
   featured=''; title_icon=''; featured_icon_path=''
   if item.get('featured_media') in MEDIA:
    m=MEDIA[item['featured_media']]
    feat_src=rewrite(m['source_url'],prefix)
    feat_path=asset_path_for_url(m['source_url'])
    if is_icon_asset(feat_path) or is_icon_asset(feat_src):
     featured_icon_path=feat_path or feat_src
     title_icon=f'<img class="article-title-icon" src="{esc(feat_src)}" alt="" aria-hidden="true" width="40" height="40" loading="lazy" decoding="async">'
    else:
     featured=f'<figure class="article-featured"><img src="{esc(feat_src)}" alt="{esc(m.get("alt_text", ""))}" loading="lazy"></figure>'
   related=''
   if ispost:
    pos=POSTS.index(item);neighbors=[]
    for idx,label in [(pos+1,'← Starszy wpis'),(pos-1,'Nowszy wpis →')]:
     if 0<=idx<len(POSTS):
      n=POSTS[idx];neighbors.append(f'<a href="{prefix+PATHS[n["id"]]}"><span>{label}</span>{esc(html.unescape(n["title"]["rendered"]))}</a>')
    related='<nav class="article-neighbors" aria-label="Sąsiednie wpisy">'+''.join(neighbors)+'</nav>'
   back=('<p class="back-link"><a href="../pages/1061-galeria.html">← Wróć do galerii</a></p>' if (not ispost and item['id'] in {1093,1192,1354}) else '<p class="back-link"><a href="../index.html">← Wróć do aktualności</a></p>')
   crumb_mid=(' <a href="../pages/1061-galeria.html">Galeria</a> /' if (not ispost and item['id'] in {1093,1192,1354}) else '')
   prose_html=content(item,prefix)
   if featured_icon_path:
    prose_html=strip_duplicate_icon(prose_html, featured_icon_path)
   body=f'<div class="wrap breadcrumb"><a href="../index.html">Strona główna</a> /{crumb_mid} <span>{esc(title)}</span></div><div class="wrap main-grid article-grid"><article class="article"><header class="article-header"><span class="eyebrow">{"Z ŻYCIA PARAFII" if ispost else "INFORMACJE PARAFIALNE"}</span><h1>{title_icon}<span>{esc(title)}</span></h1>{meta}</header>{featured}<div class="prose">{prose_html}</div>{related}{back}</article>{sidebar(prefix)}</div>'
   (ROOT/path).write_text(shell(title,body,path,text(item['excerpt']['rendered'])[:160] if 'excerpt' in item else ''))
 # Strona Linki (zaprzyjaznione strony ze starego menu)
 path='pages/linki.html';prefix='../'
 tiles=''.join(
  f'<a class="gallery-tile link-tile" href="{esc(l["url"])}" target="_blank" rel="noopener noreferrer">'
  f'<span class="gallery-tile-meta"><strong>{esc(l["name"])}</strong>'
  f'<small>{esc(l["url"].replace("https://","").replace("http://","").rstrip("/"))}</small></span></a>'
  for l in LINKS_EXT)
 body=(
  '<div class="wrap breadcrumb"><a href="../index.html">Strona g\u0142\u00f3wna</a> / <span>Linki</span></div>'
  '<div class="wrap main-grid article-grid"><article class="article">'
  '<header class="article-header"><span class="eyebrow">POLECAMY</span><h1>Linki</h1>'
  '<p class="article-meta">Strony zaprzyja\u017anione i pomocne w \u017cyciu wiary.</p></header>'
  f'<div class="prose"><div class="gallery-tiles">{tiles}</div></div>'
  '<p class="back-link"><a href="../index.html">\u2190 Wr\u00f3\u0107 do aktualno\u015bci</a></p>'
  f'</article>{sidebar(prefix)}</div>'
 )
 # decode unicode escapes in static parts
 body=body.encode('utf-8').decode('unicode_escape') if False else (
  f'<div class="wrap breadcrumb"><a href="../index.html">Strona główna</a> / <span>Linki</span></div>'
  f'<div class="wrap main-grid article-grid"><article class="article">'
  f'<header class="article-header"><span class="eyebrow">POLECAMY</span><h1>Linki</h1>'
  f'<p class="article-meta">Strony zaprzyjaźnione i pomocne w życiu wiary.</p></header>'
  f'<div class="prose"><div class="gallery-tiles">{tiles}</div></div>'
  f'<p class="back-link"><a href="../index.html">← Wróć do aktualności</a></p>'
  f'</article>{sidebar(prefix)}</div>'
 )
 (ROOT/path).write_text(shell('Linki', body, path, 'Linki do zaprzyjaźnionych stron i materiałów katolickich.'))
 # Strona Grupy i Wspólnoty
 path='pages/grupy-i-wspolnoty.html';prefix='../'
 groups=[
  {'title':'Grupa modlitwy św. Ojca Pio','img':'assets/img/wspolnoty/ojciec-pio.jpg','alt':'Święty Ojciec Pio'},
  {'title':'Żywy Różaniec','img':'assets/img/wspolnoty/zywy-rozaniec.jpg','alt':'Różaniec'},
 ]
 tiles=''.join(
  f'<div class="gallery-tile community-tile">'
  f'<img src="{prefix+g["img"]}" alt="{esc(g["alt"])}" loading="lazy" width="480" height="360">'
  f'<span class="gallery-tile-meta"><strong>{esc(g["title"])}</strong>'
  f'<small class="coming-soon">Strona w budowie</small></span></div>'
  for g in groups)
 body=(
  f'<div class="wrap breadcrumb"><a href="../index.html">Strona główna</a> / <span>Grupy i Wspólnoty</span></div>'
  f'<div class="wrap main-grid article-grid"><article class="article">'
  f'<header class="article-header"><span class="eyebrow">ŻYCIE PARAFII</span><h1>Grupy i Wspólnoty</h1>'
  f'<p class="article-meta">Wspólnoty działające przy parafii w Jaszkotlu.</p></header>'
  f'<div class="prose"><div class="gallery-tiles community-tiles">{tiles}</div></div>'
  f'<p class="back-link"><a href="../index.html">← Wróć do aktualności</a></p>'
  f'</article>{sidebar(prefix)}</div>'
 )
 (ROOT/path).write_text(shell('Grupy i Wspólnoty', body, path, 'Grupy i wspólnoty parafialne: Grupa modlitwy św. Ojca Pio oraz Żywy Różaniec.'))
 # Legacy query URLs still work on static hosts with JavaScript.
 legacy={'posts':{str(x['id']):PATHS[x['id']] for x in POSTS},'pages':{str(x['id']):PATHS[x['id']] for x in PAGES if x['id'] in PATHS},'categories':{str(c):p for c,p in CATPATH.items()}}
 (ROOT/'assets/legacy.js').write_text('window.parishLegacy = '+json.dumps(legacy,ensure_ascii=False)+';')
 index=(ROOT/'index.html').read_text().replace('<script src="assets/site.js" defer>','<script src="assets/legacy.js" defer></script><script src="assets/site.js" defer>')
 (ROOT/'index.html').write_text(index)
 # Apache/OVH optional permanent redirects for the original query URLs.
 rules=['# Opcjonalne reguły dla Apache/OVH. Nie są potrzebne do podglądu lokalnego.','DirectoryIndex index.html','<IfModule mod_rewrite.c>','RewriteEngine On']
 for key,mapping in [('p',legacy['posts']),('page_id',legacy['pages']),('cat',legacy['categories'])]:
  for ident,path in mapping.items():rules.extend([f'RewriteCond %{{QUERY_STRING}} (^|&){key}={ident}(&|$)',f'RewriteRule ^(?:index\\.php)?$ {path} [R=301,L,NE,QSD]'])
 rules.append('</IfModule>');(ROOT/'.htaccess').write_text('\n'.join(rules)+'\n')
 urls=['index.html','pages/linki.html','pages/grupy-i-wspolnoty.html']+list(PATHS.values())+list(CATPATH.values())
 (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}/{esc(p)}</loc></url>' for p in urls)+'</urlset>')
 (ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nDisallow: /data/\nDisallow: /tools/\nSitemap: {BASE}/sitemap.xml\n')
 report={'posts':len(POSTS),'pages':len(PAGES),'categories':len(CATS),'gallery_images':{i:len(a) for i,a in GALLERIES.items()},'local_assets':len(ASSETS),'source':BASE,'generated_at':datetime.now().astimezone().isoformat()}
 (ROOT/'data/migration-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
