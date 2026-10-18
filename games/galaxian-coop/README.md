# Galaxian Coop

## Overview

Galaxian Coop is a modification of *Galaxian* for the NES/Famicom (Namco, 1984) that lets **two players
fight at the same time** on one screen, inspired by Galaxian DX for the Commodore 64. The look and feel of
the original are kept; the mod adds a second ship, a shared progression system and a new title screen.

Two modes on the title screen:

- **1 PILOT** – the original single-player game, with the new lives display, weapon boosts and extra lives.
- **2 PILOTS CO-OP** – two ships, two controllers, separate scores and lives, plus life sharing.

Status: **in testing** (branch `game/galaxian-coop`, not merged into `main` yet). Everything below is
implemented and covered by the automatic emulator tests; play tests on real setups are listed in
[docs/TESTING.md](docs/TESTING.md).

## Features

- **Simultaneous co-op**: P1 (controller 1) keeps the original ship, P2 (controller 2) flies an
  orange-blue ship. Both move and shoot independently and can pass through each other.
- **Independent shooting and scoring**: every bullet belongs to its pilot; points go to the owner.
  Enemy bullets and diving enemies can hit either ship; collisions are checked per ship.
- **Lives**: each pilot starts with 3. The HUD shows one ship icon and the number of lives left
  **including the ship in play** (`X3`, `X2`, `X1`, `X0`) – in both modes.
- **Game Over** only when both pilots are out; a pilot left alone keeps playing. In co-op the ships start
  side by side (P1 left, P2 right).
- **Life sharing (co-op)**: when one pilot is out (`X0`) and the other has at least `X2`, the other pilot
  presses **SELECT** to give one ship: the donor gets −1 life and +200 points, the receiver comes back with
  1 life. A message on the top of the screen says who can press SELECT.
- **Weapon boosts (both modes, per pilot)**:

  | Level | Bullets at once | Bullet speed (px/frame) | How to get it |
  |---|---|---|---|
  | W1 | 1 | 4.00 (100 %) | start, and after every death |
  | W2 | 2 | 4.40 (110 %) | 2000 boost points, then clear a stage; in co-op also free once, for clearing the first stage |
  | W3 | 3 | 4.80 (120 %) | W2 + 5000 more boost points, then clear a stage |
  | W4 – Red Laser | 4 | 6.40 (160 %) | W3 + 8000 points scored without dying; immediately, with a "GREAT SHOT" message |

  Measured full flights from the ship to the top: 49 / 45 / 41 / 31 frames. Boost points and no-death
  points are separate from the score shown in the HUD.

  At most one level per cleared stage; the free W2 in co-op only goes to pilots alive and in play when the
  stage is cleared. A death (or a revive by SELECT) sets the pilot back to W1, clears their boost and
  no-death points and removes their shots; the score and the other pilot's weapon are not touched. W4 shots are red
  lasers; damage is unchanged.
- **Respawn shield (co-op)**: after every respawn and after a revive by SELECT the ship is invulnerable for
  4 seconds (240 frames) and blinks – slowly for 3 s, fast in the last second. It can move and fire as
  usual; points count normally. The other pilot keeps its own state. Not in 1 PILOT.
- **Extra life every 7000 points** (7000, 14000, 21000, …) for each pilot, given immediately; the life-sharing
  bonus counts too. Lives are capped at 9 (one HUD digit).
- **HUD**: `1UP` / `2UP` scores, hi-score (P2 can beat it too), lives `Xn`, weapon level `Wn` per pilot.
- **Title screen**: `1 PILOT` / `2 PILOTS CO-OP`, an animated `CO-OP` badge on the logo and the credit
  `HACK BY ZVGELO ©2026` below Namco's original credits.
- **Fixes of original glitches**: the row of white dashes on the top line and the `0` in the top-left corner
  (both present in the original ROM) are gone.

## Required original ROM

| | |
|---|---|
| File | `Galaxian (Japan).nes` |
| Size | 16 400 bytes (16-byte header + 8 KiB PRG + 8 KiB CHR) |
| Header | NES 2.0, mapper 0 (NROM) |
| SHA-256 | `1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e` |
| CRC32 (whole file) | `8451DC60` |
| CRC32 (without header) | `084F61CD` |

