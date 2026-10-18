# Galaxian Coop – raport z implementacji (RC5)

Data: 2026-10-18. Branch: `game/galaxian-coop` (bez merge do `main`, bez remote, bez push).
Wersja: **RC5** – tożsamość wizualna pilotów: zielone pociski P1, własna sylwetka statku P2.
RC4: naprawa HUD wyniku, Red Laser Overdrive (W4 na 30 s, ×2, dźwięki, agresja wrogów),
trwałe W2, W3 za 4000, kolory pocisków P1/P2, wyśrodkowane lasery, licznik etapu i odliczanie W4.
Sekcja R5 opisuje RC5, R4 – RC4, R3 – RC3, sekcja 0 – RC2, sekcje 1–9 – RC1. Starsze sekcje są aktualne poza
miejscami poprawionymi w nowszych (np. W3 za 5000 i W4 na stałe – zmienione w RC4).
Autor moda: Zvgelo. Szczegóły techniczne: [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md),
[MEMORY_MAP.md](MEMORY_MAP.md), testy i pomiary: [TESTING.md](TESTING.md).

## R5. RC5 – tożsamość wizualna pilotów

### R5.1 Pliki

| Plik | Ścieżka | SHA-256 |
|---|---|---|
| ROM RC5 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.nes` (40 976 B) | `d83b98968846b24a91d17a8564df82e5c354909b3806b5a932f28dee2f6c0c03` |
| Etykiety Mesen 2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.mlb` | – |
| Łatka BPS (w git) | `games/galaxian-coop/patches/Galaxian_Coop.bps` (4 735 B) | nałożona na oryginał daje plik identyczny bajt w bajt (sprawdzone) |
| Zrzuty (nie w git) | `games/galaxian-coop/build/screenshots/` | `ships.png`, `w4_w4.png` (z testów), `compare_*.png` (przed/po) |

Wyniki RC4 z testu manualnego na emulatorze: 11/12 PASS. FAIL: żółte pociski P1 i pomarańczowe P2 łatwo pomylić; uwaga:
statki P1 i P2 zbyt podobne.

### R5.2 Analiza palet, CHR i OAM

Przeanalizowałem wszystkie sprite'y rysowane w 36 000 klatkach gry (co-op i 1P): kafel × paleta ×
indeks koloru (tabela w REVERSE_ENGINEERING.md §7). Wnioski:
- Każda paleta sprite'ów ma zajęte wszystkie 3 kolory. Kolor 3 (`$27`) wszędzie jest pomarańczowy.
  Paleta 0: statek P2, jego pociski, białe pociski wrogów (kolor 1), punkty za flagowce. Palety 1–3:
  czerwoni, fioletowi i zieloni nurkujący (kolor 3 = 1 piksel w dwóch z czterech kafli, czyli 2 px na
  obcego). Paleta 1 to dodatkowo flagowce i eksplozje (kolor 3 na wielu pikselach).
- Gwiazdy (kafel `$32`) używają tylko koloru 1, więc zmiana koloru 3 ich nie dotyka.
- Statek P1 to tło w palecie BG 0, tej samej co tekst HUD (czerwony `$16`, biały `$30`, cyjan `$2C`).
  Pozostałe palety BG mają jako kolor 2 niebieski `$11`. Przestawienie atrybutu wierszy statku na inną
  paletę dałoby mu niebieskie gondole zamiast białych, a zmiana palety BG 0 przemalowałaby HUD.

### R5.3 Kolory (konkretne kolory NES)

- **P1: `$2A`, jasna, intensywna zieleń** (w cynes RGB 76, 208, 32). Ten sam bajt co w RC4: `$E1CF`,
  paleta sprite'ów 2, kolor 3 (`$28` → `$2A`). Wyraźnie jaśniejsza od zielonych obcych `$1A`
  (RGB 8, 124, 0) i różna od białych pocisków wrogów `$30`.
- **P2: `$27`, ciepły pomarańcz** (RGB 212, 136, 32), paleta 0, kolor 3, bez zmian.
- Warianty odrzucone. Paleta 3 zmieniłaby częstszych zielonych obcych, paleta 1 eksplozje i flagowce,
  paleta 0 nos statku P2 i jego pociski. `$1A`/`$19` jest za bliski zielonym obcym, `$3A` za blady.
- **Skutek uboczny**: 2 piksele nurkującego fioletowego obcego są zielone (w oryginale pomarańczowe,
  w RC4 żółte). Formacja i pozostali obcy są bez zmian, co sprawdza test pikseli w realnej grze.

### R5.4 Statek P2

- **Nowa sylwetka P2** (`build.P2_PIXELS`, kafle `$E1`/`$EA`, rysowana jak dotąd jako lewa połówka i jej
  lustrzane odbicie):
  - spiczasty nos w kształcie delty z białą kabiną zamiast okrągłej kopuły;
  - gondole ze ściętym, płaskim szczytem;
  - rozdzielone stateczniki ogonowe.
- **Kolory P2:** te same (pomarańczowy, niebieski, biały).
- **Kontrole w `build.py`:** symetria oraz identyczny prostokąt jak u P1 (kolumny 2–14, wiersze 0–15).
  Środek, pozycje OAM (x = P2_X + `$79`, y `$D0`), hitboksy (kod bez zmian) i liczba sprite'ów (4) są
  takie jak w RC4.
- **P1:** kolory statku zostają, zgodnie z zasadą ze specyfikacji (statek P1 korzysta ze wspólnej palety
  tła). Statki rozróżnia sylwetka P2 oraz kolory pocisków.

### R5.5 Zrzuty przed/po (`build/screenshots/`)

- `compare_ships_rc4_rc5.png`: statki RC4 (góra) i RC5 (dół), ×8, ten sam zapisany stan.
- `compare_w4_rc4_rc5.png`: scena W4/W4, ta sama klatka w RC4 i RC5 (×2).
- `compare_purple_diver_orig_rc4_rc5.png`: nurkujący fioletowy obcy: oryginalny kolor, RC4, RC5 (×10).
- `ships.png`, `w4_w4.png`: z testów RC5 (statki obok siebie; obaj piloci w Overdrive w realnej grze).

Porównania powstały z jednego stanu zapisanego w cynes. RC4 i RC5 mają ten sam kod, a paleta jest
podstawiona w stanie, więc różnią się tylko grafiką.

### R5.6 Respawn Shield

Miganie bez zmian (ten sam kod). Test `test_shield_blink_silhouettes` sprawdza w każdej klatce
4-sekundowego migania, że statek jest albo dokładnie swoim obrazem, albo w ogóle niewidoczny: bez
częściowych kafli i bez mieszania obrazów. Partner przez cały czas jest dokładny. Po tarczy oba statki
są dokładne, a wiersze nametable P1 są takie jak przed śmiercią.

### R5.7 Testy (wykonane)

- **cynes:** 89/89 OK. Doszło 7 nowych testów, `test_shot_colours` napisany od nowa, żaden
  wcześniejszy test nie został usunięty:
  - kolory wszystkich 8 slotów na W1–W4, przy strzelaniu jednoczesnym i naprzemiennym, po śmierci i po
    Life Sharing;
  - kształt i kolor laserów;
  - piksel po pikselu obrazy obu statków w ruchu i przy krawędziach;
  - układ OAM P2 i brak dodatkowych sprite'ów;
  - hitboksy (pocisk wroga przesuwany o −12…+12 px: P1 i P2 trafiane z tych samych 11 przesunięć);
  - kolory wszystkich sprite'ów wrogów w 3000 klatkach realnej gry;
  - miganie tarczy;
  - HUD przy W4/W4.
- **FCEUmm:** 5/5 OK (doszły odcień pocisków i sylwetki statków).
- **Tracer:** 4/4 OK.
- Środek pocisków na wizualnej sylwetce P2 i podział rastra sprawdzają testy z RC4
  (`test_shots_centred_on_ships`, `test_raster_split_below_formation`).
- Nie testowałem w Mesen 2, RetroArch, w teście manualnym ani na sprzęcie.

### R5.8 Wydajność

- **Kod:** PRG RC5 = PRG RC4 poza bajtem palety. Tracer: 20 000 klatek co-op, ten sam input, identyczny
  RAM w każdej klatce, identyczne zapisy APU i liczba cykli CPU (606 780 229).
- **Stress test cynes** (obaj na W4 z agresją, 8 pocisków, ×2, 24 × 3 min):
  - bez tarcz: najgorsza klatka 96 iteracji (RC4 100);
  - z tarczami: 73 (RC4 74);
  - 0 resetów, 0 klatek opóźnienia.
- **Różnice w liczbach:** cynes startuje z losowego stanu, więc sesje to inne gry niż w RC4.
  Dlatego RC4 i RC5 uruchomiłem jeszcze krokowo z tego samego zapisanego stanu, z tym samym wejściem: 48 sesji
  (24 bez tarcz, 24 z tarczami, po 3 min): ilość wolnego czasu CPU identyczna w każdej klatce, te same najgorsze
  wartości w każdej sesji, 0 klatek z różnicą. Brak regresji wydajności.

