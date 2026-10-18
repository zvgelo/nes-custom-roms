# Testy – Galaxian Coop

## Automatyczne (wykonane)

```bash
.venv/bin/pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
.venv/bin/python games/galaxian-coop/tests/test_coop.py -v
```

Ostatni przebieg (2026-10-18, Linux, Python 3.14, cynes 0.1.2): **15/15 OK**, ~95 s.

| Test | Co sprawdza |
|---|---|
| `test_reproducible` | dwa buildy dają identyczny plik |
| `test_original_untouched` | oryginalny ROM nie zmieniony (SHA-256) |
| `test_header` | NES 2.0, mapper 0, 32 KiB PRG, 8 KiB CHR |
| `test_vectors` | NMI `$E20C`, RESET/IRQ `$E020` |
| `test_original_code_only_changed_at_patches` | oryginalny kod zmieniony wyłącznie w miejscach `.patch` |
| `test_stage1_hook_removed` | `$E57A` ma oryginalne bajty |
| `test_chr` | CHR różni się tylko 2 kaflami P2 i 2 komórkami logo |
| `test_chr_change_invisible_on_title` | oryginał vs oryginał+nowy CHR: 1200 klatek ekranu tytułowego/demo identycznych pikselowo |
| `test_one_player_has_no_p2` | tryb 1P: sprite'y P2 nigdy widoczne, pad 2 bez wpływu |
| `test_independent_movement` | P1 w prawo + P2 w lewo jednocześnie, potem tylko P2 |
| `test_p2_shots_score_for_p2` | strzały P2 zwiększają tylko wynik P2 |
| `test_p2_death_respawn_and_lives` | trafienie P2 → eksplozja → respawn, `$43`−1 |
| `test_game_over_only_when_both_out` | pełna gra: P1 odpada, P2 gra dalej, Game Over po obu |
| `test_game_over_scatter_ignores_pad2` | regresja `$07F0` (etap 1 ten test oblewa) |
| `test_stress_no_crash_or_overrun` | 3 min losowego wejścia: bez crasha, zapas CPU w NMI |

Dodatkowo wykonane ręcznie (skrypty w trakcie prac): zrzuty ekranu ruchu obu statków, strzału, eksplozji, HUD;
6 sesji × 6 min z losowym wejściem (1P i co-op) – bez crasha i resetu, minimalny zapas ~286 iteracji pętli głównej (oryginał ~332).

Ograniczenia testów automatycznych: cynes to inny emulator niż Mesen; nie bada timingu PPU co do cyklu,
nie słuchano dźwięku, testy nie oceniają grywalności. **Nie testowano na Mesen 2 ani na sprzęcie.**

## Do wykonania przez użytkownika (Mesen 2)

1. Zbuduj: `python3 games/galaxian-coop/src/build.py` → `games/galaxian-coop/build/Galaxian_Coop_stage2.nes`.
2. Mesen: Settings → Input → podłącz 2 kontrolery (Player 1 i Player 2).
3. Ekran tytułowy: logo bez zmian, SELECT przesuwa kursor, START.
4. **1 PLAYER**: gra jak oryginał, brak drugiego statku, pad 2 nic nie robi.
5. **2 PLAYERS**:
   - oba statki pojawiają się razem; P2 pomarańczowo-niebieski;
   - ruch obu jednocześnie, przenikanie się statków;
   - strzał obu jednocześnie; punkty trafiają do właściwego wyniku (`1UP` / `2UP`);
   - trafienie P2: eksplozja, po ~2 s respawn na środku, ubywa ikona po prawej;
   - trafienie P1: oryginalna sekwencja (naloty wstrzymane, „READY”), P2 gra dalej;
   - P1 traci ostatni statek: P2 gra dalej, wrogowie atakują P2;
   - Game Over dopiero po utracie wszystkich statków obu graczy;
   - wynik P2 większy od hi-score aktualizuje hi-score.
6. Obserwuj: miganie sprite'ów przy statku P2 (Debug → Event Viewer / „Remove sprite limit” off),
   poprawność podziału ekranu (dolny pasek ze statkiem P1 przy skrajnych pozycjach), pauza START na padzie 1.
7. Debugger (opcjonalnie): build zapisuje obok ROM-u `Galaxian_Coop_stage2.mlb` (etykiety nowego kodu i RAM) – w debuggerze Mesen 2: File → Import Labels (format Mesen 2, import nie był testowany). Watch `$05–$12`.

Zgłaszając błąd, podaj: tryb, co robili gracze, zrzut ekranu i ewentualnie save state.