```bash
sha256sum "Galaxian (Japan).nes"
```

The result is still mapper 0 (NROM-256, 32 KiB PRG + 8 KiB CHR, NES 2.0 header), so it runs in any NES
emulator.

## Method A – apply the BPS patch

`patches/Galaxian_Coop.bps` turns the original ROM into the finished game. The repository's own
`tools/bps.py` applies it (Python 3 only); any BPS tool (Flips, Rom Patcher JS, beat) works too.

```bash
python3 tools/bps.py apply "Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"
sha256sum "Galaxian Coop.nes"
```

The expected SHA-256 of the result is listed in [docs/CHANGELOG.md](docs/CHANGELOG.md) for each version.
The patch refuses a different source ROM (it checks the source CRC32) and checks the result.

## Method B – build from source

```bash
mkdir -p games/galaxian-coop/private
cp "Galaxian (Japan).nes" games/galaxian-coop/private/
python3 games/galaxian-coop/src/build.py
```

What `src/build.py` does:

1. reads `private/Galaxian (Japan).nes` (or the path you give as first argument) and checks its SHA-256;
2. assembles `src/asm/coop.asm` with `tools/asm6502.py` (a small two-pass 6502 assembler);
3. builds a 32 KiB PRG: new code in `$8000-$DFFF`, the original program unchanged at `$E000-$FFFF`
   except for small **hooks** (`.patch` blocks in `coop.asm`, e.g. `JSR` into the new code). For each hook
   the build checks that the original bytes are exactly what the source says before replacing them;
4. adds three CHR tiles (P2 ship, red laser) and moves two blank logo cells to another blank tile;
5. checks the new RAM variables for overlaps and that the cycle-counted routine stays in one page;
6. writes `build/Galaxian_Coop.nes` and `build/Galaxian_Coop.mlb` (Mesen 2 labels:
   new routines and RAM variables; Debugger → File → Import Labels).

Options: `-o FILE` (output path), `--bps` (also write `patches/Galaxian_Coop.bps`). It prints the SHA-256
of the result; any error stops with exit code 1 and nothing is overwritten.

## Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move left | D-pad Left | D-pad Left |
| Move right | D-pad Right | D-pad Right |
| Fire | A or B | A or B |
| Share a ship (co-op) | SELECT | SELECT |
| Pause | START | – |
| Title: choose mode / start | SELECT / START | – |

Each new press of FIRE fires one shot, as long as the pilot has a free shot (1–4 depending on the weapon
level); holding the button never fires again, and a press while all shots are flying does nothing. A button
held while the ship comes back must be released first.

**SELECT (life sharing)** works only in a co-op game, during normal play (not in pause, not between
stages), on a new press of the button. The pilot who presses it must be in play with at least `X2`, and the
other pilot must be out (`X0`). Holding SELECT never gives more than one ship; pressing it in any other
situation does nothing.

## Playing on emulators

1. **ROM folder.** RetroArch keeps ROMs in `Emulation/roms/nes/` inside the folder chosen during its setup –
   usually `~/Emulation/roms/nes/`, or `/run/media/<user>/<card>/Emulation/roms/nes/` on an SD card:
   ```bash
   find ~ /run/media -maxdepth 5 -type d -path '*Emulation/roms/nes' 2>/dev/null
   ```
2. **Copy the game:**
   ```bash
   cp games/galaxian-coop/build/Galaxian_Coop.nes ~/Emulation/roms/nes/
   ```
3. **Start it** from EmulationStation-DE (Game Mode: ES-DE shortcut; Desktop Mode: RetroArch → ES-DE). If it
   does not show up, let ES-DE rescan the ROM folder (recent versions: Main Menu → Utilities) or restart it.
4. **Emulator / core**: any NES core works (mapper 0) – FCEUmm, Mesen, Nestopia. In ES-DE: the game's menu →
   *Alternative emulator*.
5. **Port 1 / Port 2**: RetroArch Quick Menu (RetroArch hotkey) → Settings → Input → *Port 1 Controls* /
   *Port 2 Controls*: a different device for each. On a handheld PC the built-in controls are normally Port 1
   and an external pad Port 2; in Game Mode check the controller order in Steam.
