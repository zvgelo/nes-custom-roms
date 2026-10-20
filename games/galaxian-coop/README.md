**English** | [Polski](README_PL.md)

<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="Galaxian Coop – two pilots, one formation, at the same time; weapon levels W1 to W4">
</p>

<p align="center">
  <a href="#screenshots">Screenshots</a> ·
  <a href="#rules">Rules</a> ·
  <a href="#controls">Controls</a> ·
  <a href="#installation">Installation</a> ·
  <a href="#running-it-in-an-emulator">Emulators</a> ·
  <a href="#known-limitations">Limitations</a> ·
  <a href="#documentation">Docs</a>
</p>

**Galaxian Coop** is an unofficial modification of *Galaxian* (Namco, NES/Famicom 1984) that lets **two
players fight the alien formation at the same time** – inspired by Galaxian DX for the Commodore 64. The
original look and feel stay; the mod adds a second ship, weapon levels with a timed **Red Laser
Overdrive**, a respawn shield, life sharing, extra lives and a stage counter. **1 PILOT** plays by exactly
the same rules as each pilot of **2 PILOTS CO-OP**.

Status: release candidate 6 (RC6) · mapper 0 · ROM SHA-256 `7e5d4fd1…` · tested automatically in
emulators ([docs/TESTING.md](docs/TESTING.md)).

## Screenshots

| Two pilots | One pilot |
|---|---|
| ![Co-op: P1 (left) and P2 (right) fighting the formation, green and orange shots](assets/screenshots/03-coop-gameplay.png) | ![1 PILOT: one ship, STG 01 above the hi score](assets/screenshots/02-single-player.png) |
| **Title screen** | **Weapon boost: W2 for both after stage 1** |
| ![Title screen with 1 PILOT and 2 PILOTS CO-OP](assets/screenshots/01-title.png) | ![Stage 2: both pilots on W2 with two shots each](assets/screenshots/04-weapon-boost.png) |

**Overdrive: READY in one stage, ACTIVE in the next**

