# Parafia Jaszkotle — strona statyczna

Nowa wersja strony parafialnej: **zwykłe pliki HTML, CSS i JavaScript**, bez WordPressa, bazy danych, usług płatnych i systemu budowania po stronie hostingu. Treść pochodzi z publicznej strony **https://parafiajaszkotle.pl**. Eksport wykonano 6 listopada 2026 r. (Europe/Warsaw).

## Co przeniesiono

- **273 unikalne posty** — tyle zwraca nagłówek `X-WP-Total` WordPressa; pobrano wszystkie trzy strony API (100 + 100 + 73). Zakres publikacji: 22.07.2024–02.11.2026.
- **9 podstron**: Kontakt, Cmentarze, Msze Św. i Nabożeństwa, Dokumenty, Galeria, Kościół, Remont Ołtarza, Remont Konfesjonału, Wszystkich Świętych 2026.
- **5 kategorii**, daty, tytuły, pełna treść HTML oraz odnośniki między wpisami.
- **200 lokalnych plików graficznych/załączników**: m.in. grafika nagłówka, favicon, zdjęcia wyróżniające, obrazy w treści i ich warianty.
- **Wszystkie 25 zdjęć widocznych w trzech galeriach NextGEN**: ołtarz — 14, konfesjonał — 3, Wszystkich Świętych 2026 — 8. Są lokalne miniatury i pełne zdjęcia; NextGEN nie jest potrzebny. Podstrona Kościół zachowuje ponadto własną galerię 9 zdjęć z WordPressa.

Suma liczników kategorii jest większa od 273, ponieważ wpis może należeć do kilku kategorii. Dane wejściowe i raport liczb znajdują się w `data/`.

## Podgląd na komputerze

```bash
cd /home/jakub-kaczorowski/git-repo/parafiajaszkotle.pl
python3 -m http.server 8000 --bind 127.0.0.1
```

Otwórz **http://localhost:8000**. Zatrzymaj serwer przez `Ctrl+C`.

Można też otworzyć `index.html` bezpośrednio w przeglądarce — odnośniki i obrazy są względne. Serwer lokalny jest jednak zalecany, zwłaszcza do sprawdzania dawnych adresów z parametrami i paginacji.

## Struktura

```text
index.html                 strona główna
posts/                     bieżące wpisy (angielskie slugi, numer NNNN- zachowany)
pages/                     podstrony informacyjne i galerie
categories/                archiwa kategorii
archive/                   zarchiwizowane wpisy i ich obrazki (nie wrzucamy na serwer)
assets/style.css           wygląd i układ na telefonach
assets/site.js             wyszukiwanie, paginacja, podgląd zdjęć
assets/legacy.js           mapa dawnych adresów WordPressa
assets/img/main/           stałe grafiki (logo, herby, mapy, logotypy partnerów)
assets/img/icons/          ikony wpisów
assets/img/gallery/        galerie zdjęć
assets/img/communities/    zdjęcia wspólnot
assets/img/posts/YYYY/     obrazki wpisów tylko z bieżącego roku
assets/documents/          PDF i inne załączniki
data/                      dane źródłowe JSON i raporty migracji
tools/build.py             powtarzalny generator HTML
tools/download_assets.py   opcjonalne pobieranie zasobów
tools/verify.py            weryfikacja liczebności i lokalnych odnośników
.htaccess                  przekierowania Apache/OVH (WordPress i dawne HTML)
sitemap.xml, robots.txt    pliki dla robotów wyszukiwarek
```

## Jak zmieniać treść tutaj

Możesz poprosić asystenta, np. „dodaj ogłoszenia na ten tydzień w tym katalogu” albo „zmień godziny kancelarii”.

**Źródłem treści są pliki JSON**: `data/posts.json` i `data/pages.json`. Treść każdego rekordu jest w `content.rendered` (HTML), tytuł w `title.rendered`, data publikacji w `date`, numery kategorii w `categories`. Rekordy kategorii są w `data/categories.json`, galerie w `data/galleries.json`. Zachowuj unikalne `id` oraz `slug`; dodając post, użyj nowego numeru `id` i daty lokalnej Europe/Warsaw. Miniatury wynikają z `featured_media` i `data/media.json`.