6. **Test both controllers**: choose `2 PILOTS CO-OP`; both ships must move and fire separately.
7. **Player 2 does nothing**: assign a device to Port 2 (step 5), connect the second pad before starting the
   game, and make sure Steam did not merge both pads into one player.
8. **Does not start**: check the file's SHA-256 against the build output; try another core.

The game draws everything inside the visible area; no overscan setting is needed.

## Known limitations

- **Sprite limit**: the NES shows at most 8 sprites per scanline. P2's ship, the extra bullets and diving
  enemies are sprites; when many of them share a line (e.g. several divers low on the screen next to P2)
  some may flicker or vanish for a frame.
- **CPU budget**: with both pilots on W4 firing all the time, the game runs close to the NES's per-frame
  limit; to stay inside it, at most one bullet hit is processed per frame (a second hit in the same frame
  registers one frame later), P2's collision checks alternate between frames, and diving enemies update
  their tilt at 30 Hz. Details and measurements: [docs/TESTING.md](docs/TESTING.md).
- When P1 loses a ship, new attack waves pause until P1 is back (original behaviour); P2's deaths do not
  pause the game. In 1 PILOT there is no invulnerability after a respawn (as in the original).
- The stage flags of the original HUD are not shown in co-op (no room); 1 PILOT keeps them.
- Messages are red (the HUD palette has no yellow); `!` is not in the font.
- Stars: 13 instead of 24 (sprites were needed for P2 and the bullets).

## Troubleshooting

| Problem | What to do |
|---|---|
| `input is not Galaxian (Japan) [SHA-256 mismatch]` | Wrong dump/version (Galaxian (USA) or a headerless file are different). Use the ROM with the SHA-256 above. |
| `original ROM not found: …` | Copy the ROM to `games/galaxian-coop/private/` or pass its path: `build.py PATH/rom.nes`. |
| BPS: `source ROM CRC mismatch` / `patch CRC mismatch` | Wrong source ROM, or the `.bps` file is damaged – restore it with `git checkout -- games/galaxian-coop/patches`. |
| `.patch $XXXX: original bytes … != …` | The source ROM is not the expected one, or `coop.asm` was edited inconsistently. |
| `assembler: line N: …` | An error in `src/asm/coop.asm` (only after own edits). |
| Different output hash | The build is deterministic; check the input hash and `git status` for local changes. |
| No file in `build/` | The build stopped with an error – read its last line. |
| `ModuleNotFoundError` | Run with `python3` from inside the repository and keep `tools/` next to `games/`. Emulator tests also need `pip install -r games/galaxian-coop/tests/requirements.txt`. |
| Black screen | Should not happen with a mapper-0 core; re-check the ROM hash and try another core. |
| Player 2 not working | See step 7 above; P2 must use controller **2**. |

## Testing

```bash
python3 games/galaxian-coop/tests/test_coop.py -v
pip install -r games/galaxian-coop/tests/requirements.txt   # for the emulator tests (cynes)
```

Automatic tests run the game in the cynes emulator and check RAM, OAM and the rendered picture.
`tests/test_fceumm.py` repeats the fire, weapon-parity and death checks in the FCEUmm core (the one
RetroArch uses) through `pip install stable-retro`. Results,
performance measurements and the manual test lists for Mesen 2, RetroArch are in
[docs/TESTING.md](docs/TESTING.md).

## Documentation

- [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md) – how the original game works, all hooks
- [docs/MEMORY_MAP.md](docs/MEMORY_MAP.md) – RAM, ROM, OAM and CHR use
- [docs/CHANGELOG.md](docs/CHANGELOG.md) – versions and output checksums
- [docs/TESTING.md](docs/TESTING.md) – tests and results
- [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) – implementation report (Polish)

## Credits

- *Galaxian* © Namco (arcade 1979, NES/Famicom 1984). The original credits stay on the title screen.
- **Galaxian Coop – Zvgelo (2026)**: all new code, graphics changes, tools, tests and documentation. No
  other hacks are used.
