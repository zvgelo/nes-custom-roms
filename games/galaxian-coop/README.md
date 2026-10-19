# Galaxian Coop

## Overview

Galaxian Coop is a modification of *Galaxian* for the NES/Famicom (Namco, 1984) that lets **two players
fight at the same time** on one screen, inspired by Galaxian DX for the Commodore 64. The look and feel of
the original are kept; the mod adds a second ship, a shared progression system and a new title screen.

Two modes on the title screen:

- **1 PILOT** – one ship, with exactly the same rules as each pilot of the co-op game (RC6).
- **2 PILOTS CO-OP** – two ships, two controllers, separate scores and lives, plus life sharing.

Status: **in testing** (branch `game/galaxian-coop`, not merged into `main` yet). Everything below is
implemented and covered by the automatic emulator tests; play tests on real setups are listed in
[docs/TESTING.md](docs/TESTING.md).

## Features

### Rules shared by both modes (RC6: one set of rules for 1 PILOT and every co-op pilot)

| Mechanic | Rule |
|---|---|
| Start | `X3` (lives including the ship in play), `W1` |
| Firing | one new press of FIRE = one shot, while the pilot has a free shot (1–4 by weapon level); a held button never fires again; P1's shots bright green, P2's orange |
| W1 | 1 shot, 4.00 px/frame (100 %); at the start, and after a death while W2 was never unlocked |
| W2 | 2 shots, 4.40 px/frame (110 %); **free once per game for the first cleared stage 1** (also for a pilot exploding or waiting for its next ship; not for one hit on its last ship); otherwise 2000 boost points + a cleared stage |
| W3 | 3 shots, 4.80 px/frame (120 %); 4000 more boost points **counted from when W2 was given** + a cleared stage |
| W4 – Red Laser Overdrive | 4 lasers, 6.40 px/frame (160 %); see below |
| Death | back on W2 if W2 was ever unlocked, else W1; W3 progress, no-death points, a READY or running overdrive cancelled, shots removed; score, extra-life thresholds and the W2 unlock kept |
| Respawn shield | 4 s (240 frames) after every respawn: bullets and divers pass, the ship blinks (fast in the last second), moves and fires; none at a new game or a stage change without a death |
| Extra life | every 7000 points (7000, 14000, 21000 …), immediately, at most 9; doubled points count; the original one-time extra ship is off |
| Points | x2 for the pilot's own kills while its W4 runs (also towards extra lives and the hi score) |
| HUD | `Xn`, `Wn`, score, hi score; row above: `STG nn` (centre) and the pilot's overdrive field `W4 RDY` / `W4 12s` … `W4 01s` |

Measured full shot flights from the ship to the top: 50 / 46 / 42 / 32 frames. Boost points and no-death
points are separate from the score shown in the HUD. At most one level per cleared stage; points above a
threshold are not carried over.

**Red Laser Overdrive (RC6)**:

1. **READY** – on W3, 8000 points scored without dying (once per life): the overdrive is *ready*, not
   started. The pilot stays on W3 (x1 points, normal enemies, no countdown); `OVERDRIVE READY NEXT STAGE`
   (1P) / `P1 W4 READY NEXT STAGE` (co-op) for 2 s on the message line, `W4 RDY` above the pilot's HUD
   until the start.
