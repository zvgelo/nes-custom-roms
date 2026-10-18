# Galaxian Coop

Jednoczesny tryb co-op dla dwóch graczy do *Galaxian (Japan)* na NES/Famicom,
inspirowany Galaxian DX z C64. Wybór **2 PLAYERS** na ekranie tytułowym uruchamia co-op,
**1 PLAYER** to niezmieniona oryginalna gra.

## ROM wejściowy (nie ma go w repozytorium)

Umieść własny zrzut w `rom/Galaxian (Japan).nes`
(SHA-256 `1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e`).
Katalogi `rom/` i `build/` są ignorowane przez git; oryginał jest tylko czytany.

## Budowanie

```bash
python3 games/galaxian-coop/src/build.py            # -> build/Galaxian_Coop_stage2.nes (+ .mlb dla Mesen 2)
python3 games/galaxian-coop/src/build.py --bps      # dodatkowo patches/Galaxian_Coop_stage2.bps
python3 tools/bps.py apply "rom/Galaxian (Japan).nes" patches/Galaxian_Coop_stage2.bps out.nes
```

Wymaga tylko Pythona 3 (bez zależności). Kod 6502 w `src/asm/coop.asm`, asembler `tools/asm6502.py`;
każda zmiana oryginalnego kodu jest opisana dyrektywą `.patch` z oryginalnymi bajtami, które build weryfikuje.

## Testy

```bash
.venv/bin/pip install -r games/galaxian-coop/tests/requirements.txt
.venv/bin/python games/galaxian-coop/tests/test_coop.py -v
```

## Dokumentacja

- `docs/REVERSE_ENGINEERING.md` – procedury gry i opis hooków
- `docs/MEMORY_MAP.md` – RAM, ROM, OAM
- `docs/CHANGELOG.md` – zmiany i znane ograniczenia
- `docs/TESTING.md` – testy wykonane i do wykonania w Mesen 2
- `docs/STAGE1_NOTES.md` – notatki z etapu 1 (historyczne)