### R5.9 Ograniczenia

- 2 piksele fioletowych obcych w nurkowaniu są zielone, a nie pomarańczowe.
- Statek P1 bez zielonego akcentu: wspólna paleta z HUD.
- Ikona życia P2 w HUD (kafel tła 8×8) jest dalej uproszczonym statkiem, wspólnym z P1.
- Zielony P1 i pomarańczowy P2 pochodzą z palety cynes. Na innych emulatorach i na sprzęcie odcienie
  będą trochę inne (FCEUmm: odcień sprawdzony testem).
- RC5 nie jest zaakceptowane przed testem manualnym na emulatorze.

## R4. RC4

### R4.1 Pliki

| Plik | Ścieżka | SHA-256 |
|---|---|---|
| ROM RC4 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.nes` (40 976 B) | `423f4be6d698caeff618a6a035cdd752eb007ffa8281c5af60a0f715be25af6c` |
| Etykiety Mesen 2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.mlb` | – |
| Łatka BPS (w git) | `games/galaxian-coop/patches/Galaxian_Coop.bps` (4 735 B) | `tools/bps.py apply` na oryginale daje plik identyczny bajt w bajt (sprawdzone `cmp`); test `test_bps_patch` sprawdza też, że łatka nie zawiera danych oryginału |

Nowy kod 4 465 B, 160 bajtów oryginału zmienionych w hookach (w tym 1 bajt palety). Oryginalny ROM
nienaruszony (SHA-256 `1188cedf…3613e`). Zdjęć z testu manualnego nie miałem w tej sesji – diagnoza oparta na opisie
(odczyty „2130G0”, „4140.0”, P1 X0 14530) i na odtworzeniu w emulatorze.

### R4.2 Glitche punktacji P1 – przyczyna (punkty 1–3 raportu)

**Przyczyna.** Wiersz wyników `$0116–$012F` to w oryginale obszar wyświetlany, nie tylko dane:
- `E307` (w `E2FE`) kopiuje **15 bajtów `$0117–$0125`** – wynik P1, dwa bajty „luki” `$011D/$011E`,
  `$011F` i hi-score – do bufora HUD `$06A0`, który `E342` wysyła do wiersza 4 nametable (kolumny 4–18);
- po GAME OVER `FB70` + `E4AA` zapisują całe 26 bajtów `$0116–$012F` do ekranu tytułowego (`$2883`).

RC3 przeniosło `AIM_TOGGLE` i `P1_REDRAW` na `$011D/$011E` (RC2 umieściło `SHIELD`/`SCORE_NEW` na
`$0126–$0128`), zakładając, że pisze tam tylko kod resetu. W efekcie w kolumnach 10–11 wiersza 4, tuż za
wynikiem P1, wyświetlał się licznik naprzemiennego celowania nurkowań (zmienia się przy każdym nurkowaniu)
i `0` (`P1_REDRAW`). **Czerwone znaki**: w tej palecie HUD litery mają kolor 1 (czerwony), cyfry kolor 2
(biały); wartości licznika trafiały na kafle liter (`$17` = G) i symboli (`$2C` = kropka), stąd „G” i „.”
między białymi cyframi, a za nimi `0`. Na ekranie tytułowym po GAME OVER pojawiały się wartości tarcz
(`$F0`). **RAM wyników nie był uszkodzony** – wyniki, hi-score, progi Extra Life i Weapon Boost liczone
z RAM były zawsze poprawne; błędne było tylko renderowanie sąsiednich komórek. Komunikat Life Sharing,
wysoki wynik, kolejka VRAM ani przepełnienie pola nie były przyczyną (sprawdzone testami poniżej).

**Odtworzenie.** Nowe testy na ROM-ie RC3 oblewają dokładnie tak jak zdjęcia: `HUD row 4 … (10, '0x2'),
(11, '0x0')` przy wyniku 2130 (ekran „2130 20”) oraz kafle `$F0 $F0 $00` na ekranie tytułowym; na RC4
przechodzą.

**Naprawa.** Pięć zmiennych przeniesione do `$0350–$0354` – wypełnienia `$FF` (`$0347–$037F`) w bloku
kopiowanym przy resecie z CHR, między tabelą wskaźników tekstów a pierwszym tekstem (nic tam nie wskazuje
i nic tego nie czyta – audyt). Build sprawdza teraz każdą nową zmienną także z `src/original_ram.txt`
(RAM używany przez oryginał w czasie działania, z tracera) i ze stosem.

### R4.3 Pociski P2 (punkt 4)

**Nie odtworzyłem błędu w RC3** ani w cynes, ani w FCEUmm. Sprawdziłem każdy z ~2 600 strzałów W2–W4
(oba emulatory, statki w ruchu): X statku przy naciśnięciu, wybrany slot, `BUL_X`, X w OAM w kolejnych
klatkach i piksele. Zero anomalii; ten sam detektor na RC2 daje ~3 000 anomalii (stary błąd `$23/$24`).
Hipoteza limitu 8 sprite'ów na linię: oba emulatory go emulują, ale w naturalnej grze (W1 i W4, 6 000
klatek) żaden pocisk nie zniknął. Znalazłem i naprawiłem dwa realne przesunięcia, które mogą tłumaczyć
obserwację:
1. **Laser W4 był 1 px na lewo** od środka statku i od X używanego w kolizjach (kafel `$60` miał środek
   w kolumnie 3, pocisk `$30` – w 4). Nowy kafel lasera ma środek w kolumnie 4 i 3 px szerokości.
2. **Strzał startował z pozycji statku sprzed ruchu w tej klatce** (u obu pilotów): przy ruchu pocisk
   odstawał 1–2 px od rysowanego statku. Strzał (`FireShot`) przeniesiony do `CoopMid`, po ruchu obu
   statków.

Testy: cynes – każdy slot, W1 i W4, krawędzie i środek: `BUL_X+4` = środek widocznej sylwetki statku,
obraz pocisku symetryczny wokół niego; FCEUmm – 3 600 klatek ruchu i strzelania na W1–W4: każdy nowy strzał
każdego slotu startuje z X statku, X nie zmienia się w locie (RAM i OAM), piksele zgodne. Jedyny wyjątek
w danych: strzał oddany w klatce zakończenia etapu – statki są wtedy przestawiane na pozycje startowe,
a pocisk leci z miejsca, w którym statek był.

### R4.4 Darmowe W2 po Stage 1 (punkt 5)

**Nie znalazłem przypadku, w którym żyjący pilot nie dostaje W2.** Prześledziłem sekwencję
`E937` → `FA52` → `FC1A` → `FC38` (`StageCleared`) → podetapy 4–7 → Stage 2. Oryginał nie ustawia
chwilowo flag pilota przy przejściu: `$4F` = `$21` tylko na starcie gry, w podetapach 4–7 bez śmierci
`$4F` = 0, a W nie zmienia się w trakcie przejścia (sprawdzane w każdej klatce). W 45 naturalnych
ukończeniach Stage 1 (bot steruje oboma statkami, pociski zestrzeliwują formację): obaj w grze → W2/W2
zawsze; W2 omijało pilota wyłącznie wtedy, gdy w klatce `INC $59` eksplodował lub czekał na statek. Ważny
szczegół oryginału: po utracie statku P1 (`$4F` = `$22`) jego powrót czeka, aż wszyscy nurkujący wrócą
do formacji (`E937`), a w co-op P2 walczy dalej – P1 bywa „martwy” kilka sekund. Jeśli P2 wtedy dokończy
etap, P1 wraca dopiero w Stage 2 z W1. To prawdopodobnie widziany przypadek; zgodnie ze specyfikacją
(„pilot rzeczywiście martwy … nie otrzymuje bonusu”) zostawiłem tę regułę. **Zmiana po decyzji
użytkownika (RC4):** darmowe W2 dostaje także pilot trafiony tuż przed końcem etapu, który ma statek w
rezerwie (eksploduje lub czeka): `PilotComing` `$8632` (w grze, albo trafiony z `LIVES` > 0). Wraca już z
W2 (`W2_OWNED` = 1, stałe W2). Bez darmowego W2 zostaje pilot wyeliminowany oraz trafiony na ostatnim
statku. Boost za punkty (W1→W2 poza darmowym, W2→W3) nadal tylko dla pilota żywego i w grze.

### R4.5 Weapon Boost W1–W4 (punkt 6)

| Poziom | Pociski | Prędkość | Warunek (RC4) |
|---|---:|---:|---|
| W1 | 1 | 100 % | start; po śmierci, jeśli W2 nigdy nie odblokowane |
| W2 | 2 | 110 % | 2000 pkt progresji + ukończony etap; co-op: raz za Stage 1; **zachowywane po śmierci** |
| W3 | 3 | 120 % | **4000 pkt od otrzymania W2** + ukończony etap; nadwyżka nie przechodzi |
| W4 Overdrive | 4 | 160 % | W3 + 8000 pkt bez śmierci, raz na życie, **30 s**, potem W3 |