| W4 READY (stage 3) | W4 ACTIVE (start of stage 4) |
|---|---|
| ![READY: message P1 W4 READY NEXT STAGE, W4 RDY above P1's score, P1 still on W3](assets/screenshots/05-overdrive-ready.png) | ![ACTIVE: P1 OVERDRIVE!, countdown W4 12s, P1 on W4, three aliens breaking from the new formation](assets/screenshots/06-overdrive-active.png) |
| Points made the overdrive ready; nothing changes until the stage is cleared. | The new formation is on screen: W4 for 12 s, ×2 points, and three aliens dive at once. |

| Life sharing | Both pilots in overdrive |
|---|---|
| ![P1 is out: P2 SELECT TO REVIVE P1](assets/screenshots/07-life-sharing.png) | ![Both pilots on W4: green lasers from P1, orange from P2](assets/screenshots/08-player-colors.png) |

All pictures are frames of the RC6 ROM in the cynes emulator (×3, no filtering), produced by the project's
test scripts with scripted input. For the READY/ACTIVE and both-in-overdrive pictures the scripts set the
score, lives, stage and weapon level in RAM to values reachable in normal play; the READY itself came
from a real kill and the overdrive from the game's own stage start ([details](docs/TESTING.md#screenshots)).

## Rules

The rules are the same for every pilot in both modes. Only the second ship, life sharing and the game-over
condition depend on having two players.

### Weapon levels

| Level | Shots at once | Shot speed | How to get it |
|---|---:|---:|---|
| **W1** | 1 | 100 % | start of the game; after a death if W2 was never unlocked |
| **W2** | 2 | 110 % | **free once per game for clearing the first stage**; otherwise 2000 points, then a cleared stage |
| **W3** | 3 | 120 % | 4000 more points after W2, then a cleared stage |
| **W4** | 4 lasers | 160 % | the Red Laser Overdrive – see below |

- One new press of FIRE = one shot, while a shot is free; holding FIRE never fires again.
- Points towards W2/W3 restart when a level is given; a cleared stage gives at most one level.
- The free W2 also goes to a pilot who is exploding or waiting for the next ship at that moment; a pilot
  hit on the last ship gets none.
- **W2 is kept after it is unlocked**: a death brings the pilot back on W2 (W1 if never unlocked). W3
  progress, points since the last death and the overdrive are reset; score and extra-life thresholds stay.

### Red Laser Overdrive (W4)

| | **W4 READY** | **W4 ACTIVE** |
|---|---|---|
| When | on W3, after 8000 points without dying (once per life) | at the start of the **next** stage, as soon as its formation is drawn (about 21 frames ≈ 0.35 s after the stage begins) |
| Weapon | still W3 | 4 lasers at 160 %, laser zap sound |
| Points | ×1 | **×2** for the pilot's own kills (they count for extra lives and the hi score) |
| Enemies | normal | **counter-attack**: three aliens leave the formation in that very frame and dive at the pilot; then about 60–80 % more dive starts, dives about 23 % faster, three of four dive targets and most enemy shots aimed at that pilot, one more shot per dive |
| HUD | `OVERDRIVE READY NEXT STAGE` (1 PILOT) or `P1 W4 READY NEXT STAGE` (co-op) for 2 s; `W4 RDY` above the score | jingle, `OVERDRIVE!` (`P1 OVERDRIVE!`, `P1 P2 OVERDRIVE!` …), countdown `W4 12s` … `W4 01s` |
| Ends | a death cancels it | after **12 seconds of play** (720 frames; pause and stage changes don't count) → back to W3, ×1, normal enemies; lasers in flight finish |

Each pilot has its own READY, countdown and once-per-life use. A revive by SELECT does not restore a
cancelled overdrive. When both pilots start in the same stage, the attacks are split between them – two
overdrives do not add up. In the game the lasers take the pilot's colour (green P1, orange P2).

### Lives, shield and stages

- **Lives**: each pilot starts with `X3` (including the ship in play). **Extra life** every 7000 points
  (7000, 14000, 21000 …), up to 9.
- **Respawn shield**: 4 seconds of invulnerability after every respawn and after a revive by SELECT; the
  ship blinks (faster in the last second), moves and fires. No shield at a game start or a stage change.
- **Stage counter** `STG 01`, `STG 02` … above the hi score, in both modes (1 PILOT also keeps the
  original stage flags).

### Two pilots only

- **Two ships**: P1 (controller 1) flies the original ship (red dome, white and cyan pods) with **bright
  green** shots; P2 (controller 2) flies its own orange-and-blue ship (delta nose, white cockpit) with
  **orange** shots. Same size and hit boxes; the ships can pass through each other.
- Separate scores and lives; points go to the pilot who shot; enemy shots and divers can hit either ship;
  dives alternate between the pilots.
- **Life sharing**: when one pilot is out (`X0`) and the other is in play with at least `X2`, that pilot
  presses **SELECT** to give one ship: donor −1 life and +200 points, receiver back with 1 life and the
  shield. The message line says who can press SELECT.
- **Game over** only when both pilots are out; a pilot left alone keeps playing.

## Controls

| Action | Player 1 | Player 2 |
|---|---|---|
| Move | D-pad left / right | D-pad left / right |
| Fire | A or B | A or B |
| Give a ship (co-op) | SELECT | SELECT |
| Pause | START | – |
| Title: choose mode / start | SELECT / START | – |

SELECT gives a ship only in a co-op game, during normal play, on a new press, when the rule above
allows it; otherwise it does nothing. A FIRE button held while the ship comes back must be released first.

## Installation

You need your own ROM of *Galaxian* (Japan) and Python 3 (tested with 3.14 on Linux). Commands are run
from the repository root.

| Required ROM | |
|---|---|
| File | `Galaxian (Japan).nes`, 16 400 bytes, NES 2.0 header, mapper 0 |
| SHA-256 | `1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e` |
| CRC32 | `8451DC60` (whole file), `084F61CD` (without header) |

Galaxian (USA) and headerless dumps are different files and are refused.

**A – apply the BPS patch**

```bash
python3 tools/bps.py apply "Galaxian (Japan).nes" games/galaxian-coop/patches/Galaxian_Coop.bps "Galaxian Coop.nes"
sha256sum "Galaxian Coop.nes"
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

Any BPS tool (Flips, Rom Patcher JS, beat) works too. The patch checks the CRC32 of the source and the
result.

**B – build from source**

```bash
mkdir -p games/galaxian-coop/private
cp "Galaxian (Japan).nes" games/galaxian-coop/private/
python3 games/galaxian-coop/src/build.py
sha256sum games/galaxian-coop/build/Galaxian_Coop.nes
# 7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca
```

The build checks the input, assembles `src/asm/coop.asm` with the repository's own 6502 assembler,
applies the code hooks (verifying every original byte it replaces), the CHR and palette changes, checks
RAM use, and writes `build/Galaxian_Coop.nes` plus Mesen 2 debugger labels `build/Galaxian_Coop.mlb`.
Options: `-o FILE`, `--bps` (also rewrite the patch). Two builds give identical bytes; errors stop the
build with exit code 1. How the hooks work: [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md).

## Running it in an emulator

The result is an ordinary mapper-0 NES ROM: load it in Mesen 2, FCEUmm (standalone or as a RetroArch
core), Nestopia, FCEUX or another NES emulator. For **2 PILOTS CO-OP**, assign a different input device
to player 1 and player 2 (RetroArch: Settings → Input → *Port 1 Controls* / *Port 2 Controls*) and connect
both controllers before starting the game.

Tested: automatically in the cynes emulator, the FCEUmm core (through `stable-retro`) and a 6502 tracer;
manually in an emulator. Not tested: Mesen 2, other emulators and cores, real NES/Famicom hardware.

## Known limitations

- **Sprite limit**: the NES shows at most 8 sprites per scanline; with many divers, shots and P2's ship on
  one line a sprite may vanish for a frame (not seen in the automatic checks).
- **CPU budget**: with both pilots in overdrive the game runs close to the per-frame limit; to stay inside
  it, at most one hit is processed per frame (a second one a frame later), P2's collision checks alternate
  frames, diver tilt updates at 30 Hz and the HUD is refreshed over a few frames. No slowdown was measured.
- When P1 loses a ship, new attack waves pause until P1 is back (as in the original); P2's deaths don't.
  The overdrive's opening attack is skipped if P1 is hit at that very moment.
- The counter-attack uses the game's own dives: the aliens fly their normal launch arc (~0.8 s) before
  turning down. The countdown follows the `OVERDRIVE!` message by a frame, the `Wn` digit by a few frames.
- 2 pixels of a diving purple alien are green instead of orange (no free colour for P1's shots); P1's ship
  keeps the original colours (it shares the HUD's palette).
- Messages are red and short (6-cell HUD fields, a 26-cell message line); 13 stars instead of 24.

## Troubleshooting

| Problem | What to do |
|---|---|
| `input is not Galaxian (Japan) [SHA-256 mismatch]` | Wrong dump or version – use the ROM with the SHA-256 above. |
| `original ROM not found: …` | Copy the ROM to `games/galaxian-coop/private/` or pass its path: `build.py PATH/rom.nes`. |
| BPS: `source ROM CRC mismatch` / `patch CRC mismatch` | Wrong source ROM, or a damaged `.bps` – restore it with `git checkout -- games/galaxian-coop/patches`. |
| `.patch $XXXX: original bytes … != …` | The source ROM is not the expected one, or `coop.asm` was edited inconsistently. |
| Different output hash | The build is deterministic: check the input hash and `git status`. |
| `ModuleNotFoundError` | Run with `python3` from inside the repository; keep `tools/` next to `games/`. |
| Player 2 does nothing | Assign a device to port 2; P2 uses controller **2**. |

## Documentation

| Document | Contents |
|---|---|
| [docs/TESTING.md](docs/TESTING.md) | how to run the tests, current results, test catalogue, measurements, manual checklist |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | every version with its ROM checksum |
| [docs/REVERSE_ENGINEERING.md](docs/REVERSE_ENGINEERING.md) | how the original game works, every hook, design decisions |
| [docs/MEMORY_MAP.md](docs/MEMORY_MAP.md) | ROM, RAM, OAM, CHR and nametable use |
| [docs/IMPLEMENTATION_REPORT.md](docs/IMPLEMENTATION_REPORT.md) | development report per release candidate (Polish; RC1–RC5 rules superseded) |
| [docs/history/](docs/history/) | superseded test history, stage-1 notes, map of squashed commits |

## Legal & credits

- **Galaxian Coop – Zvgelo (2026)**: all new code, graphics changes, tools, tests and documentation; no
  other hacks are used. Released under the [MIT License](../../LICENSE).
- The MIT License does not cover *Galaxian* itself – © Namco (arcade 1979, NES/Famicom 1984), its ROM,
  graphics and sound, the original program bytes quoted at the hook points, or the original graphics seen
  in the screenshots ([THIRD_PARTY_NOTICES](../../THIRD_PARTY_NOTICES.md)). The original credits stay on
  the title screen.
- Unofficial fan modification, not affiliated with or endorsed by Bandai Namco. No ROM is included.
