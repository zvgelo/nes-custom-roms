[English](README.md) | **Polski**

<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="NES Custom ROMs – gra we dwóch w klasyczne gry NES, budowana z własnego ROM-u">
</p>

<p align="center">
  <a href="#gry">Gry</a> ·
  <a href="#szybki-start">Szybki start</a> ·
  <a href="#budowanie-i-testy">Budowanie i testy</a> ·
  <a href="#struktura-projektu">Struktura</a> ·
  <a href="#prawa-i-autorzy">Prawa i autorzy</a>
</p>

**NES Custom ROMs** zbiera nieoficjalne projekty, dzięki którym **dwóch graczy gra jednocześnie**
w klasyczne gry NES/Famicom: autorską modyfikację kooperacyjną *Galaxiana* oraz powtarzalne budowanie
istniejącego hacka kooperacyjnego *Super Mario Bros.* Repozytorium zawiera kod źródłowy, skrypty budujące,
testy i łatki (cudze wyraźnie oznaczone) – nigdy samych gier. Buduje się z własnego, legalnie uzyskanego ROM-u.

## Gry

| [Galaxian Coop](games/galaxian-coop/README_PL.md) | Super Mario Bros. Two Players Hack – zestaw do budowania |
|---|---|
| ![Galaxian Coop: dwóch pilotów walczy razem z formacją](games/galaxian-coop/assets/screenshots/03-coop-gameplay.png) | *Kod, zrzuty i README na gałęzi `game/super-mario-coop`.* |
| Nowy silnik kooperacji dla *Galaxiana* (Japonia), autor Zvgelo: drugi statek, poziomy broni, 12-sekundowy Red Laser Overdrive z kontratakiem wrogów, tarcza po odrodzeniu, dzielenie się życiami. Te same zasady dla jednego pilota. | Budowanie jednym poleceniem, z kontrolą sum, hacka *Super Mario Bros. Two Players Hack* – **autorzy hacka: Corpse Grinder i Ti (2018)**; oryginalna łatka jest dołączona z podaniem autorów (nie na licencji MIT), a ROM pozostaje niezmieniony. |
| Mapper 0 · łatka BPS w repozytorium · RC6 | Mapper 24 (VRC6a) · oryginalna `.xdelta` hacka |

Każdy projekt jest rozwijany na osobnej gałęzi (`game/galaxian-coop`, `game/super-mario-coop`); ta gałąź
zawiera Galaxian Coop. Każde README opisuje zasady lub sterowanie, zrzuty ekranu i rozwiązywanie problemów.

## Najważniejsze cechy

- **Dwóch graczy naraz** na jednym ekranie, każdy z własnym kontrolerem.
- **Zwykłe emulatory**: łatany jest ROM, nie emulator; wyniki to zwykłe pliki NES z mapperem 0 i 24.
- **Powtarzalne budowanie**: każde wejście i wyjście jest sprawdzane przez SHA-256; dwa buildy dają te same
  bajty.
- **Łatki bez danych gry**: łatka BPS Galaxiana czyta oryginalne dane z Twojego ROM-u; test sprawdza, że nie
  zawiera żadnej części oryginału.
- **Testy w emulatorach**: cynes, rdzeń FCEUmm i tracer 6502 (dźwięk, RAM) – zob.
  [docs/TESTING.md](games/galaxian-coop/docs/TESTING.md) (po angielsku).

## Szybki start

Nałóż łatkę Galaxian Coop na swój ROM (Python 3, z katalogu głównego repozytorium):

```bash
git switch game/galaxian-coop
sha256sum "Galaxian (Japan).nes"
# 1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e
python3 tools/bps.py apply "Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"
sha256sum "Galaxian Coop.nes"
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

Otwórz `Galaxian Coop.nes` w dowolnym emulatorze NES. Działa też każde inne narzędzie BPS (Flips,
Rom Patcher JS, beat). Do Mario Two Players Hack przełącz się na gałąź `game/super-mario-coop` i postępuj
według jej README.

## Budowanie i testy

```bash
python3 games/galaxian-coop/src/build.py        # wymaga games/galaxian-coop/private/Galaxian (Japan).nes
```

Wynik trafia do `games/galaxian-coop/build/`; build wypisuje SHA-256 wyniku i odrzuca złe wejścia. Testy
i ich ostatnie wyniki: [docs/TESTING.md](games/galaxian-coop/docs/TESTING.md) (cynes 112, FCEUmm 8,
tracer 5 – wszystkie zaliczone; po angielsku). Budowanie wymaga tylko Pythona 3 (testowane 3.14, Linux);
testy w emulatorach wymagają pakietów z `games/galaxian-coop/tests/requirements.txt`, a zestaw FCEUmm –
`stable-retro`.

## Struktura projektu

```text
nes-custom-roms/
├── README.md               opis po angielsku (ta strona: README_PL.md)
├── LICENSE                 licencja MIT – własne materiały projektu
├── THIRD_PARTY_NOTICES.md  czego licencja MIT nie obejmuje
├── assets/readme/          grafika README
├── tools/                  wspólne narzędzia: asembler 6502, łatki BPS, dekoder VCDIFF,
│                           pomocnicze funkcje testów, tracer 6502
└── games/
    └── <gra>/
        ├── README.md       zasady, instalacja, sterowanie, zrzuty (+ README_PL.md)
        ├── assets/         zrzuty ekranu (i grafika README)
        ├── src/            kod źródłowy i build.py
        ├── patches/        łatki – bez danych oryginału (cudze: zob. THIRD_PARTY_NOTICES)
        ├── docs/           CHANGELOG, TESTING i dokumentacja techniczna
        ├── tests/          testy automatyczne
        ├── private/        Twoje oryginalne ROM-y                (ignorowane przez git)
        └── build/          wygenerowane ROM-y i pliki wynikowe   (ignorowane przez git)
```

## Prawa i autorzy

- **Licencja**: własny kod, narzędzia, testy, dokumentacja i grafika projektu są udostępnione na
  [licencji MIT](LICENSE) © 2026 Zvgelo. Licencja **nie** obejmuje oryginalnych gier, ROM-ów ani ich
  zasobów, Super Mario Bros. Two Players Hack ani jego oryginalnej łatki (dołączonej z podaniem autorów,
  bez domniemanej zgody na redystrybucję), ani innych materiałów osób trzecich – zob.
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) (po angielsku).
- **Nieoficjalny projekt fanowski.** Niepowiązany z Bandai Namco, Nintendo ani autorami Two Players Hack
  i nieautoryzowany przez nich. *Galaxian* © Namco (1979, NES/Famicom 1984); *Super Mario Bros.* ©
  Nintendo (1985). Nazwy gier i znaki towarowe należą do ich właścicieli.
- **Brak ROM-ów** – oryginalnych i zmodyfikowanych – w repozytorium i w linkach; `*.nes`, `private/`
  i `build/` są wykluczone w `.gitignore`. Potrzebna jest własna, legalnie uzyskana kopia każdej gry.
- **Autorzy**: *Super Mario Bros. – Two Players Hack*: oryginalny hack **Corpse Grinder & Ti** (2018).
  *Galaxian Coop*, narzędzia, testy i dokumentacja: **Zvgelo** (2026).
