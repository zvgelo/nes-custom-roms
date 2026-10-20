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

| Galaxian Coop | [Super Mario Bros. Two Players Hack – build kit](games/super-mario-coop/README.md) |
|---|---|
| *Code, screenshots and README on branch `game/galaxian-coop`.* | ![Two Players Hack: Mario and Luigi apart in level 1-1](games/super-mario-coop/assets/screenshots/03-two-players-run.png) |
| New co-op engine for *Galaxian* (Japan) by Zvgelo: a second ship, weapon levels, a 12-second Red Laser Overdrive with an enemy counter-attack, respawn shield, life sharing. Same rules for one pilot. | One-command, checksum-verified build of the *Super Mario Bros. Two Players Hack* – **the hack is by Corpse Grinder and Ti (2018)**; its patch comes from the authors' own release (not included here) and the ROM is left unmodified. |
| Mapper 0 · BPS patch included · RC6 | Mapper 24 (VRC6a) · the hack's `.xdelta` from its authors |

Each project is developed on its own branch (`game/galaxian-coop`, `game/super-mario-coop`); this branch
contains only the Mario build kit. Each README has the controls, screenshots and troubleshooting.

## Highlights

- **Two players at once** on one screen, each with their own controller.
- **Standard emulators**: the ROM is patched, not the emulator; the result is an ordinary mapper-24 NES
  file.
- **Reproducible builds**: every input and output is checked by SHA-256; two builds give the same bytes.
- **No dependencies**: a pure-Python xdelta/VCDIFF decoder applies the hack's patch (`xdelta3` optional).
- **Tested in an emulator**: the FCEUmm core through `stable-retro` – see
  [docs/TESTING.md](games/super-mario-coop/docs/TESTING.md).

## Quick start

Build the Two Players Hack from your ROM and the hack's patch from its authors (Python 3, from the repository root):

```bash
mkdir -p games/super-mario-coop/private
cp "Super Mario Bros. (World).nes" games/super-mario-coop/private/original.nes
cp "Super Mario Bros. (Two Players Hack).xdelta" games/super-mario-coop/private/
python3 games/super-mario-coop/src/build.py
sha256sum "games/super-mario-coop/build/Super Mario Bros. (Two Players Hack).nes"
# e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4
```

The patch is not included: download it from the authors' release ([Emu-Land thread](https://www.emu-land.net/forum/index.php?topic=81090.0),
attachment `Super Mario Bros. (Two Players Hack).7z`). Open the result in an NES emulator with mapper 24
support. Checksums and other patching tools: [README](games/super-mario-coop/README.md#getting-the-game).

## Build & testing

```bash
pip install -r games/super-mario-coop/tests/requirements.txt    # stable-retro, numpy (emulator tests)
python3 games/super-mario-coop/tests/test_build.py -v           # 16 tests, two of them in the FCEUmm core
```

Building needs only Python 3 (tested with 3.14 on Linux). Results:
[games/super-mario-coop/docs/TESTING.md](games/super-mario-coop/docs/TESTING.md) – all passing.

## Project structure

```text
nes-custom-roms/
├── README.md               this page (Polish: README_PL.md)
├── LICENSE                 MIT License – the project's own work
├── THIRD_PARTY_NOTICES.md  what the MIT License does not cover
├── assets/readme/          README artwork
├── tools/                  shared tools (on this branch: the VCDIFF decoder)
└── games/
    └── <game>/
        ├── README.md       rules, installation, controls, screenshots (+ README_PL.md)
        ├── assets/         screenshots (and README artwork)
        ├── src/            source code and build.py
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