Zweryfikowane testami: 3999 → brak W3, 4000 → W3 tylko po ukończeniu etapu; 3500 na W1 → W2, licznik 0;
darmowe W2 przy 800 pkt i W3 przy łącznym 4800; śmierć z W2/W3/W4 → W2 (jeśli odblokowane), W1 (jeśli nie),
zerowanie progresji/no-death/Overdrive, potem znów 4000; Life Sharing ta sama reguła; W4 tylko raz na życie
mimo ≥ 8000 no-death; nowa gra czyści wszystko. Próg osiągnięty w ostatniej klatce przed końcem etapu się
liczy (punkty dodaje `E913` w tej samej klatce przed `FC1A`).

**Overdrive (W4)**: licznik sekund × 60 klatek (bez dzielenia przy wyświetlaniu), odliczany w `CoopPre`
tylko w podetapie 8 – pauza, READY/respawn i zmiana etapu nie zużywają czasu, zmiana etapu go nie odnawia;
zmierzone 1 800 klatek gry. Każdy pocisk pamięta poziom z chwili strzału (`BUL_LV`), więc lasery w locie
kończą lot jako lasery 160 %; nowe strzały są W3 (3 sloty), czwarty slot nie jest ponownie używany.
**×2**: `ScoreAdd` liczy punkty z tabel oryginału (`E80F`/`E821`), podwaja je, gdy trafił pocisk
(`BY_SHOT`) pilota na W4 (cyfry z przeniesieniem do tysięcy `$56`), dodaje raz przez `E841` i raz
wywołuje `AfterScore` (progresja, no-death, Extra Life, HUD). Zderzenie z wrogiem i bonus Life Sharing +200
nie są podwajane. Wynik ×2 trafia do hi-score i progów Extra Life (test: 6950 → 7010, +1 życie).
**Dźwięk**: aktywacja – wznoszące arpeggio B-dur na kanale trójkątnym (nieużywanym przez grę, więc nic
nie przerywa i nic go nie przerywa), raz na odblokowanie; strzał W4 – krótki „zap” na Pulse 2 (ten sam
kanał co oryginalny strzał; obwiednia i sweep sprzętowe, nic nie trzeba aktualizować, nie może się
zawiesić; dwaj piloci w tej samej klatce zapisują te same wartości). Muzyka (Pulse 1) bez zmian – test
porównuje zapisy z oryginałem.
**Agresja** (analiza systemu trudności: REVERSE_ENGINEERING.md §5 – tabela dla etapów 1, 2, 5, 10, 20;
trudność nasyca się od etapu 8): bez trwałej flagi – każdy hook sprawdza `W4_SEC` obu pilotów, więc
efekt kończy się z ostatnim Overdrive (bez Overdrive przebieg jest bajt w bajt identyczny – test). +25 %
prób ataku (dodatkowy krok liczników bez timera okrętu flagowego), samotne ataki nie czekają na okno okrętu
flagowego (limity slotów etapu bez zmian), nurkowanie ~14 % szybsze (+1 px raz na 8 px, nigdy przez linię
strzału ani strefę trafienia), cel nurkowań i pocisków przesunięty na pilota z W4 (3 z 4). Zmierzone
(90 s, ten sam stan, P2 w Overdrive): starty nurkowań +41 %, prędkość 1,00 → 1,14 px/kl., nurkowania
w stronę P2 26 % → 50 %, pociski w stronę P2 7 % → 49 %. Obrażenia i tarcze bez zmian. Przy okazji: laser
W4 mógł przelatywać przez nurkującego (sprawdzany co 2. klatkę, 12,8 px vs okno 13 px) – okno lasera
17 px, zgodnie z jego 4 px dłuższym sprite'em.

### R4.6 Kolory pocisków

Każdy kolor każdej palety sprite'ów był zajęty (statek P2 = paleta 0 cała, przeciwnicy = palety 1–3;
kolor 3 to wszędzie pomarańczowy `$27`). Najmniej widoczna zmiana: paleta 2 kolor 3 → żółty `$28`
(jeden bajt tabeli palet `$E1CF`, wczytywanej raz przy resecie; zmienia tylko kilka pikseli detali
fioletowych obcych w czasie nurkowania). P1: paleta 2 (żółty), P2: paleta 0 (pomarańczowy, jak nos jego
statku), na W1–W4, także w 1 PILOT. Pocisk i laser używają tylko koloru 3, laser zachowuje wydłużony
kształt (8 px, 3 px szerokości). Test palety: cała pamięć palety = oryginał poza tym jednym bajtem.

### R4.7 Licznik etapu i odliczanie (punkt 7)

Wiersz 2 nametable (linie 17–24) nie jest używany przez oryginał w grze (audyt zapisów VRAM); wiersz 0
dostaje co klatkę pusty wiersz z `E4C4`, wiersze 3–4 to HUD, a komunikaty przeniosłem do samego wiersza 1.
Wiersz 2 (co-op): `W4 30s` P1 (kolumny 2–7, nad `W`/`1UP`), **`STG 01`** (kolumny 13–18, nad
`HI-SCORE`), `W4 30s` P2 (kolumny 22–27, nad `2UP`; kolumny 28–29 mają paletę 1 dla ikony statku P2,
więc cyfry byłyby niebieskie). Pola są wpisywane przez kolejkę VRAM tylko przy zmianie wartości (sekundy,
etap) i tylko gdy zapis wierszy jest bezczynny; na starcie gry baner raz czyści cały wiersz 2. Format
pełny `STG 01` się mieści. Numer = `$59 + 1`, dwie cyfry, do 99, potem 01 (zawijanie oryginału po etapie
99). Małe „s” to nowy glif w kaflu tła `$36` (nieużywanym przez żadną nametable gry – skan). 1 PILOT:
oryginalne flagi etapu, bez `STG`. Drugi wiersz komunikatu „W4 RED LASER” zastąpiło odliczanie.

### R4.8 Zmienione procedury 6502 i adresy (punkt 8)

Hooki RC4: `$E1CF` (paleta), `$F45F` `AtkGate`, `$F48B` `SoloGate`, `$EE23` `BulletAimX`, `$FD17`
`SoundTick`; zmienione działanie hooków `$E833` (`ScoreAdd` ×2), `$E91F` (`CoopMid`: strzał po ruchu,
`DiveBoost`), `$E2E4` (`HudScores`: kopia 2 klatki po trafieniu, strumień HUD co 4. klatkę), `$EE4E`
(`AimDiver`). Nowe/zmienione procedury (adresy RC4, `build/Galaxian_Coop.mlb`): `ScoreAdd` `$8489`,
`ScoreDouble` `$84AC`, `AfterScore` `$84D5`, `ResetBoost` `$843B`, `PilotDown` `$845B`, `StageCleared`
`$85B5`, `PilotComing` `$8632`, `CheckW4` `$8652`, `W4Tick` `$868F`, `CoopMid` `$86B7`, `FireShot` `$831B`, `DiverHits`
`$829B`/`DiverHitsX` `$82E7`, `PreSplit` `$9E00` (poziom i paleta per slot, 1 171 cykli), `StatusRow`
`$8BEA`, `StatusField` `$8C53`, `BannerUpdate` `$8B84`, `SfxOverdrive` `$896E`, `SfxZap` `$8979`,
`SoundTick` `$8994`, `AtkGate` `$8A97`, `SoloGate` `$8AB1`, `DiveBoost` `$8ABE`, `BulletAimX` `$8B09`,
`AimDiver` `$8A2B`. Nowa pamięć: `$0350–$0370` (wypełnienie CHR), `$F5` (dźwięk). Pełna lista: MEMORY_MAP.md.

### R4.9 Audyt pamięci i PPU

Napisałem tracer 6502 (`tools/trace6502.py`) i skrypt audytu (`tests/ram_audit.py`): 8 × 100 000 klatek
(tytuł, demo, 1P, 2P, game over, ekran końcowy) rejestruje każdy odczyt/zapis RAM i VRAM z adresem
instrukcji. Wynik dla oryginału → `src/original_ram.txt`, sprawdzany przez build. Wnioski: konflikt
`$011D/$011E` i `$0126–$0128` (wyżej), wykorzystanie wiersza wyników i ekranu tytułowego, tabele per slot
nurkujących (luki w nich zostawiłem – późniejsze etapy mogą ich używać), stos (najgłębiej `$0133`, jak
RC3; oryginał `$013A`; reset przy S < `$30` grozi tylko przy zagnieżdżonym NMI, którego w pomiarach nie
było). **Błąd w samym audycie**: pierwsza wersja tracera zwracała 0 przy odczycie CHR przez `$2007`, przez
co kopie danych z CHR wyglądały na puste i `$0156–$01FF` (trzy melodie w RAM) uznałem za wolne; agent
analizujący dźwięk to wykrył przed jakimkolwiek wydaniem, tracer poprawiłem, audyt powtórzyłem, a test
`test_tune_ram_intact_in_play` pilnuje tego obszaru. Lista z tracera jest dowodem, nie gwarancją –
ścieżki, do których przebiegi nie dotarły (późne etapy), mogą używać więcej. Build sprawdza też, że bloki
nowego kodu się nie nakładają (`PreSplit` urósł i bez tej kontroli nachodził na `ScrollFix`).

