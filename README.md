# nes-custom-roms

Lokalne repozytorium modyfikacji gier NES/Famicom. Jedna gra = jeden katalog w `games/`
i jeden branch roboczy `game/<nazwa>`; `main` zawiera tylko ukończone i zweryfikowane gry.

## Projekty

| Projekt | Katalog | Branch | Stan |
|---|---|---|---|
| Super Mario Bros. Two Players Hack (build kit) | `games/super-mario-coop/` | `game/super-mario-coop` | ukończony |
| Galaxian Coop | `games/galaxian-coop/` | `game/galaxian-coop` | Stage 2, czeka na test w RetroArch (jeszcze nie w `main`) |

Szczegóły każdej gry: jej `README.md` i katalog `docs/`.

## Struktura gry

```text
games/<gra>/
├── README.md     cel, funkcje, bazowy ROM i sumy, build, emulator, stan, ograniczenia, autorzy
├── src/          kod, asembler, patchery, build.py
├── patches/      dystrybuowalne łatki (IPS/BPS/xdelta) bez danych oryginału
├── docs/         CHANGELOG.md, TESTING.md (+ dokumentacja techniczna)
├── tests/        testy automatyczne
├── private/      oryginalne ROM-y i prywatne wejścia   (ignorowane przez Git)
└── build/        wygenerowane ROM-y i pliki wynikowe     (ignorowane przez Git)
```

`tools/` – narzędzia faktycznie używane przez więcej niż jeden projekt lub ogólne
(asembler, dekoder xdelta, łatki BPS, pomocnicze funkcje testów).

## Start

1. Python 3.10+ (build nie wymaga dodatkowych pakietów).
2. Własny zrzut oryginalnego ROM-u skopiuj do `games/<gra>/private/` pod nazwą podaną w README gry.
3. Build: `python3 games/<gra>/src/build.py` → wynik w `games/<gra>/build/`.
   Build sprawdza sumy SHA-256, nie zmienia oryginału i zwraca kod błędu przy niepowodzeniu.
4. Testy: `python3 games/<gra>/tests/<test>.py -v`; testy emulatorowe wymagają pakietów z
   `games/<gra>/tests/requirements.txt` (bez nich są pomijane).

ROM-y (oryginalne i wygenerowane) nigdy nie trafiają do Git. Repozytorium jest wyłącznie lokalne.
