#!/usr/bin/env python3
"""Sprawdź kompletność eksportu, treść, obrazy i lokalne odnośniki."""
import json,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
def read(n):return json.loads((ROOT/'data'/n).read_text())
posts=read('posts.json');pages=read('pages.json');counts=read('source-counts.json');errors=[];external_assets=set();checked=0
assert len(posts)==len(set(p['id'] for p in posts))
assert set(read('source-inventory.json')['posts']) <= {p['id'] for p in posts}
assert len(read('source-inventory.json')['posts'])==counts['posts']['api_total']
assert set(read('source-inventory.json')['pages']) <= {p['id'] for p in pages}
assert len(read('source-inventory.json')['pages'])==counts['pages']['api_total']==9
assert len(list((ROOT/'posts').glob('*.html')))==len(posts)
assert len(list((ROOT/'pages').glob('*.html')))==len(pages)
index=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
assert len(index.select('.post-card'))==len(posts)
for file in ROOT.rglob('*.html'):
 soup=BeautifulSoup(file.read_text(),'html.parser')
 assert soup.html.get('lang')=='pl',file
 assert soup.title and soup.select_one('h1,h2'),file
 for tag in soup.find_all(True):
  urls=[tag[a] for a in ['href','src','poster'] if tag.get(a)]
  urls.extend(part.strip().split()[0] for part in tag.get('srcset','').split(',') if part.strip())
  for url in urls:
   p=urlsplit(url)
   if p.scheme or p.netloc:
    if tag.name in ['img','script','link'] and p.scheme in ['http','https']:external_assets.add(url)
    continue
   if not p.path:continue
   local=(file.parent/unquote(p.path)).resolve()
   if not local.is_file():errors.append((str(file.relative_to(ROOT)),url))
   checked+=1
 for link in soup.select('a[href^="../posts/"],a[href^="posts/"]'):
  assert 'wp-json' not in link['href']
 for iframe in soup.select('iframe'):assert iframe.get('title'),file
for records,folder in [(posts,'posts'),(pages,'pages')]:
 for item in records:
  files=list((ROOT/folder).glob(str(item['id'])+'-*.html'));assert len(files)==1,item['id']
  s=BeautifulSoup(files[0].read_text(),'html.parser');prose=s.select_one('.prose');assert prose is not None
  src=BeautifulSoup(item['content']['rendered'],'html.parser')
  assert len(src.select('table'))==len(prose.select('table')),(item['id'],'tables')
  assert len(src.select('iframe'))==len(prose.select('iframe')),(item['id'],'iframes')
  assert len(prose.select('img'))>=len(src.select('img')),(item['id'],'images')
  assert not re.search(r'ngg_shortcode_\d+_placeholder',str(prose)),item['id']
  # Every source paragraph/table/list cell keeps its textual content.
  for tag in src.select('p,td,th,li'):
   t=' '.join(tag.get_text(' ',strip=True).split())
   if t and t not in ' '.join(prose.get_text(' ',strip=True).split()):errors.append((item['id'],'missing text: '+t[:80]))
for ident,images in read('galleries.json').items():
 file=next((ROOT/'pages').glob(ident+'-*.html'));s=BeautifulSoup(file.read_text(),'html.parser');assert len(s.select('.gallery-photo'))==len(images)
print(f'Posty: {len(posts)}/{counts["posts"]["api_total"]}; podstrony: {len(pages)}/9; kategorie: {len(list((ROOT/"categories").glob("*.html")))}')
print(f'Sprawdzono lokalnych odnośników/zasobów: {checked}; błędy: {len(errors)}')
print(f'Zewnętrzne pliki obrazów/skryptów/stylów: {len(external_assets)}')
if errors:
 print(json.dumps(errors,ensure_ascii=False,indent=2));raise SystemExit(1)
print('Weryfikacja zakończona powodzeniem.')
