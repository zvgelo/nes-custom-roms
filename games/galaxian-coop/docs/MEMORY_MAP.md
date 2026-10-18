# Galaxian (Japan) / Galaxian Coop – mapa pamięci

Oznaczenia pewności:
- **P** – potwierdzone: wynika wprost z kodu i zostało sprawdzone w emulatorze (cynes, odczyt RAM).
- **K** – wynika z analizy kodu, bez osobnego testu dynamicznego.
- **H** – hipoteza / interpretacja nazwy.

Adresy CPU. Offset w pliku ROM Coop = `0x10 + (adres − $8000)`; w oryginale `0x10 + (adres − $E000)`.

## Pamięć ROM

| Zakres CPU | Oryginał | Galaxian Coop |
|---|---|---|
| `$8000–$DFFF` | lustra 8 KiB PRG (nieużywane przez kod – brak odwołań, **P**) | nowy kod (`$8000–$8421`, reszta `$FF`) |
| `$E000–$FFFF` | program gry | program gry + hooki `.patch` |
| `$FFFA/$FFFC/$FFFE` | NMI `$E20C`, RESET `$E020`, IRQ `$E020` | bez zmian (**P**, test `test_vectors`) |

CHR (8 KiB): tablica `$0000` = sprite'y w grze / tło na ekranie tytułowym, `$1000` = tło w grze.
Fragmenty CHR są jednocześnie danymi: reset kopiuje PPU `$1480–$17FF` → RAM `$0300–$067F`
i PPU `$098E–$0A3F` → RAM `$014E–$01FF` (**P**).

## RAM – zmienne oryginalnej gry

### Strona zerowa

| Adres | Znaczenie | Pewność |
|---|---|---|
| `$00–$04` | odtwarzacz muzyki startowej (`FF0E`) | K |
| `$23–$24` | detekcja mikrofonu Famicoma (`$4016` bit 2) | K |
| `$27`, `$28` | liczniki wrogów w formacji (ograniczają naloty) | H |
| `$29` | flaga „po zmianie gracza” (tryb naprzemienny) | K |
| `$2A` | flaga „NMI w toku” (ochrona przed ponownym wejściem) | K |
| `$2B` | timer komunikatu GAME OVER gracza (tryb naprzemienny) | K |
| `$2D` | indeks kolejki odświeżania HUD (0–$15) | K |
| `$30`, `$31` | menu: licznik przytrzymania START/SELECT, wybór (bit0: 0 = 1 PLAYER, 1 = 2 PLAYERS) | P |
| `$36–$39` | wiersz tekstu do zapisu w NMI: adres VRAM, wskaźnik danych | K |
| `$3A–$3B` | licznik pętli głównej (czas bezczynności CPU, ziarno RNG) | P |
| `$3C` | flaga trybu naprzemiennego 2P (w Coop zawsze 0) | P |
| `$3D` / `$3E` | dodatkowy statek jeszcze do zdobycia: P1 / P2 | K |
| `$3F` | timer bonusu za flagowca | K |
| `$40`, `$41` | efekty dźwiękowe: strzał, eksplozja | K |
| `$42` / `$43` | statki w rezerwie: P1 / P2 (w oryginale „bieżący / drugi gracz”) | P |
| `$44` | licznik przycisku strzału P1 | K |
| `$4C` | przyciski aktywnego gracza (z `$EF`/`$F1` wg `$53`) | P |
| `$4E` | pauza | K |
| `$4F` | P1 trafiony: 0 = żyje, 1..$22 = eksplozja, $22 = koniec animacji | P |
| `$53` | bieżący gracz (wybór pada i wiersza punktów) – w Coop 0, chwilowo 1 przy punktach P2 | P |
| `$54–$58` | punkty do dodania (BCD cyframi) | K |
| `$59` / `$5A` | numer etapu P1 / P2 (tryb naprzemienny) | K |
| `$5B–$67` | liczniki i poziom trudności nalotów | H |
| `$68–$81` | dźwięk | K |
| `$8E–$91` | stan flagowców (zamieniane między graczami) | K |
| `$92–$9B` | liczba wrogów w locie na kolumnę | K |
| `$9C` | ogólny timer sekwencji | K |
| `$9D`, `$9E` | bieżący slot wroga: offset OAM (slot×16), indeks slotu | P |
| `$9F` | formacja pusta | K |
| `$A0–$BF`, `$C0–$C2` | kolejka eksplozji w tle | K |
| `$C3–$CC` / `$CD–$D6` | mapa bitowa formacji (bieżący / drugi gracz) | P |
| `$D7–$DF`, `$E0` | zmienne tymczasowe (`$E0` = flaga trafienia pocisku) | K |
| `$E1` | liczba wpisów kolejki VRAM (maks. 16) | P |
| `$E2–$E3`, `$E8–$EB` | wskaźniki tymczasowe, dispatcher `$E44B` | P |
| `$E4` | X statku P1 (ze znakiem, `$96..$6A`), przewijanie dolnego paska | P |
| `$E5` | przesunięcie formacji (przewijanie górnej części) | P |
| `$EC`, `$ED` | licznik klatek | K |
| `$EE`/`$EF` | pad 1: poprzednia / bieżąca klatka | P |
| `$F0`/`$F1` | pad 2: poprzednia / bieżąca klatka | P |
| `$F6`, `$F7`, `$FA`, `$FB` | kopie `$2005`, `$2001`, `$2000` | P |
| `$FD`, `$FE`, `$FF` | maszyna stanów: pod-pod-stan, pod-stan, stan główny | P |

