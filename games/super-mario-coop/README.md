**English** | [Polski](README_PL.md)

# Super Mario Bros. Two Players Hack – build kit

Mario and Luigi on screen **at the same time**, each controlled from their own controller. The game is
the **Super Mario Bros. Two Players Hack by Corpse Grinder and Ti (2018)**. This folder only helps you
build it reproducibly from your own *Super Mario Bros.* ROM and the hack's original patch, which you
download from the authors' release – it is not included here (see
[Original Hack Credits & Copyright](#original-hack-credits--copyright)).

<p align="center">
  <img src="assets/screenshots/01-title.png" width="480" alt="Title screen of the Two Players Hack: ©1985 NINTENDO, ©2018 CORPSE GRINDER & TI, 2 PLAYERS GAME selected">
</p>

<p align="center">
  <a href="#who-made-what">Who made what</a> ·
  <a href="#screenshots">Screenshots</a> ·
  <a href="#getting-the-game">Getting the game</a> ·
  <a href="#controls">Controls</a> ·
  <a href="#running-it-in-an-emulator">Emulators</a> ·
  <a href="#limitations">Limitations</a> ·
  <a href="#original-hack-credits--copyright">Credits &amp; copyright</a>
</p>

## Who made what

> **Super Mario Bros. – Two Players Hack. Original hack by Corpse Grinder & Ti (2018).**
> The game, its simultaneous co-op and its patch are their work, and their names stay on the title screen
> (`©2018 CORPSE GRINDER & TI`). This project does not modify the hack and adds no branding to it.

| | Two Players Hack (Corpse Grinder and Ti, 2018) | This folder (Zvgelo, 2026, MIT) |
|---|---|---|
| Co-op engine: Luigi on screen with Mario, second controller | ✔ | – |
| The `.xdelta` patch | ✔ (not included here – download it from the authors' release) | – |
| One-command build with SHA-256 checks, pure-Python xdelta/VCDIFF decoder, tests, documentation | – | ✔ |

The ROM built here is byte for byte the Two Players Hack (SHA-256 `e962eee2…`), the same result as
applying the patch with `xdelta3`.

## Screenshots

| Level 1-1, both players | Moving independently |
|---|---|
| ![Mario and Luigi side by side at the start of level 1-1](assets/screenshots/02-two-players-start.png) | ![Mario and Luigi apart in level 1-1, each moved by its own controller](assets/screenshots/03-two-players-run.png) |

Frames of the built ROM in the FCEUmm core (through `stable-retro`), driven by two virtual controllers,
×3 without filtering. The graphics are Nintendo's and the hack authors' (see
[THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md)).

## Getting the game

You need two files that this repository does **not** contain, and Python 3 (tested with 3.14 on Linux).
Commands are run from the repository root.

| Input | |
|---|---|
| Your own ROM | `Super Mario Bros. (World).nes`, 40 976 bytes, iNES 1.0, mapper 0 |
| its SHA-256 | `f61548fdf1670cffefcc4f0b7bdcdd9eaba0c226e3b74f8666071496988248de` |
| its CRC32 | `3337EC46` (whole file), `D445F698` (without header) |
| The hack's patch | `Super Mario Bros. (Two Players Hack).xdelta`, 19 395 bytes, from the authors' release: the [Emu-Land thread](https://www.emu-land.net/forum/index.php?topic=81090.0) by Ti_ (2018-10-13), attachment `Super Mario Bros. (Two Players Hack).7z` |
| its SHA-256 | `d38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd` |

The result is a **mapper 24 (Konami VRC6a)** ROM (64 KiB PRG, 8 KiB CHR), as the hack's header says.

**A – one command (recommended)**

```bash
mkdir -p games/super-mario-coop/private
cp "Super Mario Bros. (World).nes" games/super-mario-coop/private/original.nes
cp "Super Mario Bros. (Two Players Hack).xdelta" games/super-mario-coop/private/
python3 games/super-mario-coop/src/build.py
sha256sum "games/super-mario-coop/build/Super Mario Bros. (Two Players Hack).nes"
# e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4
```

`src/build.py` checks the original and the patch, applies the patch with `tools/vcdiff.py` (or the
`xdelta3` program with `--xdelta3` – same bytes) and checks the result. Options: `--patch FILE` (patch in
another place), `-o FILE`. Without the patch it stops and says where to get it; a patch with another
SHA-256 is refused. Any failed check stops with exit code 1; the inputs are never written. Both input
locations are ignored by git (`private/`, `*.xdelta`).

**B – any xdelta tool**

```bash
xdelta3 -d -s "Super Mario Bros. (World).nes" "Super Mario Bros. (Two Players Hack).xdelta" \
    "Super Mario Bros. (Two Players Hack).nes"
# or, without xdelta3:
python3 tools/vcdiff.py "Super Mario Bros. (World).nes" "Super Mario Bros. (Two Players Hack).xdelta" \
    "Super Mario Bros. (Two Players Hack).nes"
sha256sum "Super Mario Bros. (Two Players Hack).nes"
# e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4
```

## Controls

| | Controller 1 | Controller 2 |
|---|---|---|
| Character | Mario | Luigi |
| Move | D-pad | D-pad |
| Jump / swim | A | A |
| Run / fireball | B | B |
| Pause | START | – |

On the title screen SELECT (controller 1) chooses **1 PLAYER GAME** or **2 PLAYERS GAME**; START starts.
Choose **2 PLAYERS GAME** for co-op.

## Running it in an emulator

The ROM needs an emulator with **mapper 24** support, for example FCEUmm (standalone or as a RetroArch
core), Mesen 2, Nestopia or FCEUX. Assign a different input device to player 1 and player 2 (RetroArch:
Settings → Input → *Port 1 Controls* / *Port 2 Controls*) and connect both controllers before starting.

## Limitations

- Tested only in the FCEUmm core through `stable-retro` (title screen and both controllers, see
  [docs/TESTING.md](docs/TESTING.md)). Not tested: RetroArch itself, Mesen 2, other emulators, real
  hardware, sound, collisions between the players, deaths and level restarts, later levels.
- The co-op behaviour is entirely the Two Players Hack's; questions about it belong to its authors.
- An emulator without mapper 24 shows a black screen or broken graphics.

## Troubleshooting

| Problem | What to do |
|---|---|
| `input is not Super Mario Bros. (World) [SHA-256 mismatch]` | Wrong dump or version – use the ROM with the SHA-256 above. |
| `original ROM not found: …` | Copy your ROM to `games/super-mario-coop/private/original.nes` or pass its path: `build.py PATH/rom.nes`. |
| `patch not found: …` | Download the authors' release, put the `.xdelta` in `games/super-mario-coop/private/` or pass `--patch PATH`. |
| `….xdelta: unexpected SHA-256` | A changed or damaged file, or a different release – use the unmodified patch with the SHA-256 above. |
| `xdelta3 not found` | Only with `--xdelta3`: install `xdelta3` or drop the option. |
| Black screen, wrong graphics | The emulator lacks mapper 24 – use another one. |
| Player 2 does nothing | Assign a device to port 2 and connect the second controller before starting. |

## Tests

```bash
pip install -r games/super-mario-coop/tests/requirements.txt    # stable-retro, numpy (emulator tests)
python3 games/super-mario-coop/tests/test_build.py -v           # all 16: 14 file/build + 2 emulator tests
python3 games/super-mario-coop/tests/test_emulator.py -v        # only the 2 emulator tests (FCEUmm core)
```

The ROM tests need the original ROM and the patch in `private/` (or their paths in `SMB_ORIGINAL` and
`SMB_XDELTA`); without them only the 4 file tests run. Results: [docs/TESTING.md](docs/TESTING.md). History: [docs/CHANGELOG.md](docs/CHANGELOG.md).

## Original Hack Credits & Copyright

*Super Mario Bros. – Two Players Hack* was created by **Corpse Grinder and Ti (2018)**.

This repository is not the original creator of the hack and does not claim authorship of its cooperative
gameplay, original modifications, or patch.

The patch is **not distributed** with this repository. It is attributed to its original creators and
available from their own release ([Emu-Land thread](https://www.emu-land.net/forum/index.php?topic=81090.0)); this repository only records its SHA-256
(`d38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd`) and applies it locally. The patch is **not** covered by the [MIT License](../../LICENSE), and no
license or redistribution permission from the original creators is claimed or implied.

*Super Mario Bros.* and its original assets remain the intellectual property of their respective rights
holders (© Nintendo, 1985). This is an unofficial fan project and is not affiliated with or endorsed by
Nintendo. No ROM is included.

Copyright holders with concerns regarding material in this repository may contact the repository maintainer
through GitHub, for example by opening an issue in this repository. Justified requests will be reviewed.

**This repository's own part – Zvgelo (2026)**: the build script, VCDIFF decoder, tests and
documentation, under the [MIT License](../../LICENSE). Details:
[THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md).