2. **ACTIVE** – at the start of the next stage, in the first frame its formation is on screen (the game
   draws a new formation column by column in its first ~0.35 s of play): W4 for **12 seconds** (720 frames of play;
   pause and stage changes don't count), x2 points, the rising jingle, `OVERDRIVE!` (`P1 OVERDRIVE!` …)
   and the countdown `W4 12s`. In that same frame **three aliens break from the formation** and attack
   (their dives go for the overdrive pilot), and the enemies stay aggressive for the whole 12 s: about
   +60–80 % dive starts (one more solo diver allowed at a time), dives ~23 % faster, 3 of 4 dive targets
   on the overdrive pilot, one more shot per dive (the game's limit of 7 enemy shots stays).
3. **EXPIRED** – after 12 s: W3, x1, normal enemies (dives already flying finish normally; lasers in
   flight too). **CANCELLED** – a death before or during it; a revive by SELECT doesn't bring it back; a
   new game clears it.

### Co-op only

- **P2's ship**: controller 2, an orange-blue ship of its own shape (delta nose with a white cockpit,
  flat-topped pods and split tail fins; same size and hit boxes). The ships start side by side (P1 left,
  P2 right) and can pass through each other.
- **Separate lives and scores**; every bullet belongs to its pilot; enemy bullets and divers hit either
  ship. **Game Over** only when both pilots are out; a pilot left alone keeps playing.
- **Life sharing**: when one pilot is out (`X0`) and the other has at least `X2`, the other presses
  **SELECT** to give one ship: donor −1 life and +200 points (never doubled), receiver back with 1 life
  and a shield. A message on the top line says who can press SELECT.
- **Targets**: dives alternate between the two pilots; with one pilot in overdrive 3 of 4 dives and most
  enemy shots go for that pilot (P2: 7 of 8; P1: all, as the original aims at P1); with both in overdrive they are split between them (the aggression is
  the same as with one: two overdrives don't add up).
- **HUD**: `2UP` score, P2's `Xn`/`Wn` on the right, its overdrive field above `2UP`; the original stage
  flags don't fit (1 PILOT keeps them next to `STG nn`).

### Other

- **Title screen**: `1 PILOT` / `2 PILOTS CO-OP`, an animated `CO-OP` badge on the logo and the credit
  `HACK BY ZVGELO ©2026` below Namco's original credits.
- **Fixes of original glitches**: the row of white dashes on the top line and the `0` in the top-left corner
  (both present in the original ROM) are gone. RC6: the attract demo fires again (RC1–RC5's bullet engine
  had stopped it).

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
4. changes CHR: the two P2 ship tiles (P2's own ship, `P2_PIXELS`; checked: symmetric, same box as
   P1's), the laser tile, an `s` glyph for the countdown, a `!` glyph for `OVERDRIVE!`, and two blank logo
   cells moved to another blank tile; one palette byte (sprite palette 2, colour 3: green `$2A`);
5. checks the new RAM variables for overlaps, against the zero page the original uses and against
   `src/original_ram.txt` (RAM the original uses at run time, traced); checks that the cycle-counted
   routine and its tables each stay in one page and that no code blocks overlap;
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

- **Sprite limit**: the NES shows at most 8 sprites per scanline. P2's ship, the extra shots and diving
  enemies are sprites; when many of them share a line some may vanish for a frame (not seen in the
  automatic natural-play checks, see TESTING.md).
- **CPU budget**: with both pilots on W4 firing all the time, the game runs close to the NES's per-frame
  limit; to stay inside it, at most one bullet hit is processed per frame (a second hit in the same frame
  registers one frame later), P2's collision checks alternate between frames, diving enemies update
  their tilt at 30 Hz and the HUD is refreshed over 8 frames. Details and measurements:
  [docs/TESTING.md](docs/TESTING.md).
- **Purple aliens' details**: no sprite palette had a free colour for P1's green shots; 2 orange pixels
  of a diving purple alien are now green (the formation and the other aliens are unchanged).
- **P1's ship keeps its colours**: it is background drawn with the HUD palette (BG palette 0); a green
  accent would change the HUD or need another palette for the ship rows (whose colour 2 is blue, not
  white). The ships are told apart by P2's silhouette and the shot colours.
- When P1 loses a ship, new attack waves pause until P1 is back (original behaviour); P2's deaths do not
  pause the game. The overdrive's opening attack is skipped if P1 is hit at that very moment.
- The stage flags of the original HUD are not shown in co-op (no room; `STG nn` instead); 1 PILOT shows
  both (they always agree).
- Messages are red (the HUD palette has no yellow). The `W4 RDY` / `NEXT STAGE` wording is short because
  each HUD field has 6 cells and the message line 26.
- The overdrive's opening attack uses the game's own dives: the aliens fly their normal launch arc
  (~0.8 s) before they turn down at the pilot.
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

Automatic tests run the game in the cynes emulator and check RAM, OAM, nametables and the rendered
picture. `tests/test_fceumm.py` repeats the fire, weapon-parity, death and shot-origin/colour checks in the
FCEUmm core (the one RetroArch uses) through `pip install stable-retro`. `tests/test_trace.py` checks the
sound (APU writes) in a 6502 tracer (`tools/trace6502.py`), which also makes the RAM audit
(`tests/ram_audit.py`). Results,
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
