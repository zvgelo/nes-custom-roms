# Galaxian (Japan) – analiza procedur

Narzędzia: własny disassembler rekurencyjny (śledzi też tabele skoków dispatchera `$E44B`,
~3540 instrukcji, cały kod osiągalny z RESET/NMI), statyczny skan odwołań do RAM,
emulator cynes do testów dynamicznych (odczyt RAM/OAM, zrzuty ekranu, licznik bezczynności CPU).
Pewność: **P** potwierdzone kodem i emulatorem, **K** z kodu, **H** hipoteza.

## 1. Architektura i pętla główna

- **Reset `$E020`** (**P**): `SEI/CLD`, S=`$4D`, czeka na VBlank, zeruje `$00–$FF`, `$0200`, `$0600`, `$0700`;
  sprawdza sygnaturę w `$0105` (ciepły reset), kopiuje dane z CHR do RAM (`E0B8–E0FF`),
  czyści dwa nametable, wpisuje palety, włącza NMI i wchodzi w **pętlę główną `$E18B`**:
  `INC $3A / BEQ / JMP` – nic poza liczeniem. Cała gra działa w NMI.
- **NMI `$E20C`** (**P**):
  1. Kontrola poprawności: S ≥ `$30`, przerwany kod w `$E000+`, brak flag B/D, `$2A` = 0 –
     inaczej odczyt padów i miękki reset (`E22F`).
  2. `$4014` (OAM DMA ze strony 2), `E4AA`: zapis wiersza tekstu (26 B) i kolejki VRAM (16 × 2 B).
  3. Pętla opóźniająca `E286` → podział ekranu: `$2005` = −`$E5` (kołysanie formacji).
  4. `F038` gwiazdy (co drugą klatkę), `E54D` pady, pętla `E2A8` → drugi podział: `$2005` = −`$E4` (**statek P1**).
  5. `E373` logika (pauza lub dispatcher stanów `E3BF`), `E460` tablice ruchu, `F66D` wybór w menu,
     licznik klatek, `E2FE` HUD i hi-score, RNG, `RTI`.
- **Dispatcher `$E44B`** (**P**): `JSR $E44B` + tabela `.dw` za instrukcją; indeks w A.
  Tabele: `E3C6` (stany `$FF`), `E901` (pod-stany gry), `E9D0` (stany wrogów), `ED82`, `E427`, `F520`, `F6A8`, `F604`, `F992`, `FA75`.

Budżet CPU (licznik `$3A`): w grze min. ~330 iteracji pętli głównej na klatkę (~3300 cykli wolnych) w oryginale,
~286 w Coop przy dwóch graczach (**P**, test obciążeniowy).

## 2. Kontrolery – `$E54D` (**P**)

Strobe `$4016`, zapamiętanie poprzednich stanów (`$EE`, `$F0`), 8 odczytów `$4016`/`$4017`
z `AND #3 / CMP #1` (obsługa padów Famicoma i NES) do `$EF` i `$F1`.
`E576–E57F`: `$4C = ($53 & 1) ? $F1 : $EF`. `E580–E59F`: mikrofon Famicoma.
**Oba pady są czytane zawsze**; w trybie naprzemiennym używany jest tylko jeden.

## 3. Statek P1 – ruch i rysowanie (**P**)

- Statek **nie jest sprite'em**: to kafle tła (`$62/$60/$63/$61` z tablicy `$1000`) w wierszach 26–27,
  przesuwane poziomo drugim podziałem ekranu. X = `$E4` (ze znakiem), ekran x = 120 + `$E4`.
- Ruch `EEC0`: tylko gdy `$4F` = 0; Lewo → `DEC $E4` do `$96`, Prawo → `INC $E4` do `$6A`, 1 px/klatkę.
- Rysowanie / wymazywanie kafli statku: `EFFF` (z `FBEB` przy respawnie), eksplozja `EF09` (kolejka VRAM).

## 4. OAM (**P**)

Bufor `$0200–$02FF`, DMA w każdym NMI. Podział: patrz `MEMORY_MAP.md`.
Wrogowie w locie: slot × 16, 4 sprite'y 2×2 (`ED1C`, kolejność kafli wg odbicia `ED8A–EDCC`).
Wrogowie w formacji to kafle tła.