Bity padów (`$EF`, `$F1`): 7 A, 6 B, 5 SELECT, 4 START, 3 Góra, 2 Dół, 1 Lewo, 0 Prawo (**P**).

Stany `$FF`: 0 inicjalizacja, 1 ekran tytułowy, 2 demo, 3 gra, 4 GAME OVER, 5 koniec demo / ekran końcowy, 6 powrót do 0 (**P** dla 1–4).
Pod-stany gry (`$FE`, tabela `$E901`): 0–1 czyszczenie ekranu, 2 start gry `F9D9`, 3 strata statku / koniec fali `FA52`, 4 `F883`, 5 czyszczenie, 6 respawn `FA69`, 7 „READY” `FBEB`, 8 normalna gra `E913` (**P**).

### Strona 1 (stos i dane)

| Adres | Znaczenie | Pewność |
|---|---|---|
| `$0101–$0115` | flagi resetu / sygnatura | K |
| `$0116–$012F` | blok punktów: P1 `$0117–$011C`, hi-score `$0120–$0125`, P2 `$0129–$012E` (cyfry 0–9, `$10` = pusto) | P |
| `$0130–$014D` | stos (S startuje od `$4D`, NMI resetuje grę gdy S < `$30`) | P |
| `$014E–$01FF` | dane dźwięku skopiowane z CHR | K |

### Strony 2–7

| Adres | Znaczenie | Pewność |
|---|---|---|
| `$0200–$027F` | OAM: 8 slotów wrogów w locie po 4 sprite'y (slot 7 = eksplozja wroga z formacji) | P |
| `$0280–$0283` | OAM: pocisk P1 (Y=`$C8` gotowy na statku, 0 = zużyty) | P |
| `$0284–$029F` | OAM: 7 pocisków wrogów | P |
| `$02A0–$02FF` | OAM: 24 gwiazdy (oryginał) | P |
| `$0300–$067F` | dane z CHR: teksty, układ logo, tablice | P |
| `$0690–$06BB` | bufor HUD → VRAM `$2074–$209F` (wiersz 3 kol. 20 … wiersz 4 kol. 31) | P |
| `$06BC–$06D5` | bufor 26-znakowego wiersza tekstu | K |
| `$06D8–$06FF`, `$0700–$07FF` | stan wrogów w locie, kolejka VRAM (`$0748/58/68/78`), tablice ruchu | K |
| `$07E8–$07FF` | 24 wpisy liczone co klatkę przez `E471` (prędkości; `$07FF` = prędkość formacji) | P |

**`$07F0` nie jest wolny** (**P**): to wpis Y=8 tablicy `$07E8+Y`, zapisywany przez `E4A1/E4A6`
i czytany w `E413` jako przesunięcie Y sprite'a 0 w animacji po GAME OVER (`FB83`/`E400`).
Bufor z etapu 1 nadpisywał go przyciskami P2, przez co ten sprite stał w miejscu
(test `test_game_over_scatter_ignores_pad2`; etap 1 go nie przechodzi).

## RAM – nowe zmienne Galaxian Coop

Zakres `$05–$22` nie jest używany przez oryginalny kod (statyczny skan wszystkich odwołań)
i pozostał zerowy w 6 sesjach emulatora po 2 min z losowym wejściem (**P**). Reset zeruje stronę zerową.

| Adres | Nazwa | Znaczenie |
|---|---|---|
| `$05` | `COOP` | 1 = gra w trybie co-op (wybór „2 PLAYERS”) |
| `$06` | `P1_OUT` | P1 bez statków, P2 gra dalej |
| `$07` | `P1_BLOCK` | `$4F` lub `P1_OUT` – używane zamiast `$4F` w sterowaniu/kolizjach P1 |
| `$08` | `P2_STATE` | 0 poza grą, 1 żyje, 2 eksplozja, 3 czeka na respawn |
| `$09` | `P2_X` | X statku P2 (ta sama konwencja co `$E4`) |
| `$0A` | `P2_TIMER` | timer eksplozji / respawnu |
| `$0B` | `P2_FIRE` | licznik przycisku strzału P2 |
| `$0C` | `P2_BY` | Y pocisku P2 (`$C8` gotowy, 0 zużyty) |
| `$0D` | `P2_BX` | X pocisku P2 |
| `$0E–$0F` | `SAVE_BY/BX` | pocisk P1 odłożony na czas sprawdzania pocisku P2 |
| `$10–$11` | `T0/T1` | tymczasowe |
| `$12` | `AIM_TOGGLE` | naprzemienny cel nalotu |
| `$13–$22` | – | wolne |

Liczniki statków P2 i dodatkowego statku P2 to oryginalne `$43` i `$3E`, punkty P2 – oryginalny wiersz `$0129–$012E`.

## OAM w Galaxian Coop

| Zakres | Zawartość |
|---|---|
| `$0200–$029F` | bez zmian |
| `$02A0–$02AF` | statek P2: TL, TR (odbity), BL, BR (odbity); kafle `$E1`/`$EA`, paleta 0 |
| `$02B0–$02B3` | pocisk P2 (kafel `$30`) |
| `$02B4–$02FF` | 19 gwiazd (było 24) |

Ukryte sprite'y P2 mają Y = `$F8`.
