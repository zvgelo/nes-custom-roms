# Galaxian Coop – raport z implementacji (RC3)

Data: 2026-10-18. Branch: `game/galaxian-coop` (bez merge do `main`, bez remote, bez push).
Wersja: **RC3** – strzały-duchy, parytet broni P1/P2, budżet CPU i sprostowanie pomiarów.
Sekcja R3 opisuje RC3, sekcja 0 – RC2, sekcje 1–9 – RC1 (specyfikacja v1.0). Starsze sekcje są nadal
aktualne poza miejscami poprawionymi w nowszych; **wszystkie liczby „najgorszej klatki” z RC1 i RC2 są
nieważne** (artefakt pomiaru, R3.4).
Autor moda: Zvgelo. Szczegóły techniczne: [REVERSE_ENGINEERING.md](REVERSE_ENGINEERING.md),
[MEMORY_MAP.md](MEMORY_MAP.md), testy i pomiary: [TESTING.md](TESTING.md).

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