## 5. Pocisk gracza i strzelanie (**P**)

`E627` (z `E5BA`): Y w `$0280`, X w `$0283`. Y = `$C8` → pocisk „gotowy” na czubku statku,
X = `$E4`+`$7C`, kafel `$30` (gdy `$4F` ≠ 0 – kafel `$10`, niewidoczny).
Strzał `E5A8`: maska A|B (`$C0`), licznik `$44` (3 po puszczeniu) – trzeba puścić i nacisnąć.
Lot: −4 px/klatkę, po przekroczeniu góry ekranu → `$C8`. Dźwięk `FEA8`.

## 6. Pocisk vs wrogowie (**P**)

`F2B3`: `$E0`=0; `F381` formacja (pozycja pocisku → kolumna/wiersz siatki, bit w `$C3+kol`,
eksplozja w slocie 7, punkty `E833`); `F2D1` → `F2EF` wrogowie w locie (prostokąt 12×13 względem sprite'a),
trafienie → `F31E` (stan `$0B`, punkty, flagowiec + eskorta); `$E0` ≠ 0 → `$0280` = 0.

## 7. Kolizje ze statkiem (**P**)

- Pociski wrogów `E5BA–E61D`: 7 pocisków, Y += 2; jeśli `$4F` = 0 i Y−`$CA` < `$11`:
  czubek (Y−`$CA` < 5) x ∈ [`$E4`+`$7A`, +5), korpus x ∈ [`$E4`+`$77`, +11) → `$4F`=1, `FE64`, pocisk usunięty.
- Wrogowie w locie (stany 2 i 7, `EB9C` → `EC37–EC93`): Y ≥ `$98`, Y−`$C7` < 5 → x ∈ [`$E4`+`$70`, +17),
  < `$13` → x ∈ [`$E4`+`$6D`, +23) → `F31E` (wróg ginie, punkty dla gracza), `$4F`=1, `FE64`.
- Nalot celuje w `$E4`: `EE4E` (punkt docelowy przy starcie nurkowania), `E65E` (orientacja sprite'a).

## 8. Życia, punkty, Game Over, zmiana gracza (**P**)

- Punkty `E833`: `$53` wybiera wiersz (P1 `$0117`, P2 `$0129`), dodaje `$54–$58`, zero wiodące → `$10`;
  przy progu dodatkowy statek: `$3D`−−, `$42`++. Hi-score: `E2FE`/`E321` porównuje wiersz bieżącego gracza.
- Strata statku: `$4F` ≠ 0 → `E937` czeka, aż wszyscy wrogowie wrócą + 60 klatek → `$FE`=3 → `FA52`:
  `$42`=0 → `FB23` (Game Over), inaczej `FACB` (zamiana graczy, tylko gdy `$3C`) → `FA69`: `$42`−−, „READY” → `FBEB`: rysuje statek, `$4F`=0.
  W tym czasie `F415` nie wypuszcza nowych nalotów.
- Zamiana graczy `FACB`: wymienia `$3D/$3E`, `$42/$43`, `$59/$5A`, `$8E/$90`, `$8F/$91`, formacje `$C3/$CD`, przełącza `$53`.
- Game Over `FB23`: w trybie naprzemiennym najpierw komunikat dla gracza i przejście do drugiego, potem `FB65` → `$FF`=4,
  animacja `FB83`/`E400` (8 sprite'ów, ruch z `$07E8/$07F0`).

## 9. Menu 1P/2P (**P**)

Stan 1, `F75F`: SELECT przełącza `$31` bit 0 (kursor), START przytrzymany 3 klatki → `$FF`=3.
`F9D9` (start gry): przy `$FF`=3 `$3C` = `$53` = `$31 & 1`, `$42`=`$43`=3, zerowanie punktów, HUD.

## 10. HUD (**P**)

Etykiety (`1UP`, `HI-SCORE`, `2UP`) to teksty z tablicy wskaźników `$0301` (dane z CHR) rysowane przez wiersz 26 B.
Bufor `$0690–$06BB` jest strumieniowany po 2 B na wpis (`E342`, do 16 wpisów/klatkę) do `$2074–$209F`.
`E2FE` kopiuje punkty bieżącego gracza i hi-score do `$06A0–$06AE`, `E897` ikony statków (`$6E/$6F`), `E8B2` flagi etapu (`$6C/$6D`).

## 11. Implementacja Coop (skrót)

Hooki w oryginalnym kodzie (wszystkie przez `.patch` z weryfikacją oryginalnych bajtów):

| Adres | Oryginał | Nowe | Cel |
|---|---|---|---|
| `$E2CE` | `JSR $E373` | `JSR CoopPost` | rysowanie P2, HUD, hi-score P2 |
| `$E913` | `JSR $F2B3` | `JSR CoopPre` | `P1_BLOCK`, pocisk P2 vs wrogowie |
| `$E91F` | `JSR $E9B1` | `JSR CoopMid` | ruch, strzał, kolizje, życia P2 |
| `$EEC0`, `$E640` | `LDA $4F` | `LDA $07` | P1 poza grą nie steruje / nie strzela |
| `$E5DF`, `$EC59` | `INC/DEC $4F` | `INC/DEC $07` | P1 poza grą nie jest trafiany |
| `$E611`, `$EC8F` | `LDA #1 / STA $4F` | `JSR SetP1Dead / NOP` | trafienie ustawia też `P1_BLOCK` |
| `$EE4E` | `LDX $9E / LDY $9D` | `JMP AimDiver / NOP` | naloty na zmianę w P1 i P2 |
| `$FA34` | `STA $3C / STA $53` | `JSR CoopInit / NOP` | „2 PLAYERS” = co-op |
| `$FA5D` | `JMP $FB23` | `JMP P1OutOfLives` | P1 bez statków nie kończy gry, gdy P2 gra |
| `$FAA0` | `LDA $31` | `LDA $3C` | bez „PLAYER 1” przy respawnie w co-op |
| `$FC17` | `JMP $EFFF` | `JMP P1ShipRedraw` | nie rysuj statku P1 poza grą |
| `$F03F…$F061`, `$FC9B…$FCBA` | gwiazdy od `$02A0` | od `$02B4`, 19 szt. | miejsce w OAM na P2 |

Usunięty hook etapu 1 (`$E57A`) – P2 czyta `$F1` bezpośrednio.

Kluczowe decyzje:
- **Statek P2 jako sprite'y** – statek P1 jest tłem przewijanym podziałem ekranu; drugi podział w tych samych liniach jest niemożliwy.
  Grafika: lewa połowa statku (kafle `$E1` góra, `$EA` dół) + kopia odbita poziomo, bo statek jest symetryczny względem kolumny 8.
  Kafle `$E1`/`$EA` były puste, ale użyte w logo – w danych logo (CHR `$155F`, `$1568`) zamienione na `$10` (też pusty) – logo identyczne (test pikselowy).
- **Kolizje P2** – kopie oryginalnych prostokątów z `$E4` zamienionym na `P2_X`.
- **Pocisk P2 vs wrogowie** – oryginalne `F381`/`F2D1` czytają slot pocisku P1, więc pocisk P2 jest na chwilę wstawiany w ten slot (P1 zapamiętany).
- **Punkty P2** – na czas trafienia `$53`=1 i zamiana `$42/$43`, `$3D/$3E` – oryginalne `E833` liczy punkty i dodatkowy statek dla P2.
- **Życia** – P1 dalej obsługiwany przez oryginalny przebieg (pauza nalotów do respawnu P1), P2 ma własny automat: eksplozja 32 klatki,
  respawn po 120 klatkach w trakcie normalnej gry. P1 bez statków przechodzi w `P1_OUT` (statek ukryty, wrogowie celują w P2).
  Gdy obaj są poza grą, `CoopPre` ustawia `$4F`=`$22`, `$42`=0 i oryginalny przebieg kończy grę.
- **HUD** – patrz `MEMORY_MAP.md`; flagi etapu nie mieszczą się i w co-op nie są pokazywane.
