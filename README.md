# nes-custom-roms

Unofficial modifications of classic NES/Famicom games, distributed as **source code and patches** – no
ROM images. You bring your own legally obtained copy of the original game; the build (or a BPS patch)
checks it and produces the modified `.nes` file locally.

![Super Mario Bros. Co-op: Mario and Luigi in level 1-1](games/super-mario-coop/assets/screenshots/03-two-players-run.png)

## What is NES ROM hacking?

An NES game is a small program for the console's 6502 CPU plus graphics data, stored in a ROM image.
A *ROM hack* changes that program or data – here to let two players play at the same time. Because the
original games are copyrighted, this repository never contains them: it contains the new code, the tools
that assemble and apply it, and patch files that only describe the differences. A patch is useless
without the original ROM it was made for.

## Available modifications

| Game | What it adds | Mapper of the result | Documentation |
|---|---|---|---|
| **Galaxian Coop** | Simultaneous 2-player co-op for *Galaxian* (Japan, Namco): a second ship, weapon levels W1–W4, a 12-second Red Laser Overdrive with an enemy counter-attack, respawn shield, life sharing, extra lives, stage counter. Same rules in 1-player mode. New code by Zvgelo. | 0 (NROM) | on branch `game/galaxian-coop`: `games/galaxian-coop/README.md` |
| **Super Mario Bros. Two Players Hack – build kit** | Mario and Luigi at the same time. The game is the *Two Players Hack* by Corpse Grinder and Ti (2018); this project only builds the unmodified hack reproducibly. | 24 (VRC6a) | [games/super-mario-coop/README.md](games/super-mario-coop/README.md) |

Each game lives in its own folder under `games/` and is developed on its own branch
(`game/galaxian-coop`, `game/super-mario-coop`).

## Requirements

- **Python 3** to build or patch (tested with Python 3.14 on Linux). Building needs nothing else: the
  repository has its own 6502 assembler (`tools/asm6502.py`), BPS patcher (`tools/bps.py`) and
  xdelta/VCDIFF decoder (`tools/vcdiff.py`).
- **Your original ROM** with the SHA-256 given in the game's README.
- **An NES emulator** that supports the mapper listed above, e.g. Mesen 2, FCEUmm (standalone or as a
  RetroArch core), Nestopia or FCEUX.
- Optional, for the automatic tests only: the packages in `games/<game>/tests/requirements.txt`
  (`cynes`, `numpy`) and `stable-retro` for the FCEUmm tests.

## Quick start – Galaxian Coop with the BPS patch

```bash
git clone <repository-url> nes-custom-roms
cd nes-custom-roms
git switch game/galaxian-coop                    # the branch the game is developed on

# check your original ROM: must print 1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e
sha256sum "/path/to/Galaxian (Japan).nes"

# apply the patch (any BPS tool works too: Flips, Rom Patcher JS, beat)
python3 tools/bps.py apply "/path/to/Galaxian (Japan).nes" \
    games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"

# check the result against the checksum in games/galaxian-coop/docs/CHANGELOG.md
sha256sum "Galaxian Coop.nes"
```

Then open `Galaxian Coop.nes` in your emulator. Controls and rules: `games/galaxian-coop/README.md` on
that branch.

## Building from source

```bash
# Galaxian Coop
mkdir -p games/galaxian-coop/private
cp "/path/to/Galaxian (Japan).nes" games/galaxian-coop/private/
python3 games/galaxian-coop/src/build.py         # -> games/galaxian-coop/build/Galaxian_Coop.nes

# Super Mario Bros. Co-op
mkdir -p games/super-mario-coop/private
cp "/path/to/Super Mario Bros. (World).nes" games/super-mario-coop/private/original.nes
python3 games/super-mario-coop/src/build.py      # -> games/super-mario-coop/build/
```

Every build checks the SHA-256 of its inputs, never writes to the original ROM, writes only to the
game's `build/` folder, produces the same bytes on every run, prints the SHA-256 of the result and exits
with code 1 on any error. Each game's README lists the expected checksums.

## Running the games

Load the built `.nes` file in any emulator that supports the game's mapper. For the co-op modes assign a
different input device to player 1 and player 2 (in RetroArch: Settings → Input → *Port 1 Controls* /
*Port 2 Controls*) and connect both controllers before starting the game. The games were tested
automatically in the cynes emulator and in the FCEUmm core (see each game's `docs/TESTING.md`); other
emulators and real hardware are listed there as not tested.

## Testing

```bash
pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
python3 games/galaxian-coop/tests/test_coop.py -v           # cynes emulator, 112 tests
python3 games/galaxian-coop/tests/test_trace.py -v          # 6502 tracer: sound and RAM, 5 tests
pip install stable-retro
python3 games/galaxian-coop/tests/test_fceumm.py -v         # FCEUmm core, 8 tests

python3 games/super-mario-coop/tests/test_build.py -v      # 16 tests
python3 games/super-mario-coop/tests/test_emulator.py -v    # FCEUmm core, 2 tests
```

The tests need the original ROMs in the games' `private/` folders; without them they are skipped.

## Repository structure

```text
nes-custom-roms/
├── README.md                this file
├── .gitignore               keeps ROMs, private/ and build/ out of git
├── tools/                   shared tools
│   ├── asm6502.py           6502 assembler (Galaxian Coop)
│   ├── bps.py               create / apply BPS patches
│   ├── nestest.py           cynes emulator helpers for tests, PNG writer
│   ├── trace6502.py         6502 tracer (sound and RAM checks)
│   └── vcdiff.py            xdelta / VCDIFF decoder (Super Mario Bros. Co-op)
└── games/
    └── <game>/
        ├── README.md        what the mod does, required ROM, build, controls, troubleshooting
        ├── assets/          screenshots
        ├── src/             source code and build.py
        ├── patches/         distributable patches – no original game data
        ├── docs/            CHANGELOG, TESTING and technical notes
        ├── tests/           automatic tests
        ├── private/         your original ROMs              (ignored by git)
        └── build/           generated ROMs and other output  (ignored by git)
```

## Legal notice

- This is an **unofficial fan project**. It is not affiliated with, endorsed by or sponsored by Namco,
  Bandai Namco, Nintendo or any other rights holder. *Galaxian* and *Super Mario Bros.* and their
  characters, graphics and trademarks belong to their owners.
- The repository contains **no original or modified ROM images**: `*.nes`, `private/` and `build/` are
  excluded by `.gitignore`, and no `.nes` file has ever been committed. You need your own, legally
  obtained copy of each original game. Links to ROM downloads are neither given nor accepted.
- The BPS patch made by `tools/bps.py` copies the original data from your ROM instead of storing it; a
  test checks that no part of the original ROM is embedded in it.
- Third-party work keeps its authors' terms: the *Super Mario Bros. Two Players Hack* `.xdelta` patch is
  the work of Corpse Grinder and Ti.
- A license for the project's own code and documentation has not been chosen yet; until one is added,
  all rights to the new code are reserved by its author.

## Credits

- **Zvgelo (2026)** – Galaxian Coop (all new code and graphics changes), the tools, tests and
  documentation of this repository and the reproducible Mario build.
- **Corpse Grinder and Ti (2018)** – *Super Mario Bros. Two Players Hack*, the co-op engine of the Mario
  modification.
- *Galaxian* © Namco (arcade 1979, NES/Famicom 1984); *Super Mario Bros.* © Nintendo (1985).
