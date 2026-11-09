'use strict';
// All navigation and post content remain accessible without JavaScript.
(() => {
  const legacy = window.parishLegacy;
  if (legacy) {
    const q = new URLSearchParams(location.search);
    const target = legacy.posts[q.get('p')] || legacy.pages[q.get('page_id')] || legacy.categories[q.get('cat')];
    if (target) { location.replace(target + location.hash); return; }
  }
  const list = document.getElementById('post-list');
  if (list) {
    const cards = Array.from(list.children);
    const search = document.getElementById('search');
    const pagination = document.getElementById('pagination');
    const status = document.getElementById('search-status');
    const size = cards.length <= 6 ? 6 : 12;
    let page = 1;
    const normalize = s => s.toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l');
    const params = new URLSearchParams(location.search);
    search.value = params.get('szukaj') || '';
    page = Math.max(1,parseInt(params.get('strona') || '1',10) || 1);
    search.closest('.search-control').hidden = false;
    const prev = document.createElement('button');prev.textContent = '← Poprzednia';prev.type = 'button';
    const counter = document.createElement('span');
    const next = document.createElement('button');next.textContent = 'Następna →';next.type = 'button';
    pagination.append(prev,counter,next);
    function render(updateUrl = true) {
      const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
      const filtered = cards.filter(c => words.every(w => normalize(c.dataset.title).includes(w)));
      const pages = Math.max(1,Math.ceil(filtered.length / size));
      page = Math.min(page,pages);
      cards.forEach(c => c.hidden = true);
      filtered.slice((page-1)*size,page*size).forEach(c => c.hidden = false);
      status.textContent = filtered.length ? `Wpisy ${(page-1)*size+1}–${Math.min(page*size,filtered.length)} z ${filtered.length}` : 'Brak wpisów pasujących do wyszukiwania. Spróbuj innej frazy.';
      pagination.hidden = filtered.length <= size;
      prev.disabled = page <= 1; next.disabled = page >= pages;
      counter.textContent = `Strona ${page} z ${pages}`;
      if (updateUrl) {
        const u = new URL(location.href);
        if(page>1)u.searchParams.set('strona',page);else u.searchParams.delete('strona');
        if(search.value.trim())u.searchParams.set('szukaj',search.value.trim());else u.searchParams.delete('szukaj');
        try { history.replaceState(null,'',u); } catch (_) { /* file:// preview */ }
      }
    }
    search.addEventListener('input',()=>{page=1;render();});
    prev.addEventListener('click',()=>{page--;render();document.getElementById('archive-heading').scrollIntoView({block:'start'});});
    next.addEventListener('click',()=>{page++;render();document.getElementById('archive-heading').scrollIntoView({block:'start'});});
    render(false);
  }

  const dialog = document.getElementById('lightbox');
  if (dialog && typeof dialog.showModal === 'function') {
    const image = dialog.querySelector('img');
    const caption = document.getElementById('lightbox-caption');
    const btnPrev = document.getElementById('prev-lightbox');
    const btnNext = document.getElementById('next-lightbox');
    const btnClose = document.getElementById('close-lightbox');
    let previousFocus = null;
    let group = [];
    let index = 0;

    function groupFor(anchor) {
      const root = anchor.closest('.photo-grid, .wp-block-gallery, .gallery-index, .prose, article') || document;
      const list = Array.from(root.querySelectorAll('a[data-lightbox]'));
      return list.length ? list : [anchor];
    }

    function show(i) {
      index = (i + group.length) % group.length;
      const a = group[index];
      const thumb = a.querySelector('img');
      image.removeAttribute('width');
      image.removeAttribute('height');
      image.style.width = 'auto';
      image.style.height = 'auto';
      image.src = a.href;
      image.alt = thumb ? thumb.alt : '';
      if (caption) caption.textContent = group.length > 1 ? (index + 1) + ' / ' + group.length : '';
      btnPrev.hidden = group.length < 2;
      btnNext.hidden = group.length < 2;
      previousFocus = a;
    }

    function open(anchor) {
      group = groupFor(anchor);
      index = Math.max(0, group.indexOf(anchor));
      show(index);
      if (!dialog.open) dialog.showModal();
    }

    document.querySelectorAll('a[data-lightbox]').forEach(a => a.addEventListener('click', e => {
      e.preventDefault();
      open(a);
    }));

    // Also open plain gallery figures that are not wrapped yet
    document.querySelectorAll('.wp-block-gallery img').forEach(img => {
      const wrap = img.closest('a[data-lightbox]');
      if (wrap) return;
      const a = document.createElement('a');
      a.href = img.currentSrc || img.src;
      a.dataset.lightbox = 'true';
      a.className = 'gallery-photo';
      img.replaceWith(a);
      a.appendChild(img);
      a.addEventListener('click', e => { e.preventDefault(); open(a); });
    });

    btnPrev.addEventListener('click', e => { e.stopPropagation(); show(index - 1); });
    btnNext.addEventListener('click', e => { e.stopPropagation(); show(index + 1); });
    btnClose.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
    dialog.addEventListener('close', () => { if (previousFocus) previousFocus.focus(); });
    document.addEventListener('keydown', e => {
      if (!dialog.open) return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
    });
  }
})();

// Galeria: bieżący rok rozwinięty, starsze zwinięte
(function(){var y=String(new Date().getFullYear()),d=document.querySelectorAll('details.gallery-year');if(!d.length)return;var has=false;d.forEach(function(e){if(e.dataset.year===y)has=true});d.forEach(function(e,i){e.open=has?e.dataset.year===y:i===0});})();