Jednorazowe przygotowanie narzędzi generatora:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r tools/requirements.txt
```

Po zmianie danych:

```bash
. .venv/bin/activate
python3 tools/build.py
python3 tools/verify.py
```

Zwykły podgląd/wgranie strony **nie wymaga instalowania żadnych bibliotek**. Biblioteki są potrzebne wyłącznie do ponownego generowania i testów. Generator działa bez pobierania treści z WordPressa; dane są już lokalne. Aby ponowić pobieranie obrazów, uruchom osobno `python3 tools/download_assets.py`. Nowe własne obrazy zapisuj w odpowiednim podkatalogu `assets/img/` (np. `icons/`, `gallery/…`, `communities/`, stałe grafiki w `main/`, obrazki wpisów w `posts/YYYY/`), a dokumenty w `assets/documents/`.

Wygląd edytuj w `assets/style.css`; wspólny nagłówek, stopkę i szablony w `tools/build.py`. Bezpośrednia zmiana wygenerowanego HTML działa, ale **zostanie nadpisana przy następnym generowaniu**. Generator nie usuwa sam starych plików po zmianie slug/usunięciu wpisu — stare ścieżki usuń świadomie, dodając w razie potrzeby przekierowania.

Repozytorium Git jest zainicjalizowane lokalnie; nie wysłano go na żaden serwer. Po sprawdzeniu możesz zrobić pierwszy commit: `git add . && git commit -m "Nowa statyczna strona parafii"`.

## Publikacja na OVH / własna domena

**Nic nie zostało opublikowane, DNS i obecna strona nie były zmieniane.**

1. Zrób kopię plików WordPressa, bazy danych i dotychczasowego `.htaccess` na OVH.
2. Najpierw wgraj nową stronę do osobnego katalogu testowego/subdomeny. Serwuj `index.html`, `posts/`, `pages/`, `categories/`, `assets/`, `robots.txt`, `sitemap.xml` i opcjonalnie `.htaccess`. Katalogów `archive/`, `data/`, `tools/`, `.git/` i środowiska `.venv/` nie wrzucamy na publiczny hosting.
3. Na istniejącym hostingu OVH zwykle wystarczy zmiana katalogu WWW domeny lub podmiana plików po akceptacji — DNS może pozostać bez zmian. Nie nadpisuj produkcyjnego WordPressa bez sprawdzenia kopii i wersji testowej.
4. Jeśli wybierzesz inny hosting statyczny, podepnij domenę zgodnie z instrukcją tego hostingu i dopiero potem ustaw odpowiednie rekordy A/AAAA lub CNAME w OVH. Zachowaj rekordy pocztowe MX/SPF/DKIM/DMARC.
5. Włącz certyfikat HTTPS dla obu wariantów domeny i wybierz jeden adres główny. Dotychczasowa strona to `parafiajaszkotle.pl`; jeśli nowy adres ma być **jaszkotle.pl**, zmień `BASE` w `tools/build.py`, wygeneruj pliki ponownie i skonfiguruj przekierowanie drugiej domeny.
6. `.htaccess` zawiera przekierowania dawnych adresów `?p=`, `?page_id=` i `?cat=` oraz dawnych statycznych ścieżek HTML (np. `posts/0280-ogloszenia-….html`) na nowe angielskie nazwy plików. Mapę utrzymuje generator w `data/redirects.json`. Na hostingu bez Apache mapa w `assets/legacy.js` obsługuje parametry WordPressa po stronie przeglądarki.

## Ograniczenia / świadome różnice

- Nie ma panelu WordPressa, bazy danych ani automatycznej synchronizacji z dawną stroną. To stan z dnia eksportu; dalsze poprawki wykonuje się w tym projekcie.
- Galerie NextGEN zostały zastąpione zwykłymi lokalnymi zdjęciami; funkcje pluginu nie zostały przeniesione. Dostępne publicznie galerie miały łącznie 25 zdjęć, bez dodatkowej paginacji.
- Filmy YouTube i odnośniki do obcych serwisów nadal potrzebują internetu. Same teksty i lokalne zdjęcia działają offline.
- Jeden rekord biblioteki mediów (`wp-content/uploads/2025/09/kep-log.htm`) zwraca dokument HTML, nie obraz/załącznik graficzny. Nie skopiowano go jako obrazu. **Nie jest używany w treści żadnego z 273 postów ani 9 podstron**, więc nie powoduje braku w ich treści. Szczegóły: `data/asset-errors.json`.
- Nie przenoszono zaplecza, wtyczek ani komentarzy; zakres migracji obejmuje wszystkie publiczne posty i podstrony dostępne w API.
- Dane kontaktowe, porządek nabożeństw i opłaty na cmentarzu przeniesiono z materiałów źródłowych bez aktualizowania ich merytorycznej treści; przed publikacją warto je potwierdzić w parafii.

## Nazwy plików po angielsku

Nazwy plików, katalogów i adresów podstron są po angielsku (kebab-case, ASCII). Treść strony, tytuły i menu zostają po polsku. Numeracja wpisów (`NNNN-`) jest zachowana.

Tygodniowe slugi generator tłumaczy automatycznie: `ogloszenia-…` → `announcements-…`, `intencje-…` → `mass-intentions-…`, `koleda-…` → `christmas-visits-…`. Pozostałe wpisy i podstrony mają mapę w `data/slugs-en.json`. Kategorie: `news`, `announcements`, `mass-intentions`, `curia`, `documents`, `sunday-word`.

## Archiwum wpisów i obrazków

Na stronę trafiają tylko wpisy z bieżącego roku oraz wpisy z kategorii Kuria i Dokumenty (ustawienie `ARCHIVE_BEFORE_YEAR` i `KEEP_CATEGORIES` w `tools/build.py`).
Starsze wpisy zostają w `data/posts.json`, a ich gotowe strony HTML leżą w `archive/posts/`. Katalogu `archive/` nie wrzucamy na serwer.

W `assets/img/posts/` ma być wyłącznie katalog bieżącego roku. Przy archiwizacji (na początku nowego roku, przy kolejnym `python3 tools/build.py`) generator sam przenosi obrazki ze starych lat:
- jeśli żywa strona ich nadal potrzebuje (np. mapa cmentarza, logo KEP) — do `assets/img/main/`;
- w przeciwnym razie — do `archive/img/posts/<rok>/`.

## Słowo na niedzielę

Wpis z kategorii „Słowo na niedzielę” (id 11) zawsze ma stały plik `posts/sunday-word.html` i nie dostaje numeru. Co tydzień poprzedni wpis jest podmieniany, więc na serwerze wystarczy nadpisać ten jeden plik.
