# Changelog – Galaxian Coop

## Stage 2 – 2026-10-18

Wynik: `build/Galaxian_Coop_stage2.nes` (SHA-256 `eb19e3ef1519b20da9e3a9c16c9e4cadf1a6b7725d61adfb27d875ad2db88159`),
łatka `patches/Galaxian_Coop_stage2.bps` (1289 B, bez danych oryginału).

### Dodane
- Tryb „2 PLAYERS” uruchamia jednoczesny co-op (tryb naprzemienny wyłączony). „1 PLAYER” bez zmian.
- Statek P2 (sprite'y, kolor pomarańczowo-niebieski), sterowanie padem 2, przenikanie statków.
- Pocisk P2 (A/B), trafienia w formację i wrogów w locie, punkty dla właściciela pocisku.
- Pociski i wrogowie w locie trafiają oba statki; zderzenie z wrogiem daje punkty temu, kto się zderzył (jak w oryginale).
- Eksplozja P2 (klatki eksplozji wroga), respawn po 2 s.
- Osobne życia: 3 statki na gracza, osobny dodatkowy statek; P1 bez statków ustępuje, P2 gra dalej; Game Over po odpadnięciu obu.
- Naloty celują na zmianę w P1 i P2; gdy P1 jest poza grą – w P2.
- HUD: `1UP`/`2UP`, oba wyniki, rezerwowe statki P1 (lewa strona) i P2 (prawa); wynik P2 też bije hi-score.
- `tools/asm6502.py` (asembler), `tools/bps.py` (łatki BPS), `tools/nestest.py` + `tests/test_coop.py` (15 testów).

### Zmienione
- PRG 32 KiB (NROM-256), oryginalny kod w `$E000–$FFFF`, nowy od `$8000`.
- 19 gwiazd zamiast 24 (5 sprite'ów dla P2).
- CHR: 2 kafle sprite'ów dla P2; 2 komórki logo wskazują inny pusty kafel (wygląd bez zmian).

### Usunięte / naprawione
- Hook etapu 1 (`$E57A` → kopiowanie `$F1` do `$07F0`). `$07F0` jest używany przez grę;
  w etapie 1 sprite 0 animacji po GAME OVER nie poruszał się (wykazane testem).

### Znane ograniczenia
- Flagi etapu nie są wyświetlane w co-op (brak miejsca w HUD).
- Statek P2 jest ostatni w kolejności OAM przed gwiazdami: przy >8 sprite'ach w linii (dużo wrogów nisko) może migać/znikać fragmentami.
- Śmierć P1 wstrzymuje nowe naloty do jego respawnu (oryginalny przebieg); śmierć P2 – nie.
- Komunikat „READY” pokazuje się też, gdy P1 odpada (bez statku).
- Wrogowie obracają sprite w stronę P1 również wtedy, gdy lecą na P2 (tylko wygląd).

## Stage 1 – eksperyment (przed repozytorium)

Rozszerzenie PRG do 32 KiB, hook `$E57A → $8000` kopiujący pad 2 do `$07F0`. Zastąpiony w Stage 2.