### R4.10 Testy (punkt 9)

- **cynes: 82/82 OK** (było 61; +4 testy HUD z commitu poprawki, +17 testów RC4; 7 starszych zaktualizowanych
  pod zmienione reguły, żaden nie usunięty).
- **FCEUmm (stable-retro 1.0.1): 4/4 OK** (+1: początki strzałów, kolory, środek lasera, limit sprite'ów).
- **Tracer: 4/4 OK** (dźwięk aktywacji raz, zap vs zwykły strzał, równoczesny ogień, muzyka i RAM melodii
  bez zmian).
- Nie testowane: Mesen 2 (brak), RetroArch, sprzęt. **RC4 nie jest zaakceptowane przed
  testem manualnym użytkownika na emulatorze.**

### R4.11 Wydajność (punkt 10)

| Scenariusz | Najgorsza klatka (iteracje bezczynności ≈ 10 cykli) |
|---|---|
| 1 PILOT, 4 × 2 min | 546 (RC3 596, oryginał 349) |
| co-op W1, 4 × 2 min | 477 (RC3 494) |
| obaj w Overdrive (W4 + agresja), ogień, 24 × 3 min | **100** (~1 000 cykli), 0 resetów, 0 klatek opóźnienia |
| to samo z tarczami, 24 × 3 min | **74** (~740 cykli), 0 resetów, 0 klatek opóźnienia |

Metoda RC3 (poprawiony odczyt `$3A/$3B` z PC przerwania). Agresja daje znacznie gęstsze klatki niż test
RC3 (7 nurkujących, start grupy okrętu flagowego, 8 laserów, 6–7 pocisków wroga), więc liczby RC3 (116 /
127 bez agresji) nie są tym samym testem. Pierwsza wersja RC4 miała w takiej klatce tylko 12 iteracji;
profilowanie najcięższych zapisanych klatek (warianty ROM z wyłączanymi procedurami) i zmiany: strumień
HUD co 4. klatkę (całość na ekranie w ≤ 8 klatek), kopia wyniku 2 klatki po trafieniu, szybsza pętla
trafień w nurkujących (23 zamiast 30 cykli), przyspieszenie nurkowania jednym slotem na klatkę, wiersz
statusu co 4. klatkę – na tych samych 16 klatkach najgorsza z 14 do 54. Podział rastra: `PreSplit` 1 171
cykli, podział 37 cykli później niż w oryginale (< 1 linia), test sprawdza, że jest między formacją
a statkiem. OAM: bez dodatkowych sprite'ów.

### R4.12 Commity (od najstarszego)

1. `309bdfc Fix score HUD corruption` – przeniesienie zmiennych z wiersza wyników, kontrola buildu
   z listą RAM oryginału, tracer i skrypt audytu, poprawiony helper nametable, 4 testy HUD/tytułu.
2. `d925e73 Add overdrive power-up` – cały kod RC4: W3 za 4000, trwałe W2, Overdrive (30 s, ×2, dźwięki,
   agresja), kolory i wyśrodkowanie pocisków, strzał po ruchu, okno trafienia lasera, wiersz statusu
   (`STG`, odliczanie), oszczędności CPU, kontrola nakładania bloków kodu.
3. `bf500a8 Add RC4 regression tests` – 17 nowych testów cynes, 1 FCEUmm, 4 tracera; aktualizacja 7
   starszych testów pod zmienione reguły.
4. `Update RC4 docs` – README, CHANGELOG, TESTING, MEMORY_MAP, REVERSE_ENGINEERING, ten raport, łatka BPS.

Kod RC4 jest w jednym commicie: zmiany w `coop.asm` są od siebie zależne (wspólne zmienne, `PreSplit`,
`ScoreAdd`, HUD), a stany pośrednie nie byłyby osobno budowane ani testowane. Bez `Co-authored-by`, bez
merge do `main`, bez remote/push.

### R4.13 Ograniczenia i otwarte kwestie

- Błędu startu pocisków P2 i błędu W2 nie odtworzyłem (R4.3, R4.4) – proszę o potwierdzenie w teście manualnym,
  a jeśli wystąpią: krótki film lub opis sytuacji (który slot, ruch, etap, czy pilot ginął).
- Detale fioletowych obcych w nurkowaniu: kilka pikseli żółtych zamiast pomarańczowych (koszt koloru P1).
- HUD odświeża się w ≤ 8 klatek (zmiana wartości ≤ 12 klatek, ~0,2 s) zamiast 1–2.
- Pocisk wroga celuje w P1 (oryginał), chyba że tylko P2 ma Overdrive (3 z 4 pocisków w P2) albo P1 jest
  poza grą.
- Zapas CPU w najgorszej klatce z agresją: ~740 cykli (z tarczami) – mniej niż w RC3 bez agresji.
- Zagnieżdżone NMI przy bardzo głębokim stosie zresetowałoby grę (sprawdzenie oryginału w `E212` przed
  `NmiGuard`); w pomiarach 0 klatek opóźnienia.
- Mesen 2, RetroArch, manual test setup i sprzęt nie testowane przez autora.

## R3. RC3

### R3.1 Pliki

| Plik | Ścieżka | SHA-256 |
|---|---|---|
| ROM RC3 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.nes` (40 976 B) | `aa33c6b037254a197cf78a29510db75391c6a95f151b2dcf99c9ea9c5a851e8d` |
| Etykiety Mesen 2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.mlb` | – |
| Łatka BPS (w git) | `games/galaxian-coop/patches/Galaxian_Coop.bps` (3 891 B) | odtwarza ROM RC3 bajt w bajt (sprawdzone) |

Nowy kod 3 704 B; 38 hooków, 143 bajty oryginału (nowy hook `E2E4`).

### R3.2 BUG – „P1 strzela zza ekranu”

**Przyczyna.** P1 nie tworzył żadnych pocisków – w RAM (`BUL_Y`) nie było ich ani w czasie eksplozji,
READY, oczekiwania, ani przy X0, i nie zdobywał punktów. Problem był wyłącznie w OAM:
1. Oryginalne procedury trafień (`F381` formacja, `F2D1/F2EF/F31E` nurkowie) czytają „pocisk” z
   `$0280/$0283` – to sprite oryginalnego pocisku P1, u nas slot 0 pocisków P1. `BulletOwnerSlot`
   (`$821D`) kopiuje tam pozycję każdego sprawdzanego pocisku, także P2. Po trafieniu pociskiem P2 nikt
   tego nie przywracał: `PreSplit` narysował slot wcześniej w tej klatce, a w klatce z trafieniem rysowanie
   gotowych pocisków jest pomijane. Przez jedną klatkę widać było „pocisk P1” w miejscu trafienia P2 –
   przy martwym lub wyeliminowanym P1 wyglądało to jak strzał P1 spoza ekranu (pomiar: przy X0 i P2
   walczącym ~1 taka klatka na 140, zawsze w klatce trafienia P2).
2. Rzadziej: w klatce śmierci `PilotDown` zerował pociski w RAM, ale ich sprite'y narysowane wcześniej
   w tej klatce zostawały na ekranie przez jeszcze jedną klatkę (dotyczyło P1 i P2).
Pociski wrogów i ich przypisanie nie miały udziału (sprawdzone skanem OAM).

**Naprawa.** `BulletHitDone` (`$8235`) po każdej oryginalnej procedurze trafienia odtwarza `$0280/$0283`
jako slot 0 P1 (pozycja jego pocisku albo ukryty). `PilotDown` (`$8400`, `PilotDownShot` `$8420`) od razu
ukrywa sprite'y usuwanych pocisków. Skan 2 × 3000 klatek (P1 X0 i obaj żywi): 0 klatek ze sprite'em
pocisku bez pocisku w RAM (poza prawdziwym pociskiem w ostatniej klatce lotu przy górnej krawędzi).

### R3.3 BUG – parytet broni P1/P2

**Przyczyna znaleziona przy pomiarze.** `BUL_X` zajmował `$1E–$25`. Procedura padów oryginału
(`E580–E59C`, co klatkę) zapisuje surowy bajt `$4016` do `$23` i zlicza zmiany bitu 2 w `$24` (ukryta
funkcja z mikrofonem Famicoma: 4 zmiany przy liczniku resetów `$0115` = 10 → skok do resetu `E23A`). Skutki:
X 2. pocisku P2 był co klatkę nadpisywany (~64 – pocisk leciał z lewej strony ekranu i trafiał tam
wrogów), X 3. pocisku P2 rósł; wartość X w `$24` mogła też spełnić warunek tego resetu. P1 nie był
dotknięty – stąd wrażenie różnej broni P1/P2 przy W2–W4. Prędkość, opóźnienie FIRE i limity były
identyczne. Moja kontrola RAM w buildzie sprawdzała dotąd tylko kolizje między nowymi zmiennymi.

**Naprawa.** `BUL_X` → `$0E–$15` (strona zerowa, `PreSplit` bez zmian w czasie – sprawdzone pikselowo).
Zmienne z `$0E–$15`: `CUR_SLOT`, `CUR_PL`, `T0`, `T1` → `$1E–$21`, `TITLE_STEP` → `$22`, `P1_GRANTED` → `$25`,
`AIM_TOGGLE` → `$011D`, `P1_REDRAW` → `$011E` (luka strony 1, którą oryginał zapisuje tylko przy resecie).
`build.py` odrzuca teraz każdą zmienną na jednym ze 115 adresów strony zerowej używanych bezpośrednio przez
oryginał (`ORIGINAL_ZP`); inne kolizje z oryginałem nie istnieją.

**Pomiary P1 vs P2** (oba statki na tej samej wysokości, bez wrogów; cynes, potwierdzone w FCEUmm):

| Poziom | Pilot | FIRE → pocisk | Y w kolejnych klatkach | px/klatkę | Pełny lot | Maks. pocisków | 6 szybkich naciśnięć |
|---|---|---|---|---|---|---|---|
| W1 | P1 / P2 | 2 kl. / 2 kl. | 200, 196, 192, 188, 184 | 4,000 | 50 kl. | 1 | 1 strzał |
| W2 | P1 / P2 | 2 / 2 | 200, 196, 192, 187, 183 | 4,378 | 46 | 2 | 2 |
| W3 | P1 / P2 | 2 / 2 | 200, 196, 191, 186, 181 | 4,780 | 42 | 3 | 3 |
| W4 | P1 / P2 | 2 / 2 | 200, 194, 188, 181, 175 | 6,387 | 32 | 4 | 4 |

Wartości P1 i P2 identyczne w każdej kolumnie (przed poprawką W4 P2: 5 strzałów z 6 naciśnięć, bo
pocisk z błędnym X trafiał wroga i zwalniał slot). 100/110/120/160 % – zgodnie ze specyfikacją
(4,00/4,40/4,80/6,40 w stałym przecinku 8.8; pomiar z całego lotu zaokrągla start i koniec). Strzał w 2.
klatce naciśnięcia dla obu (reguła oryginału). Trzymanie FIRE = 1 strzał; pełna pula blokuje kolejne;
po śmierci i respawnie W1 – testy w R3.5.

### R3.4 Wydajność

**Sprostowanie.** Licznik bezczynności `$3A/$3B` jest zwiększany dwiema instrukcjami. Jeśli NMI przerwie
pętlę między `INC $3A` (przejście na 0) a `INC $3B`, odczyt jest o 256 za mały, a następny o 256 za
duży. Moje skrypty tego nie uwzględniały: „1 iteracja” w RC2 i „15” w RC1 to artefakty (te same klatki
RC2 odczytane poprawnie: 257–332). Prawdziwa najgorsza klatka W4 w RC2: 67 iteracji (~670 cykli), z
tarczami 92. Raport RC2 przedstawiał więc sytuację znacznie gorzej, niż była – zapas nigdy nie był
„około 10 cykli”. Poprawiony pomiar odczytuje przerwany PC (stan cynes / ramka NMI na stosie); używają go
skrypty i oba testy obciążeniowe.

**Analiza** (15 najcięższych klatek W4, zapisane stany, odtwarzanie deterministyczne): wszystkie z pełną
kolejką VRAM, 3–5 nurkami i 7–8 pociskami, bez trafienia. Koszty (wyłączanie procedur): oryginał –
nurkowie `E9B1` ~2950 cykli, start ataku `F415` do ~3800, tablice ruchu `E460` ~1700, HUD i hi-score
`E2FE` ~820 (w tym ~350 na kopię wyników i porównanie hi-score w każdej klatce), `EF09` ~480, pociski wrogów
~430; nasze – silnik pocisków ~1400, gotowe pociski ~300, przechył nurków ~250, `FireShot` ~150, `P2Draw`
~130, komunikaty ~90, tarcze ~70+50.

**Optymalizacja (bez zmiany mechaniki i obrazu).** `HudScores` (`$8856`, hook `E2E4`): kopia wyników i
porównanie hi-score z `E2FE` tylko w klatce z punktami i następnej (oryginał pokazuje nowy hi-score
z jednoklatkowym opóźnieniem) oraz po nowym hi-score P2; strumień HUD do VRAM (`E342`) co klatkę jak
dotąd. Flaga `SCORE_NEW` (`$0128`) ustawiana w `AfterScore` (wszystkie punkty, także premia Life Sharing),
`CoopInit` i `CoopHiScore`. Szybkie wyjście `ShieldTick` bez aktywnych tarcz. Wynik na tych samych 15
klatkach: najgorsza 78 → 115 iteracji, średnia 172 → 207. Test sprawdza na ekranie, że wyniki i hi-score
(P1 i P2) dalej się aktualizują. Podział rastra – identyczny (linie 0–120, co-op, 8 laserów, 1P).

**Wynik RC3** (24 sesje × 3 min W4 i 24 z tarczami): najgorsza klatka **116 iteracji (~1160 cykli)**,
z tarczami **127 (~1270)**; 0 resetów, 0 klatek opóźnienia. Zwykła gra: oryginał 349, RC3 1P 596, co-op
494. Cel 150–300 cykli jest spełniony z dużym zapasem; nie zmniejszałem liczby testów kolizji ani
częstotliwości logiki. Limit klatek opóźnienia (`NmiGuard`, 8) bez zmian.

**Zmiana budżetu względem RC2** (poprawiony pomiar): W4 67 → 116 iteracji, z tarczami 92 → 127.

### R3.5 Testy RC3

- cynes: **61/61 OK** – 56 wcześniejszych + `test_p1_death_no_ghost_shots`, `test_p2_death_no_ghost_shots`
  (pełna sekwencja śmierci przez trafienie pociskiem wroga, X2→X1 i X1→X0, eksplozja, READY, X0,
  ożywienie, W1 + tarcza, trzymany FIRE), `test_weapon_parity`, `test_w4_with_shields_stable`,
  `test_hud_scores_follow_points`. Testy obciążeniowe korzystają z poprawionego licznika.
- FCEUmm (stable-retro): **3/3 OK** (`tests/test_fceumm.py`): FIRE i parytet W1–W4, śmierć P1 i P2 bez
  duchów, tarcza. Uruchomione na kodzie RC2 – wszystkie trzy oblewają (duchy P1 i P2, dwa różne X
  pocisków P2), więc wykrywają zgłoszone błędy.
- Nowe testy RC3 w cynes na kodzie RC2 też oblewają w tych samych miejscach.
- Mesen 2 nie jest zainstalowany – nie testowano. RetroArch, sprzęt – nie testowano
  (FCEUmm w stable-retro to nie to samo co RetroArch). RC3 nie jest zaakceptowane przed testem manualnym.

### R3.6 Zmienione procedury RC3

| Procedura | Adres | Zmiana |
|---|---|---|
| `BulletHitDone` | `$8235` | odtwarza `$0280/$0283` (slot 0 P1) |
| `PilotDown`, `PilotDownShot` | `$8400`, `$8420` | ukrywa sprite'y pocisków przy śmierci |
| `HudScores` | `$8856` | nowa, hook `E2E4` |
| `AfterScore`, `CoopInit`, `CoopHiScore` | `$843B`, `$800C`, `$8C44` | ustawiają `SCORE_NEW` |
| `ShieldTick` | `$80C5` | szybkie wyjście |
| zmienne strony zerowej | – | `BUL_X` `$0E–$15`, przesunięte `CUR_SLOT`…`P1_GRANTED`, `AIM_TOGGLE`/`P1_REDRAW` na stronie 1 |
| `build.py` | – | kontrola `ORIGINAL_ZP` |

### R3.7 Commity RC3

`Fix P1 ghost shooting`, `Verify weapon parity`, `Optimize frame budget`, `Add RC3 tests`,
`Add FCEUmm checks`, oraz commit dokumentacji RC3.

### R3.8 Ograniczenia

- Pocisk w ostatniej klatce lotu jest rysowany przy samej górnej krawędzi (Y=0) – prawdziwy pocisk, jak w
  RC2.
- Strumień HUD oryginału zapełnia kolejkę VRAM w każdej klatce; zostawiony bez zmian, bo jego
  ograniczenie zmieniłoby tempo odświeżania HUD.
- Pozostałe ograniczenia RC2 (0.9) i RC1 (8) bez zmian.

## 0. RC2

### 0.1 Pliki

| Plik | Ścieżka | SHA-256 |
|---|---|---|
| ROM RC2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.nes` (40 976 B) | `14fd826686e2aebf6151637683f6d43cef2e54d3739b8ccaea9c2768d2595538` |
| Etykiety Mesen 2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.mlb` | – |
| Łatka BPS (w git) | `games/galaxian-coop/patches/Galaxian_Coop.bps` (3 804 B) | odtwarza ROM RC2 bajt w bajt (sprawdzone) |

Nowy kod: 3 625 B; 37 hooków, 140 bajtów oryginału zmienionych (RC1: 135 – hook `EEC0` urósł z 2 do 7 B).

### 0.2 Wyniki testów RC1 użytkownika (test manualny na emulatorze)

PASS: ekran tytułowy, ukośne logo CO-OP z animacją, credits; brak białych kresek i zera u góry; tryb dwóch
graczy z dwoma padami i osobnymi pozycjami; Life Sharing przy X0 z premią +200. Wykryte błędy 1–3 poniżej.

### 0.3 Rzeczywiste przyczyny błędów

**BUG 1 – „automatyczne” strzelanie.** Strzał używał reguły oryginału `E5A8`: licznik = 3 przy puszczonym
przycisku, przy trzymanym zmniejszany co klatkę, strzał przy 0. Licznik nie zatrzymywał się na 0, tylko
przechodził na `$FF` i odliczał dalej – trzymany FIRE strzelał ponownie co 256 klatek (~4,3 s; pomiar:
strzały w klatkach 2, 258, 514). W oryginale przy jednym pocisku było to prawie niewidoczne; z 2–4 slotami
kolejne strzały wychodziły same. Dodatkowo `FireShot` przy zajętych wszystkich slotach wychodził przed
aktualizacją licznika, więc puszczenie przycisku w tym czasie było gubione, a stan licznika zależał od
zajętości slotów. Prędkości, punktacja i kolizje nie miały tu udziału.
*Poprawka* (`FireShot` `$82D0`): licznik aktualizowany co klatkę niezależnie od slotów i stanu pilota; po
puszczeniu = 2 (zachowany czas oryginału: strzał w 2. klatce naciśnięcia), przy 0 zatrzymany
(naciśnięcie zużyte) aż do puszczenia. Naciśnięcie przy pełnej puli albo gdy pilot nie może strzelać
również zostaje zużyte. `FireRearm` (`$83D9`) przy powrocie statku zeruje licznik, jeśli FIRE jest trzymany
(sekwencja READY P1 nie wywołuje `FireShot`). Osobny licznik dla każdego pada (`FIRE_CNT` `$0B/$0C`).

**BUG 2 – W2 i strzały po śmierci.** Sprawdzone przyczyny z listy:
- reset poziomu przy śmierci działał (`SetP1Dead`/`P2Kill` → `ResetBoost`), współdzielenia stanu P1/P2
  ani złego właściciela pocisku nie było;
  - **pociski martwego pilota nie były usuwane** – leciały dalej i mogły punktować, dodając punkty boostu
    i no-death już po wyzerowaniu;
  - **pilot trafiony tuż przed końcem etapu dostawał darmowe W2** (patrz BUG 3) i wracał z respawnu już na
    W2 – to daje obraz „W2 po śmierci”;
  - trzymany FIRE przy respawnie: P2 dostawał licznik 3 (uzbrojony), więc trzymany przycisk strzelał 2 klatki
    po powrocie.
  *Poprawka*: wspólna procedura `PilotDown` (`$83E3`) dla śmierci i ożywienia: W1, punkty boostu i no-death
  = 0, usunięcie 4 pocisków pilota (wolne sloty `PreSplit` ukrywa), tarcza w co-op. Drugi pilot nietknięty.
  Przy okazji: hook `E611` (`SetP1Dead`) gubił rejestr X, przez co oryginał usuwał pocisk wroga nr 0 zamiast
  tego, który trafił – teraz X i Y są zachowane.

**BUG 3 – W2 po Stage 1 tylko dla jednego pilota.** Pętla w `StageCleared` obsługiwała obu pilotów
(X=1, potem 0), flaga jednorazowa była ustawiana po pętli, `$53` nie grał roli, HUD pokazywał poprawne
wartości, a nic później nie nadpisywało poziomu. Przyczyna: warunek „pilot w grze” (`PilotInGame`)
sprawdzał tylko, czy pilot nie odpadł, a nie czy żyje. Koniec etapu przychodzi ścieżką `E94D`
(`LDA $9F / ORA $4F`) → `FA52` → `FC1A` → `FC38`, tą samą co utrata statku P1, więc w tej chwili pilot
często eksploduje albo czeka na statek. Symulacja 16 naturalnie ukończonych etapów 1: w 8 jeden z pilotów
był wtedy trafiony i mimo to dostawał W2. Twojej konkretnej rozgrywki nie da się odtworzyć; najbardziej
prawdopodobne wyjaśnienie obserwacji to taki moment (albo śmierć jednego z pilotów tuż po starcie Stage 2,
która poprawnie zeruje jego W2). Logika przyznawania jest teraz jednoznaczna i pokryta testem. *Poprawka*: `PilotAlive` (`$8546`) – boost tylko dla pilota żywego i w grze;
obaj obsłużeni w jednej pętli przed ustawieniem flagi; brak przyznania wstecz po respawnie/ożywieniu;
1P bez zmian (próg 2000).

### 0.4 Respawn Shield (tylko co-op)

- `SHIELD` `$0126/$0127` (P1/P2; wolna luka między hi-score a wynikiem P2, zapisywana tylko przy resecie).
  - Ustawiany na 240 w `PilotDown` (śmierć i ożywienie odbiorcy), 0 przy nowej grze. Dawca, start gry i start
    etapu bez śmierci – bez tarczy. 1P – bez tarczy.
  - `ShieldTick` (`$80BE`, z `CoopPre`, raz na klatkę logiki) odlicza tylko, gdy statek jest w grze – czas
    liczy się od powrotu statku; pauza go zatrzymuje; przeciążenie CPU go nie skraca (liczy klatki logiki).
    240 klatek = 4,00 s przy 60 Hz, 3,99 s przy NTSC 60,0988 Hz.
  - Kolizje: P1 – tarcza w `P1_BLOCK`, który czytają tylko dwa testy trafień oryginału (`E5DF` pociski,
    `EC59` nurkowie); ruch (`P1MoveGate`, hook `EEC0`), strzał (`CanFire`) i celowanie nurków (`AimDiver`)
    sprawdzają tylko „trafiony / poza grą”. P2 – `P2Alive` pomija `P2VsBullets` i `P2VsDivers`. Wszystkie
    ścieżki śmierci (`E611`, `EC8F`, `P2Kill`) leżą za tymi testami. Punkty, wrogowie i drugi pilot bez zmian.
  - Miganie: 8 klatek widoczny / 8 ukryty, ostatnia sekunda 4/4; ostatnia faza ukryta, więc statek jest stale
    widoczny dokładnie od klatki końca ochrony. P2 – sprite'y ukryte w `P2Draw`. P1 to tło: `P1Blink`
    (`$80EB`) zaraz po podziale rastra statku zapisuje `$2001` = `$16` (tło wyłączone, sprite'y włączone),
    a `E280` przywraca `$1E` na początku następnej klatki. Poniżej podziału w czasie gry jest tylko statek
    P1, więc nic innego nie znika. Bez zapisów do nametable/OAM, bez dodatkowych sprite'ów, oba podziały
    rastra w niezmienionym czasie.

### 0.5 Zmienione i nowe procedury RC2

| Procedura | Adres | Zmiana |
|---|---|---|
| `FireShot` | `$82D0` | nowa reguła strzału (BUG 1) |
| `FireRearm` | `$83D9` | nowa; wywoływana przy respawnie P1 (`P1ShipRedraw` `$804C`, hook `FC17`), P2 (`P2Waiting` `$8599`) i przy ożywieniu |
| `CanFire` | `$8315` | P1: `P1_DEAD | P1_OUT` zamiast `P1_BLOCK` |
| `PilotDown` | `$83E3` | nowa: reset broni, usunięcie pocisków, tarcza |
| `SetP1Dead` | `$806F` | `PilotDown`, zachowuje X/Y |
| `P2Kill`, `GiveFromP1`, `GiveFromP2` | `$85F0`, `$875E`, `$879A` | `PilotDown` (+ `FireRearm` dla odbiorcy) |
| `StageCleared`, `PilotAlive` | `$84E3`, `$8546` | boost tylko dla żywych (BUG 3); `PilotInGame` usunięta |
| `CoopPre`, `ShieldTick` | `$8087`, `$80BE` | odliczanie tarczy, tarcza P1 w `P1_BLOCK` |
| `P1MoveGate` | `$8107` | nowa; hook `EEC0` (7 B: `LDA $4F / BNE / JSR EED6`) |
| `AimDiver` | `$8867` | tarcza nie zmienia celu nurków |
| `P2Alive`, `P2Draw` | `$85C0`, `$8C39` | tarcza P2: brak kolizji, miganie |
| `ShieldHidden`, `P1Blink`, `CoopPost` | `$80D1`, `$80EB`, `$8899` | faza migania, miganie P1 |
| `ResetPilots` | `$8398` | `FIRE_CNT` = 0, `SHIELD` = 0 na start gry |

### 0.6 Testy RC2

- Automatyczne (cynes): **56/56 OK** – 45 testów RC1 bez zmian + 3 testy broni RC2 + 8 testów tarczy
  (lista w TESTING.md). Pokrywają punkty 1–19 listy tarczy i całą listę FIRE / śmierć / Stage 1;
  punkt 20 (brak regresji) to pełny zestaw 45 wcześniejszych testów.
  - Pomiary: symulacja 16 naturalnych ukończeń Stage 1 przed i po poprawce; wzory migania P1/P2 klatka po
    klatce; zapas CPU (0.7).
  - **Nie testowano poza cynes** (Mesen 2, RetroArch, sprzęt). RC2 nie jest zaakceptowane
    do czasu testów manualnych użytkownika na emulatorze. Lista kontrolna RC2 w TESTING.md.

### 0.7 Zapas CPU (RC2) – NIEAKTUALNE, patrz R3.4 (artefakt pomiaru)

- Zwykła gra (4 × 2 min losowego wejścia), najgorsza klatka: co-op 327 iteracji (RC1: 329), 1 PILOT 459.
  - Stress W4 (obaj na W4, ciągły ogień, 24 sesje × 3 min): **0 resetów, 0 klatek opóźnienia**, najgorsza klatka 1 iteracja zapasu (~10 cykli), najgorsze wartości sesji 1–242.
  - To samo z obiema tarczami stale aktywnymi (miganie co klatkę): **0 resetów, 0 klatek opóźnienia**, najgorsza klatka 3 iteracje (~30 cykli), sesje 3–185.
- Zapas w najcięższych klatkach W4 jest mniejszy niż w RC1 (15 iteracji): klatka jest wykorzystana prawie
  do końca. `NmiGuard` (klatka opóźnienia zamiast resetu) nie zadziałał w żadnej z 48 sesji, ale to
  najsłabszy punkt wydajności; ewentualna dalsza optymalizacja – patrz rekomendacje.
  - Koszt tarczy na klatkę: `ShieldTick` ~20 cykli przy nieaktywnych tarczach; miganie kilkanaście cykli;
    przy aktywnej tarczy P2 odpadają jego testy kolizji (mniej pracy).

### 0.8 Commity RC2

`Fix fire input`, `Fix death weapon reset`, `Fix stage one boost`, `Add respawn shield`,
`Add shield blinking`, `Fix fire after respawn`, `Add weapon regression tests`, `Test respawn protection`,
oraz commit dokumentacji RC2.

### 0.9 Ograniczenia RC2

- Naciśnięcie FIRE musi trwać co najmniej 2 klatki (jak w oryginale); naciśnięcie przy pełnej puli
  pocisków jest zużyte – trzeba nacisnąć ponownie po zwolnieniu slotu.
  - Pilot trafiony w chwili ukończenia etapu nie dostaje darmowego W2 (zgodnie ze specyfikacją).
  - Tarcza P1 odlicza tylko w klatkach, w których działa logika gry (`E913`); w czasie sekwencji READY po
    śmierci P1 tarcza P2 stoi, tak jak cała rozgrywka.
  - Miganie P1 wyłącza tło poniżej podziału rastra statku. W czasie gry jest tam tylko statek P1; gdyby w
    przyszłości coś innego trafiło do tego obszaru tła, też by migało.
  - Pozostałe ograniczenia RC1 bez zmian (sekcja 8).

## 1. Podsumowanie (RC1)

Wszystkie punkty specyfikacji v1.0 są zaimplementowane w `src/asm/coop.asm` i pokryte testami
automatycznymi w emulatorze cynes (**45/45 OK**). Gra nie była testowana w Mesen 2, RetroArch,
w teście manualnym ani na sprzęcie – te testy zostają po stronie użytkownika (listy w TESTING.md).

| Plik | Ścieżka | SHA-256 |
|---|---|---|
| Oryginał (wejście, nie w git) | `games/galaxian-coop/private/Galaxian (Japan).nes` | `1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e` |
| ROM wynikowy (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.nes` (40 976 B) | `9e87f49b320547c96663e810196c87c78bfb714c040fa12596b8f33bced3ee5d` |
| Etykiety Mesen 2 (nie w git) | `games/galaxian-coop/build/Galaxian_Coop.mlb` | – |
| Łatka BPS (w git) | `games/galaxian-coop/patches/Galaxian_Coop.bps` (3 617 B) | odtwarza ROM bajt w bajt (sprawdzone) |

ROM: NES 2.0, mapper 0 (NROM-256), 32 KiB PRG + 8 KiB CHR. Nowy kod: 3 446 bajtów w `$8000–$9FFF`,
oryginalny program w `$E000–$FFFF` zmieniony tylko w 37 hookach (135 bajtów), każdy sprawdzany przy buildzie.

## 2. Zrealizowane funkcje

### Tryby
- **1 PILOT** – oryginalna gra + wspólne systemy: HUD `Xn`/`Wn`, boosty W1–W4, dodatkowe życia.
  - **2 PILOTS CO-OP** – dwa statki, dwa pady, osobne pociski z właścicielem, osobne wyniki, życia i kolizje;
    statki się przenikają; Game Over dopiero po odpadnięciu obu; hi-score z obu wyników.
  - Wspólna logika obu trybów: jedna procedura punktacji (`ScoreAdd`/`AfterScore`), jeden silnik pocisków
    (4 sloty na pilota), jeden HUD.

### Life Sharing (tylko co-op)
- Odbiorca: dokładnie `X0` i wyeliminowany; dawca: co najmniej `X2`.
  - Wyzwalacz: nowe naciśnięcie SELECT na padzie dawcy (zbocze z poprzedniego i bieżącego stanu pada),
    maksymalnie jeden transfer na naciśnięcie.
  - Dawca: −1 życie, +200 punktów przez wspólną procedurę punktacji (liczą się do boostu, no-death
    i dodatkowych żyć).
  - Odbiorca wraca z 1 życiem na W1, z wyzerowanym postępem, 24 px obok dawcy (dawca się nie przesuwa).
  - Nieaktywne w pauzie, na ekranie tytułowym, w Game Over i w 1P.
  - Komunikat `P2 SELECT TO REVIVE P1` / `P1 SELECT TO REVIVE P2`, albo `P1 OUT` / `P2 OUT`, gdy partner ma
    `X1`; znika po ożywieniu.

### Pozycje startowe (co-op)
P1 po lewej (`$E4`=`$F4`), P2 po prawej (`$0C`) od środka, bez nakładania. Dotyczy startu gry, każdego
nowego etapu i respawnu; ożywienie obok partnera. 1P bez zmian (środek).

### Weapon Boost W1–W4 (oba tryby, osobno dla każdego pilota)

| Poziom | Pociski | Prędkość (8.8) | Zmierzone | Warunek |
|---|---|---|---|---|
| W1 | 1 | 4,00 px/kl. | 100 % | start, po śmierci / ożywieniu |
| W2 | 2 | 4,40 | 109 % | 2000 pkt boostu + ukończony etap; co-op: raz w grze za pierwszy etap |
| W3 | 3 | 4,80 | 120 % | +5000 pkt boostu + ukończony etap |
| W4 „Red Laser” | 4 | 6,40 | 160 % | na W3, od razu przy `no_death_points` ≥ 8000 |

- Maksymalnie jeden poziom na etap, nadwyżka punktów nie przechodzi dalej.
  - Śmierć lub ożywienie: W1, punkty boostu i no-death = 0. Wynik, progi żyć i drugi pilot bez zmian.
  - Darmowe W2 w co-op dostają tylko piloci w grze, tylko raz (nie po śmierci).
  - Strzały wylatują kolejno (oryginalna reguła: jedno naciśnięcie = jeden strzał); do 8 pocisków naraz.
  - Przy 6,4 px/klatkę żadna kolizja nie jest pomijana: okna trafień mają 12–13 px.
  - W4: czerwone lasery (kafel `$60`, paleta sprite'ów 1). Komunikat `P1 GREAT SHOT` / `W4 RED LASER`
    (`P2 …`, `BOTH PILOTS GREAT SHOT`, w 1P `GREAT SHOT`) przez 120 klatek, tylko przy przejściu W3→W4,
    potem wiersze czyszczone.

### Dodatkowe życia
+1 co 7000 punktów (7000, 14000, …), osobno dla każdego pilota, od razu, każdy próg raz. Kilka progów
w jednej operacji – wszystkie. Śmierć nie zeruje progów, nowa gra tak. Działa w 1P. Limit 9 żyć
(jedna cyfra w HUD); zastępuje jednorazowy dodatkowy statek oryginału.

### HUD
Oba wyniki; dla każdego pilota ikona statku, `Xn` (wszystkie życia, łącznie ze statkiem w grze) i `Wn`.
W4 czerwone. Ikona P2 w kolorach P2. W 1P tylko P1.

### Ekran tytułowy
Logo `GALAXIAN` bez zmian; ukośna plakietka `CO-OP` (sprite'y) przy krawędzi logo, czerwona z krótkim
białym błyskiem (8 z 64 klatek). Menu `1 PILOT` / `2 PILOTS CO-OP`. Linia `HACK BY ZVGELO ©2026`
pod napisami Namco, które zostały.

## 3. Naprawione błędy

| Błąd | Przyczyna | Poprawka |
|---|---|---|
| Białe kreski w 1. linii (test manualny na emulatorze) | oryginał: scroll Y=`$FF`, linia 0 pokazuje tablicę atrybutów jako kafle | `ScrollFix`: Y=`$EF` + nametable `$2800` (pusty wiersz 29), czas wyrównany do 42 cykli |
| `0` w lewym górnym rogu | oryginał: wolne sprite'y na Y=0 z kaflem `$00` | `ClearOam`: pusty kafel `$10` |
| Niezgodne życia (2 vs 3) | HUD pokazywał zapas, odejmowany w różnych chwilach dla P1 i P2 | HUD = zapas + statek w grze, flaga `P1_GRANTED` |
| Reset gry przy przekroczeniu czasu NMI | watchdog oryginału (`E22F`) | `NmiGuard`: jedna klatka opóźnienia, reset dopiero po 8 z rzędu |
| `$07F0` (etap 1) | dane gry nadpisywane | hook usunięty, `$07F0` nieużywany, test regresji |

## 4. Architektura

- Cała logika gry działa w NMI (jak w oryginale). Hooki `JSR`/`JMP` w kodzie oryginału prowadzą do nowego
  kodu (pełna tabela w REVERSE_ENGINEERING.md §3, adresy procedur w §4 i w pliku `.mlb`).
  - P1 to tło przesuwane podziałem rastra; P2 to 4 sprite'y (połówki symetryczne, druga kopia odbita).
  - Kolizje używają procedur oryginału (`F381` formacja, `F31E` zestrzelenie nurka) z `$53` = właściciel,
    więc punktacja jest oryginalna. Testy `F381` wykonywane najpierw w kodzie inline.
  - RAM: tylko adresy, których oryginał nie używa (analiza statyczna + emulator); `build.py` sprawdza
    nakładanie się zmiennych. Mapa: MEMORY_MAP.md. OAM: P2 `$02A0`, pociski P1 `$0280/$02BC/$02C0/$02C4`,
    P2 `$02B0/$02B4/$02B8/$02C8`, 13 gwiazd od `$02CC`.
  - PPU/CHR: 2 kafle statku P2, kafel lasera, 2 komórki logo przekierowane na pusty kafel (obraz bez zmian,
    sprawdzone pikselowo); wiersze komunikatów 1–2 i HUD w `$2000`, wiersze tytułu 16/18/28 w `$2800`.

## 5. Wydajność

- Zwykła gra (4 sesje × 2 min, losowe wejście), najgorsza klatka – iteracje wolnej pętli (~10 cykli):
  oryginał **349**, 1 PILOT **350**, co-op W1 **329**. Zapas praktycznie jak w oryginale.
  - Optymalizacje (szczegóły w REVERSE_ENGINEERING.md §5): ruch i rysowanie pocisków w stałym czasie
    (939 cykli) wewnątrz pętli opóźniającej przed podziałem rastra, która jest skrócona o dokładnie tyle
    (22 × 42 cykle) – podział nie przesuwa się (linie 0–120 identyczne pikselowo); jedno trafienie na
    klatkę; sprawdzanie nurków co drugą klatkę na pocisk; kolizje statku P2 na zmianę; przechył nurków
    30 Hz; HUD co 4. klatkę; sprawdzanie progów życia tylko przy zmianie cyfry tysięcy; brak przerysowania
    gotowych pocisków w klatce z trafieniem.
  - Stress W4 (obaj piloci na W4, ciągły ogień, życia uzupełniane, 3 min na sesję, 24 sesje): **0 resetów, 0 klatek opóźnienia**, najgorsza klatka
    15 iteracji zapasu (~150 cykli; przed ostatnimi optymalizacjami 0). `NmiGuard` jest tylko siatką
    bezpieczeństwa – w pomiarach nie zadziałał ani razu.
  - Limity PPU: 64 sprite'y – 32 (nurkowie) + 7 (pociski wrogów) + 4 (P2) + 8 (pociski graczy)
    + 13 (gwiazdy) = 64; dlatego gwiazd jest 13 zamiast 24. Limit 8 sprite'ów na linię
    może powodować migotanie przy wielu nurkach obok P2 (jak w oryginale przy nurkach).

## 6. Testy

- **Automatyczne (wykonane)**: `tests/test_coop.py` – 45 testów (7 buildu, 38 emulatora), wynik 45/45 OK.
  Pokrycie: build/BPS, CHR, poprawki grafiki, tryby, co-op, Game Over, HUD żyć, 9 testów Life Sharing,
  tytuł i plakietka, 6 testów broni (progi 1999/2000 i 4999/5000, W4, reset po śmierci, darmowe W2,
  ożywienie na W1), 2 testy żyć, komunikaty, pozycje startowe, 2 testy obciążeniowe.
  - **Pomiary (wykonane, skrypty)**: zapas CPU, stress W4, prędkości pocisków, identyczność podziału rastra.
  - **Mario** (regresja po zmianach README): 14/14 OK; polecenia z README Mario uruchomione, hashe zgodne.
  - **README (wykonane)**: metody A (BPS) i B (build) uruchomione z katalogu repo, ten sam SHA-256;
    `git log --all --name-only` – żaden plik `.nes` nigdy nie był w git.
  - **Nie wykonane**: Mesen 2 (także import `.mlb`), RetroArch, handheld PC, sprzęt, dźwięk,
    dwa fizyczne pady, długie sesje gry przez człowieka. Wynik z cynes nie jest potwierdzeniem dla RetroArcha.

## 7. Commity (branch `game/galaxian-coop`, od najnowszego)

`Update tools list`, `Merge Mario docs`, `Add Galaxian build guide`, `Rename outputs, update BPS`,
`Add boost and banner tests`, `Add W4, banners, spawns, badge`, `Add weapon boost`, `Unify lives display`,
`Fix stray HUD tile`, `Add coop tests`, `Add title credits`, `Add life sharing`, `Improve lives HUD`,
`Fix top screen artifacts`, wcześniejsze: etap 2, asembler, BPS, testy, dokumentacja.
Branch `game/super-mario-coop`: `Document ROM patching`, `Add Mario build guide` (włączone do Galaxian
przez `Merge Mario docs`). `main` bez zmian.

Odstępstwo od planu commitów: część zmian z jednej sesji pracy (W4, komunikaty, pozycje, plakietka,
optymalizacje CPU, `NmiGuard`) trafiła do jednego commitu `Add W4, banners, spawns, badge`, bo powstawały
równolegle w tym samym pliku; nie przepisywałem historii, żeby je rozdzielić.

## 8. Ograniczenia i odstępstwa od specyfikacji

- Jedno trafienie pocisku na klatkę: drugie trafienie w tej samej klatce liczy się klatkę później.
  - Zapas CPU w skrajnym obciążeniu W4 jest mały (15 iteracji); gdyby go zabrakło, gra pokaże pojedynczą
    klatkę opóźnienia zamiast resetu (§5).
  - Gdy P1 traci statek, nowe ataki czekają na jego powrót (zachowanie oryginału); śmierć P2 nie wstrzymuje
    gry. W 1 PILOT brak nieśmiertelności po respawnie (jak w oryginale); w co-op od RC2 jest Respawn Shield.
  - 13 gwiazd zamiast 24; flagi etapów z HUD oryginału nie są widoczne w co-op (brak miejsca), w 1P są.
  - Komunikaty są czerwone (paleta HUD nie ma żółtego), brak znaku `!` w foncie.
  - Limit 9 żyć (jedna cyfra).
  - Plakietka `CO-OP` to sprite'y (nie zmienia CHR logo); jej „animacja” to subtelny błysk, nie ruch.

## 9. Rekomendacje

1. Test w Mesen 2 i manualny test na emulatorze według list z TESTING.md (szczególnie 1. linia ekranu w teście manualnym,
   dwa pady, W4 w obu statkach).
   2. W Mesen 2 obserwować `$067E` (`LAG_TOTAL`) w długiej grze na W4 – czy klatki opóźnienia się pojawiają.
   3. Po akceptacji: merge `game/galaxian-coop` → `main` (`--no-ff`), status w głównym README na „Completed”.
   4. Ewentualnie: żółta paleta komunikatów kosztem palety HUD.
5. RC2: zwiększyć zapas CPU w najcięższych klatkach W4 (obecnie 1–3 iteracje), np. przenosząc kolejne
   stałe koszty do `PreSplit` albo rzadziej sprawdzając kolizje nurków przy W4.
