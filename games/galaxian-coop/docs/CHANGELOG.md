# Changelog – Galaxian Coop

Output of each version: `build/Galaxian_Coop.nes` from `Galaxian (Japan).nes`
(SHA-256 `1188cedf…3613e`). Earlier versions can be rebuilt from their git commit.

## 2026-10-18 – RC3: ghost shots, weapon parity, frame budget (branch `game/galaxian-coop`)

Result: SHA-256 `aa33c6b037254a197cf78a29510db75391c6a95f151b2dcf99c9ea9c5a851e8d`,
`patches/Galaxian_Coop.bps` (3891 bytes). Bugs reported after RC2 tests in manual emulator testing.

### Fixed
- **"P1 shooting from off screen"**: no real P1 shot was created. The original hit routines read the
  bullet from `$0280/$0283`, which is also P1 shot slot 0's sprite; every shot tested there (also P2's)
  left its position in that sprite, so after a P2 hit a P1 shot showed for one frame where P2's shot hit –
  most visible while P1 was dead or out. The slot is now restored after each hit routine. A dying pilot's
  shots also showed for one more frame; their sprites are hidden at once now.
- **P2's 2nd and 3rd shots flew from the wrong place** (W2–W4): `BUL_X` overlapped `$23/$24`, which the
  original's pad routine overwrites every frame (Famicom microphone check). This could also reach the
  original's microphone reset path. `BUL_X` moved to `$0E–$15`; the build now refuses variables on
  addresses the original uses. P1 and P2 are now measured identical on W1–W4.

### Changed
- `E2FE` (scores/hi score into the HUD buffer, every frame) now copies only in frames with points or a new
  hi score; the HUD stream is unchanged. Worst W4 frame: +37 idle iterations (~370 cycles) on the same
  saved frames.
- CPU measurements corrected: the idle counter could be read in the middle of its 16-bit increment; the
  "1 iteration" (RC2) and "15 iterations" (RC1) worst frames were measurement artefacts. Real worst W4
  frame in RC2: 67 iterations (~670 cycles); RC3: see TESTING.md.

### Tests
- 61 cynes tests (5 new) and 3 new checks in a second emulator (FCEUmm via stable-retro).

## 2026-10-18 – RC2: weapon fixes and respawn shield (branch `game/galaxian-coop`)

Result: SHA-256 `14fd826686e2aebf6151637683f6d43cef2e54d3739b8ccaea9c2768d2595538`,
`patches/Galaxian_Coop.bps` (3804 bytes). Bugs found by the user testing RC1 in manual emulator testing.

### Fixed
- **Held FIRE fired again**: the original counter rule (`E5A8`) wrapped from 0 to `$FF`, so a held button
  fired every 256 frames; the shared engine also skipped the counter while all shots were flying, so a
  release could be missed. Now one shot per new press on every level, for each pad separately.
- **Weapon after a death**: a pilot who was exploding or waiting for the next ship when a stage ended still
  got the free W2 (and kept it after the respawn); the shots of a dead pilot kept flying and could still
  score. Now a death or revive gives W1 with no boost or no-death points and removes the pilot's shots; a
  button held through the respawn needs a new press.
- **Free W2 after stage 1**: given only to pilots alive and in play at that moment, in one pass for both
  pilots; never later.
- P1 hit by an enemy bullet removed enemy bullet 0 instead of the one that hit (register X lost in the
  hook at `E611`).

### Added
- **Respawn shield** (co-op): 4 s (240 frames) of invulnerability after each respawn and for the revived
  pilot after life sharing; the ship blinks (8/8 frames, last second 4/4) and can move and fire. Not at
  the start of a game or stage, not for the donor, not in 1 PILOT.

### Tests
- 11 new emulator tests (56 in total), see TESTING.md.

## 2026-10-18 – boosts, life sharing, new HUD and title (branch `game/galaxian-coop`)

