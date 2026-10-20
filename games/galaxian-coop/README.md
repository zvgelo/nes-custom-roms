# Galaxian Coop

A modification of *Galaxian* for the NES/Famicom (Namco, 1984) that lets **two players fight at the same
time** on one screen, inspired by Galaxian DX for the Commodore 64. The original look and feel are kept;
the mod adds a second ship, weapon levels with a timed Red Laser Overdrive, a respawn shield, life sharing,
extra lives, a stage counter and a new title screen. The same rules apply in 1-player mode.

![Two pilots fighting the formation together](assets/screenshots/03-coop-gameplay.png)

- **1 PILOT** – one ship, with exactly the same rules as each pilot of the co-op game.
- **2 PILOTS CO-OP** – two ships, two controllers, separate scores and lives, plus life sharing.

Status: release candidate 6 (RC6). Everything below is implemented and covered by automatic emulator
tests ([docs/TESTING.md](docs/TESTING.md)).

## Screenshots

| Title screen | One pilot |
|---|---|
| ![Title screen with the 1 PILOT and 2 PILOTS CO-OP choices](assets/screenshots/01-title.png) | ![1 PILOT game: one ship, stage counter STG 01](assets/screenshots/02-single-player.png) |
| **Weapon boost: W2 for both after stage 1** | **Overdrive READY, starts with the next stage** |
| ![Stage 2: both pilots on W2 with two shots each](assets/screenshots/04-weapon-boost.png) | ![P1 W4 READY NEXT STAGE on the message line and W4 RDY above P1's score](assets/screenshots/05-overdrive-ready.png) |
| **Overdrive active: the new formation counter-attacks** | **Life sharing prompt** |
| ![P1 OVERDRIVE!, W4 12s countdown and three aliens breaking from the new formation](assets/screenshots/06-overdrive-active.png) | ![P1 is out: P2 SELECT TO REVIVE P1](assets/screenshots/07-life-sharing.png) |

More: [both pilots in overdrive – P1's green and P2's orange lasers](assets/screenshots/08-player-colors.png).
All screenshots are frames of the current ROM running in the cynes emulator, scaled ×3 without filtering;
the progress shown (scores, lives, stage, weapon levels) is reachable in normal play.

## Rules

### Weapon levels

| Level | Shots at once | Shot speed | How to get it |
|---|---|---|---|
| W1 | 1 | 4.00 px/frame (100 %) | at the start; after a death if W2 was never unlocked |
| W2 | 2 | 4.40 px/frame (110 %) | **free, once per game, for clearing the first stage**; otherwise 2000 boost points and then a cleared stage |
| W3 | 3 | 4.80 px/frame (120 %) | 4000 more boost points counted from when W2 was given, then a cleared stage |
| W4 – Red Laser Overdrive | 4 lasers | 6.40 px/frame (160 %) | see below |

- One new press of FIRE fires one shot, while the pilot has a free shot; holding the button never fires
  again. A button held while the ship comes back must be released first.
- Boost points are the points the pilot scores; they restart when a level is given (no surplus is
  carried over). A cleared stage gives at most one level.
- The free W2 also goes to a pilot who is exploding or waiting for its next ship when the stage is
  cleared (it comes back with W2); a pilot hit on its last ship gets none.
- **Once W2 is unlocked it is kept**: a death brings the pilot back on W2 (W1 if W2 was never unlocked).
  W3 progress, the points since the last death and the overdrive are reset; the score and the extra-life
  thresholds are kept.

### Red Laser Overdrive (W4)

1. **READY** – on W3, after scoring 8000 points without dying (once per life). Nothing changes yet: the
   pilot keeps W3, normal points and normal enemies. The message line shows `OVERDRIVE READY NEXT STAGE`
   (1 PILOT) or `P1 W4 READY NEXT STAGE` (co-op) for two seconds; `W4 RDY` stays above the pilot's score.
2. **NEXT STAGE** – the overdrive starts with the next stage, in the first frame its formation is on
   screen (the game draws a new formation column by column during the first ~0.35 s of play). In that
   frame:
   - the pilot gets 4 red lasers at 160 % speed with their own zap sound, and a rising jingle plays;
   - **SCORE ×2** for the pilot's own kills (the doubled points count towards extra lives and the hi
     score);
   - `OVERDRIVE!` (`P1 OVERDRIVE!`, `P2 OVERDRIVE!`, `P1 P2 OVERDRIVE!`) and the countdown `W4 12s`;
   - **the counter-attack**: three aliens break from the formation at once and dive at the overdrive
     pilot, and the enemies stay aggressive for the whole overdrive – about 60–80 % more dive starts (one
     more diver allowed at a time), dives about 23 % faster, three of four dive targets and most enemy
     shots aimed at the overdrive pilot, one more shot per dive.
