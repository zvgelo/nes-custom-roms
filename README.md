**English** | [Polski](README_PL.md)

<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="NES Custom ROMs – two-player co-op for classic NES games, built from your own ROM">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-NES%20%2F%20Famicom-b71c1c" alt="Platform: NES / Famicom">
  <img src="https://img.shields.io/badge/build-Python%203-3776ab" alt="Build: Python 3">
  <img src="https://img.shields.io/badge/distribution-no%20ROMs-555555" alt="Distribution: no ROMs">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT%20(own%20code)-2e7d32" alt="License: MIT for the project's own code"></a>
</p>

<p align="center">
  <a href="#games">Games</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#build--testing">Build &amp; testing</a> ·
  <a href="#project-structure">Project structure</a> ·
  <a href="#legal--credits">Legal &amp; credits</a>
</p>

**NES Custom ROMs** collects unofficial projects that let **two players play classic NES/Famicom games at
the same time**: an original co-op modification of *Galaxian* and a reproducible build of an existing
*Super Mario Bros.* co-op hack. The repository contains source code, build scripts, tests and the
project's own patches – never the games themselves or third-party patches. You build from your own, legally obtained ROM.

## Games

| [Galaxian Coop](games/galaxian-coop/README.md) | Super Mario Bros. Two Players Hack – build kit |
|---|---|
| ![Galaxian Coop: two pilots fighting the formation together](games/galaxian-coop/assets/screenshots/03-coop-gameplay.png) | *Code, screenshots and README on branch `game/super-mario-coop`.* |
| New co-op engine for *Galaxian* (Japan) by Zvgelo: a second ship, weapon levels, a 12-second Red Laser Overdrive with an enemy counter-attack, respawn shield, life sharing. Same rules for one pilot. | One-command, checksum-verified build of the *Super Mario Bros. Two Players Hack* – **the hack is by Corpse Grinder and Ti (2018)**; its patch comes from the authors' own release (not included here) and the ROM is left unmodified. |
| Mapper 0 · BPS patch included · RC6 | Mapper 24 (VRC6a) · the hack's `.xdelta` from its authors |

Each project is developed on its own branch (`game/galaxian-coop`, `game/super-mario-coop`); this branch
contains Galaxian Coop. Each README has the rules or controls, screenshots and troubleshooting.

## Highlights

- **Two players at once** on one screen, each with their own controller.
- **Standard emulators**: the ROM is patched, not the emulator; the results are ordinary mapper-0 and
  mapper-24 NES files.
- **Reproducible builds**: every input and output is checked by SHA-256; two builds give the same bytes.
- **Patches without game data**: the Galaxian BPS patch reads the original data from your ROM; a test
  checks that no part of the original is stored in it.
- **Tested in emulators**: cynes, the FCEUmm core and a 6502 tracer (sound, RAM) – see
  [docs/TESTING.md](games/galaxian-coop/docs/TESTING.md).

## Quick start

Apply the Galaxian Coop patch to your ROM (Python 3, from the repository root):

```bash
git switch game/galaxian-coop
sha256sum "Galaxian (Japan).nes"
# 1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e
python3 tools/bps.py apply "Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"
sha256sum "Galaxian Coop.nes"
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

Open `Galaxian Coop.nes` in any NES emulator. Any other BPS tool (Flips, Rom Patcher JS, beat) works too.
For the Mario Two Players Hack, switch to branch `game/super-mario-coop` and follow its README.

## Build & testing

```bash
python3 games/galaxian-coop/src/build.py        # needs games/galaxian-coop/private/Galaxian (Japan).nes
```

The output goes to `games/galaxian-coop/build/`; the build prints the SHA-256 of the result and refuses
wrong inputs. Tests and their latest results: [docs/TESTING.md](games/galaxian-coop/docs/TESTING.md)
(cynes 112, FCEUmm 8, tracer 5 – all passing). Building needs only Python 3 (tested with 3.14 on Linux);
the emulator tests need the packages in `games/galaxian-coop/tests/requirements.txt` and, for the FCEUmm
suite, `stable-retro`.

## Project structure

```text
nes-custom-roms/
├── README.md               this page (Polish: README_PL.md)
├── LICENSE                 MIT License – the project's own work
├── THIRD_PARTY_NOTICES.md  what the MIT License does not cover
├── assets/readme/          README artwork
├── tools/                  shared tools: 6502 assembler, BPS patcher, VCDIFF decoder,
│                           emulator test helpers, 6502 tracer
└── games/
    └── <game>/
        ├── README.md       rules, installation, controls, screenshots (+ README_PL.md)
        ├── assets/         screenshots (and README artwork)
        ├── src/            source code and build.py
        ├── patches/        own patches only (Galaxian BPS) – no original game data
        ├── docs/           CHANGELOG, TESTING and technical documentation
        ├── tests/          automatic tests
        ├── private/        your original ROMs, the Mario hack's patch (ignored by git)
        └── build/          generated ROMs and outputs                 (ignored by git)
```

## Legal & credits

- **License**: the project's own code, tools, tests, documentation and artwork are released under the
  [MIT License](LICENSE) © 2026 Zvgelo. It does **not** cover the original games, ROMs or their assets,
  the Super Mario Bros. Two Players Hack or its original patch (not distributed here), or other
  third-party material – see
  [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
- **Unofficial fan project.** Not affiliated with, endorsed by or sponsored by Bandai Namco, Nintendo or
  the authors of the Two Players Hack. *Galaxian* © Namco (1979, NES/Famicom 1984); *Super Mario Bros.* ©
  Nintendo (1985). Game names and trademarks belong to their owners.
- **No ROMs** – original or modified – are included or linked; `*.nes`, `private/` and `build/` are
  excluded by `.gitignore`. You need your own, legally obtained copy of each original game.
- **Credits**: *Super Mario Bros. – Two Players Hack*: original hack by **Corpse Grinder & Ti** (2018).
  *Galaxian Coop*, the tools, tests and documentation: **Zvgelo** (2026).
