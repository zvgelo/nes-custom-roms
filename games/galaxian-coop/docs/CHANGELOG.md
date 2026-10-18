# Changelog – Galaxian Coop

Output of each version: `build/Galaxian_Coop.nes` from `Galaxian (Japan).nes`
(SHA-256 `1188cedf…3613e`). Earlier versions can be rebuilt from their git commit.

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