3. **12 seconds** of play later (pause and stage changes don't count) the pilot is back on W3 with ×1
   points and the enemies return to normal; lasers already flying finish their flight.

A death cancels a READY or running overdrive (a revive by SELECT does not bring it back). With two pilots
each has its own READY, countdown and once-per-life use; both may start in the same stage, and then the
attacks are split between them (two overdrives do not add up).

### Lives, shield and stages

- Each pilot starts with `X3` (lives including the ship in play).
- **Extra life** every 7000 points (7000, 14000, 21000 …), immediately, up to 9.
- **Respawn shield**: after every respawn (and after a revive by SELECT) the ship is invulnerable for
  4 seconds and blinks – slowly for 3 s, fast in the last second. It can move and fire. There is no
  shield at the start of a game or after a stage change without a death.
- **Stage counter** `STG 01`, `STG 02` … above the hi score in both modes (1 PILOT also keeps the
  original stage flags on the right).
- **Game over** in co-op only when both pilots are out; a pilot left alone keeps playing.

### Co-op only

- **Two ships**: P1 (controller 1) flies the original ship (red dome, white and cyan pods) and fires
  **bright green** shots; P2 (controller 2) flies its own orange-and-blue ship (delta nose, white
  cockpit) and fires **orange** shots. Same size and hit boxes; the ships can pass through each other.
- Separate scores and lives; every shot's points go to its pilot; enemy shots and divers can hit either
  ship. Dives alternate between the two pilots.
- **Life sharing**: when one pilot is out (`X0`) and the other is in play with at least `X2`, the other
  pilot presses **SELECT** to give one ship: the donor gets −1 life and +200 points, the receiver comes
  back with 1 life and the respawn shield. The message line says who can press SELECT.

## Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move left / right | D-pad Left / Right | D-pad Left / Right |
| Fire | A or B | A or B |
| Share a ship (co-op) | SELECT | SELECT |
| Pause | START | – |
| Title: choose mode / start | SELECT / START | – |

SELECT shares a ship only in a co-op game during normal play (not in pause, not between stages), on a new
press of the button, when the rule above allows it; otherwise it does nothing.

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

Galaxian (USA) and headerless dumps are different files and are refused. The result is still mapper 0
(NROM-256, 32 KiB PRG + 8 KiB CHR, NES 2.0 header).

## Installation

All commands are run from the repository root, with Python 3 (tested with Python 3.14 on Linux).

### Method A – apply the BPS patch

`patches/Galaxian_Coop.bps` turns the original ROM into the finished game. The repository's own
`tools/bps.py` applies it; any BPS tool (Flips, Rom Patcher JS, beat) works too.

```bash
python3 tools/bps.py apply "Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"
sha256sum "Galaxian Coop.nes"
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

The patch refuses a different source ROM (it checks the source CRC32) and checks the result. The expected
SHA-256 of each version is listed in [docs/CHANGELOG.md](docs/CHANGELOG.md).

### Method B – build from source

```bash
mkdir -p games/galaxian-coop/private
cp "Galaxian (Japan).nes" games/galaxian-coop/private/
python3 games/galaxian-coop/src/build.py
sha256sum games/galaxian-coop/build/Galaxian_Coop.nes
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

What `src/build.py` does:

1. reads `private/Galaxian (Japan).nes` (or the path you give as first argument) and checks its SHA-256;
2. assembles `src/asm/coop.asm` with `tools/asm6502.py` (a small two-pass 6502 assembler);
3. builds a 32 KiB PRG: new code in `$8000-$DFFF`, the original program unchanged at `$E000-$FFFF`
   except for small **hooks** (`.patch` blocks in `coop.asm`, e.g. `JSR` into the new code). For each hook
   the build checks that the original bytes are exactly what the source says before replacing them;
4. changes CHR: P2's ship tiles, the laser tile, the `s` and `!` glyphs of the HUD messages, two blank
   logo cells; and one palette byte (P1's green shots);
5. checks the new RAM variables for overlaps, against the zero page the original uses and against
   `src/original_ram.txt` (RAM the original uses at run time, traced); checks that the cycle-counted
   routine and its tables each stay in one page and that no code blocks overlap;
6. writes `build/Galaxian_Coop.nes` and `build/Galaxian_Coop.mlb` (Mesen 2 debugger labels; Debugger →
   File → Import Labels).

Options: `-o FILE` (output path), `--bps` (also write `patches/Galaxian_Coop.bps`). It prints the SHA-256
of the result; any error stops with exit code 1 and nothing is overwritten. Two builds give identical
bytes.

## Running it in an emulator

Load `Galaxian_Coop.nes` (or your patched file) in any NES emulator – the game uses mapper 0, which every
emulator supports: e.g. Mesen 2, FCEUmm (standalone or as a RetroArch core), Nestopia, FCEUX.

For **2 PILOTS CO-OP** assign a different input device to player 1 and player 2 (in RetroArch: Settings →
Input → *Port 1 Controls* / *Port 2 Controls*), connect both controllers before starting the game, and
check that both ships move separately. If player 2 does nothing, port 2 has no device assigned or both
controllers were given to one player.

Automatic tests ran in the cynes emulator, the FCEUmm core (through `stable-retro`) and a 6502 tracer;
manual play testing was done in an emulator. Mesen 2, other emulators and real NES/Famicom hardware
were not tested – see [docs/TESTING.md](docs/TESTING.md).

## Testing

```bash
pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
python3 games/galaxian-coop/tests/test_coop.py -v           # 112 tests (cynes)
python3 games/galaxian-coop/tests/test_trace.py -v          # 5 tests (sound, RAM; no extra packages)
pip install stable-retro
python3 games/galaxian-coop/tests/test_fceumm.py -v         # 8 tests (FCEUmm core)
```

The tests need the original ROM in `games/galaxian-coop/private/` (or `GALAXIAN_ROM=path`); without
it, or without an emulator package, the affected tests are skipped. They check RAM, OAM, nametables and
the rendered picture: the rules above, both modes side by side, HUD contents, CPU margin under stress,
sounds. Results and measurements: [docs/TESTING.md](docs/TESTING.md).

## Known limitations

- **Sprite limit**: the NES shows at most 8 sprites per scanline. P2's ship, the extra shots and diving
  enemies are sprites; when many share a line some may vanish for a frame (not seen in the automatic
  natural-play checks).
- **CPU budget**: with both pilots in overdrive the game runs close to the NES's per-frame limit; to stay
  inside it, at most one bullet hit is processed per frame (a second hit registers one frame later),
  P2's collision checks alternate between frames, diving enemies update their tilt at 30 Hz and the HUD
  is refreshed over a few frames. No slowdown frames were measured (see TESTING.md).
- **Purple aliens' details**: no sprite palette had a free colour for P1's green shots; 2 pixels of a
  diving purple alien are green instead of orange.
- **P1's ship keeps its colours**: it is background drawn with the HUD palette; the ships are told apart
  by P2's silhouette and the shot colours.
- When P1 loses a ship, new attack waves pause until P1 is back (original behaviour); P2's deaths do not
  pause the game. The overdrive's opening attack is skipped if P1 is hit at that very moment.
- The overdrive's opening attack uses the game's own dives: the aliens fly their normal launch arc
  (~0.8 s) before they turn down at the pilot. The countdown field follows the `OVERDRIVE!` message by
  a frame, the `Wn` digit by a few frames.
- Messages are red (the HUD palette has no yellow) and short: each HUD field has 6 cells, the message
  line 26.
- Stars: 13 instead of 24 (sprites were needed for P2 and the shots).

## Troubleshooting

| Problem | What to do |
|---|---|
| `input is not Galaxian (Japan) [SHA-256 mismatch]` | Wrong dump or version. Use the ROM with the SHA-256 above. |
| `original ROM not found: …` | Copy the ROM to `games/galaxian-coop/private/` or pass its path: `build.py PATH/rom.nes`. |
| BPS: `source ROM CRC mismatch` / `patch CRC mismatch` | Wrong source ROM, or the `.bps` file is damaged – restore it with `git checkout -- games/galaxian-coop/patches`. |
| `.patch $XXXX: original bytes … != …` | The source ROM is not the expected one, or `coop.asm` was edited inconsistently. |
| `assembler: line N: …` | An error in `src/asm/coop.asm` (only after your own edits). |
| Different output hash | The build is deterministic; check the input hash and `git status` for local changes. |
| No file in `build/` | The build stopped with an error – read its last line. |
| `ModuleNotFoundError` | Run with `python3` from inside the repository and keep `tools/` next to `games/`. |
| Player 2 does nothing | Assign a device to port 2 (see above); P2 uses controller **2**. |

## Documentation

- [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md) – how the original game works, all hooks
- [docs/MEMORY_MAP.md](docs/MEMORY_MAP.md) – RAM, ROM, OAM and CHR use
- [docs/CHANGELOG.md](docs/CHANGELOG.md) – versions and output checksums
- [docs/TESTING.md](docs/TESTING.md) – tests, results and measurements
- [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) – development report per release
  candidate (Polish, historical: the rules of RC1–RC5 described there are superseded by RC6 and this
  README)

## Credits

- *Galaxian* © Namco (arcade 1979, NES/Famicom 1984). The original credits stay on the title screen.
  This is an unofficial fan modification, not affiliated with or endorsed by Bandai Namco.
- **Galaxian Coop – Zvgelo (2026)**: all new code, graphics changes, tools, tests and documentation. No
  other hacks are used.