Result: SHA-256 `9e87f49b320547c96663e810196c87c78bfb714c040fa12596b8f33bced3ee5d`,
`patches/Galaxian_Coop.bps` (3617 bytes).

### Added
- **Life sharing** (co-op): SELECT (new press) gives one ship to a partner who is out (`X0`), if the giver
  has at least `X2`; the receiver re-enters beside the giver with 1 life and W1; the giver gets +200 points.
- **Revive prompt**: `P2 SELECT TO REVIVE P1` / `P1 SELECT TO REVIVE P2` on the top of the screen, or
  `P1 OUT` / `P2 OUT` when the partner has only `X1`.
- **Weapon boosts W1–W4** in both modes, per pilot: 1/2/3/4 bullets at 100/110/120/160 % speed.
  W2: 2000 boost points + a cleared stage (co-op: free once for the first stage); W3: +5000 + a cleared
  stage; W4 (red laser): W3 + 8000 points without dying, immediately, with a `GREAT SHOT` / `W4 RED LASER`
  message. A death or a revive resets the pilot to W1.
- **Extra life every 7000 points** per pilot (both modes; replaces the original one-time extra ship);
  the life-sharing bonus counts; lives capped at 9.
- **HUD**: one ship icon with `Xn` (all lives left, including the ship in play) and `Wn` per pilot, in both
  modes; P2's icon in P2's colours.
- **Title**: `1 PILOT` / `2 PILOTS CO-OP`, animated `CO-OP` badge on the logo, `HACK BY ZVGELO ©2026`.
- **Co-op spawn positions**: P1 left, P2 right of the centre (start, respawn, each new stage).
- Shared bullet engine for both pilots (4 slots each), red laser tile, Mesen 2 labels for all new code
  and RAM, build checks for RAM overlaps and page alignment.

### Fixed
- White dashes on screen line 0 during play (original ROM: Y scroll `$FF` showed the attribute table).
- `0` in the top-left corner (original ROM: free sprites parked at Y=0 with tile `$00`).
- Lives display: one pilot showed 2, the other 3 at the start (the HUD showed reserve ships, updated at
  different moments for P1 and P2); now total lives `X3`/`X3`.
- A missed NMI deadline reset the whole game (original watchdog); now one lag frame, the reset only after
  8 in a row.

### Changed
- Stars: 13 instead of 24 (sprites for P2 and up to 8 bullets).
- CPU: bullet movement/drawing inside the raster wait (constant time), one bullet hit per frame, diver
  checks every other frame per bullet, P2 ship checks on alternate frames, diver tilt at 30 Hz, HUD every
  4th frame. See TESTING.md for measurements.
- Build output renamed to `Galaxian_Coop.nes` / `.mlb` / `.bps`.

## 2026-10-18 – Stage 2 (commit `3080e8d`, branch `game/galaxian-coop`)

Result: SHA-256 `eb19e3ef1519b20da9e3a9c16c9e4cadf1a6b7725d61adfb27d875ad2db88159`.

- "2 PLAYERS" starts simultaneous co-op; "1 PLAYER" unchanged.
- P2 ship (sprites), controller 2, ships pass through each other.
- P2 bullet, hits on formation and divers, points to the bullet's owner.
- Enemy bullets and divers hit both ships; P2 explosion and respawn.
- Separate lives; P1 without ships sits out while P2 plays; Game Over when both are out.
- Dives alternate between P1 and P2.
- HUD with both scores and reserve ships; P2 can set the hi score.
- PRG 32 KiB (NROM-256), new code from `$8000`; 19 stars.
- Removed the Stage 1 hook (`$E57A`, copy of `$F1` into `$07F0`): `$07F0` is game data – sprite 0 of the
  game-over animation did not move in Stage 1.

## Stage 1 – experiment (before the repository)

PRG expanded to 32 KiB, hook `$E57A → $8000` copying pad 2 into `$07F0`. Replaced in Stage 2.
