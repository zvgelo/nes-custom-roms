# Galaxian Coop

## Cel

Jednoczesny tryb co-op dla dwóch graczy do *Galaxian (Japan)* na NES/Famicom, inspirowany Galaxian DX z C64,
z zachowaniem wyglądu i klimatu oryginału. Wybór **2 PLAYERS** uruchamia co-op (zamiast gry naprzemiennej),
**1 PLAYER** to niezmieniona oryginalna gra.

## Funkcjonalność

- Dwa statki naraz: P1 – pad 1 (oryginalny statek), P2 – pad 2 (pomarańczowo-niebieski); statki się przenikają.
- Każdy gracz ma własny pocisk (A/B); punkty dostaje właściciel pocisku.
- Pociski i nurkujący wrogowie trafiają oba statki; naloty celują na zmianę w P1 i P2.
- Osobne 3 statki i osobny dodatkowy statek dla każdego gracza; gracz bez statków odpada, drugi gra dalej;
  Game Over po odpadnięciu obu.
- HUD: `1UP`/`2UP`, oba wyniki, rezerwowe statki P1 (lewo) i P2 (prawo); wynik P2 też bije hi-score.

## Autorzy

- *Galaxian* – Namco (arcade 1979, NES/Famicom 1984).
- Galaxian Coop – Zvgelo 2026 (kod 6502 w `src/asm/coop.asm`, narzędzia, testy). Nie korzysta z cudzych hacków.

## Bazowy ROM i sumy kontrolne

Własny zrzut skopiuj do `private/Galaxian (Japan).nes` (albo podaj ścieżkę jako argument builda).

| Plik | Rozmiar | SHA-256 |
|---|---|---|
| `private/Galaxian (Japan).nes` | 16 400 | `1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e` |
| `build/Galaxian_Coop_stage2.nes` | 40 976 | `eb19e3ef1519b20da9e3a9c16c9e4cadf1a6b7725d61adfb27d875ad2db88159` |
| `patches/Galaxian_Coop_stage2.bps` | 1 289 | (łatka BPS z oryginału; nie zawiera jego danych) |

Oryginał: NES 2.0, mapper 0, 8 KiB PRG + 8 KiB CHR. Wynik: NES 2.0, mapper 0 (NROM-256), 32 KiB PRG + 8 KiB CHR.

## Budowanie

```bash
python3 games/galaxian-coop/src/build.py            # -> build/Galaxian_Coop_stage2.nes + .mlb (etykiety Mesen 2)
python3 games/galaxian-coop/src/build.py --bps      # dodatkowo patches/Galaxian_Coop_stage2.bps
python3 games/galaxian-coop/src/build.py ŚCIEŻKA/rom.nes -o WYJŚCIE.nes
python3 tools/bps.py apply "games/galaxian-coop/private/Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop_stage2.bps WYJŚCIE.nes
```

Tylko Python 3, bez dodatkowych pakietów. Build sprawdza SHA-256 oryginału i oryginalne bajty w każdym miejscu
`.patch`, nie nadpisuje oryginału, przy błędzie kończy się kodem 1. Asembler: `tools/asm6502.py`.

## Uruchamianie w emulatorze

Mapper 0 – działa w każdym emulatorze NES (Mesen 2, FCEUX, RetroArch: FCEUmm/Mesen/Nestopia).
Potrzebne dwa pady: port 1 i port 2. Instrukcje dla Mesen 2 i RetroArcha: `docs/TESTING.md`.

## Stan

Stage 2 ukończony: wszystkie funkcje powyżej działają w testach automatycznych (15/15, emulator cynes).
Czeka na test użytkownika w RetroArch (manual test setup); niezmergowany do `main`.

## Znane ograniczenia

- Flagi etapu nie są wyświetlane w trybie co-op (brak miejsca w HUD).
- Statek P2 to sprite'y – przy wielu wrogach nisko na ekranie może migać (limit 8 sprite'ów na linię).
- Śmierć P1 wstrzymuje naloty do jego respawnu (oryginalny przebieg); śmierć P2 – nie.
- Gwiazd jest 19 zamiast 24.
- Szczegóły: `docs/CHANGELOG.md`.

## Testy i dokumentacja

```bash
.venv/bin/pip install -r games/galaxian-coop/tests/requirements.txt    # cynes, numpy
.venv/bin/python games/galaxian-coop/tests/test_coop.py -v
```

- `docs/REVERSE_ENGINEERING.md` – procedury gry i hooki
- `docs/MEMORY_MAP.md` – RAM, ROM, OAM
- `docs/CHANGELOG.md` – historia zmian
- `docs/TESTING.md` – wyniki testów i testy do wykonania
- `docs/STAGE1_NOTES.md` – notatki z etapu 1 (historyczne)
