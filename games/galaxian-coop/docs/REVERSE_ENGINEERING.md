# Galaxian (Japan) – how the game works, and how Galaxian Coop hooks into it

Tools: a recursive 6502 disassembler that also follows the inline jump tables of the dispatcher `$E44B`
(~3540 instructions, all code reachable from RESET/NMI), a static scan of all RAM references, and the
cynes emulator for dynamic checks (RAM/OAM reads, screenshots, the main-loop idle counter as a CPU meter).
Confidence: **C** code + emulator, **K** code only, **H** hypothesis.

## 1. Program structure

- **RESET `$E020`** (C): `SEI/CLD`, S=`$4D`, waits for VBlank, clears `$00–$FF`, `$0200`, `$0600`,
  `$0700`; checks a signature at `$0105` (warm reset); copies data from CHR into RAM (`E0B8–E0FF`); clears
  both nametables, writes palettes, enables NMI and enters the **main loop `$E18B`**: `INC $3A / BEQ / JMP`
  – nothing else. The whole game runs in the NMI.
- **NMI `$E20C`** (C):
  1. sanity checks: S ≥ `$30`, interrupted code in `$E000+`, no B/D flag, `$2A` = 0 – otherwise
     read pads and reset (`E22F`);
  2. OAM DMA from page 2 (`$4014`), `E4AA`: 26-byte text row + VRAM queue (16 × 2 bytes), constant time;
  3. delay loop `E286` → first raster split: `$2005` = −`$E5` (formation sway);
  4. `F038` stars (even frames only), `E54D` pads, delay loop `E2A8` (`$BE` × 42 cycles) → second split:
     `$2005` = −`$E4` (**P1 ship**). The second split is only a few lines below the formation's bottom row;
  5. `E373` game logic (pause or state dispatcher `E3BF`), `E460` movement tables, `F66D` menu, frame
     counter, `E2FE` HUD and hi score, RNG, `RTI`.
- **Dispatcher `$E44B`** (C): `JSR $E44B` followed by a `.dw` table; index in A.

## 2. Original game logic (summary)

- **Pads `E54D`** (C): strobe, keep previous (`$EE`, `$F0`), 8 reads of `$4016`/`$4017` into `$EF`, `$F1`;
  `$4C` = pad of the current player (`$53`). Both pads are always read.
- **P1 ship** (C): not a sprite – background tiles `$62/$60/$63/$61` in rows 26–27 moved by the second
  raster split. X = `$E4` (signed), screen x = 120 + `$E4`. Movement `EEC0`: only when `$4F` = 0,
  1 px/frame, `$96..$6A`. Drawn by `EFFF` (from `FBEB`), explosion `EF09` through the VRAM queue.
- **P1 bullet `E627`** (C): Y `$0280`, X `$0283`; Y=`$C8` = ready on the ship; fire rule `E5A8` (A|B,
  counter `$44` = 3 while released: each press fires once, the button must be held 2 frames); −4 px/frame.
- **Bullet vs enemies `F2B3`** (C): `F381` formation (bullet position → column/row, bit in `$C3+col`,
  explosion in slot 7, points `E833`); `F2D1` → `F2EF` divers (window 12×13 around the sprite), hit →
  `F31E`; hit → `$0280` = 0.
- **Hits on the ship** (C): enemy bullets `E5BA–E61D` (tip: Y−`$CA` < 5, x in [`$E4`+`$7A`, +5); body:
  < `$11`, x in [`$E4`+`$77`, +11)); divers in states 2/7 `EB9C` → `EC37–EC93` (boxes 17/23 px wide) →
  `F31E`, `$4F`=1, sound `FE64`. Dives aim at `$E4` (`EE4E` target, `E65E` tilt).
- **Scores `E833`** (C): `$53` selects the row, adds `$54–$58`; the original one-time extra ship via
  `$3D`/`$42`. Hi score: `E2FE`/`E321` for the current player.
- **Lost ship** (C): `$4F` ≠ 0 → `E937` waits for all divers + 60 frames → `$FE`=3 → `FA52`: `$42`=0 →
  `FB23` game over; else (`FACB` player swap in alternating 2P) → `FA69`: `DEC $42` (`FA83`), "READY" →
  `FBEB`: draws the ship, `$4F`=0. `F415` launches no new attacks meanwhile.
- **Wave end** (C): formation empty (`$9F`) → same path; `FC1A` resets the formation, `INC $59` at `FC38`.
- **Menu** (C): state 1 `F75F`; SELECT toggles `$31` bit 0, START held 3 frames → `$FF`=3; `F9D9` starts.
- **Title** (C): built by `F5FF` in nametable `$2800`, one 26-byte row per frame (`F92B/F937` → `E4AA`);
  last step `F666`. Shown with vertical scroll `$EF`.
- **HUD** (C): labels drawn once as text rows; buffer `$0690–$06BB` streamed by `E342` (2 bytes per
  queue entry) to `$2074–$209F`; `E2FE` copies scores; `E897` reserve-ship icons, `E8B2` stage flags.

## 3. Galaxian Coop – hooks

All 37 hooks are `.patch` blocks in `src/asm/coop.asm`; the build checks every original byte.

| Address | Original | New | Purpose |
|---|---|---|---|
| `$E21D` | `LDA $0106,X / CMP #$E0 / BCC E22F` | `JMP NmiGuard` | overlapping NMI → one lag frame instead of a reset; watchdog after 8 |
| `$E286` | `LDY #$EB` | `LDY #$EA` | compensates ScrollFix (−22 cycles) |
| `$E2A5` | `JSR $E54D` | `JSR PreSplit` | constant-time bullet move/draw inside the raster wait |
| `$E2A8` | `LDY #$BE` | `LDY #$A8` | wait shortened by exactly `PreSplit`'s 22 × 42 cycles |
| `$E2CE` | `JSR $E373` | `JSR CoopPost` | P2 draw, ready bullets, banner, HUD, hi score, title badge |
| `$E542` | scroll/ctrl writes | `JMP ScrollFix` | play: Y scroll `$EF` + nametable `$2800` → blank screen line 0 |
| `$E5BA` | `JSR $E627` | `JSR P1Bullets` (RTS) | original P1 bullet replaced by the shared engine |
| `$E5DF`, `$EC59` | `INC/DEC $4F` | `INC/DEC P1_BLOCK` | a P1 who is out can't be hit |
| `$E611`, `$EC8F` | `LDA #1 / STA $4F` | `JSR SetP1Dead` | P1 hit: also `P1_BLOCK`, weapon reset |
| `$E833` | `JSR $E88D` | `JMP ScoreAdd` | every score: boost points, no-death points, W4, extra lives |
| `$E913` | `JSR $F2B3` | `JSR CoopPre` | `P1_BLOCK`, bullet collisions for both pilots |
| `$E91F` | `JSR $E9B1` | `JSR CoopMid` | life sharing, P2 movement/collisions/lives |
| `$EB9C` | `JSR $E65E` | `JSR OrientHalf` | diver tilt every other frame (CPU) |
| `$EE4E` | `LDX $9E / LDY $9D` | `JMP AimDiver` | dives alternate between P1 and P2 |
| `$EEC0` | `LDA $4F` | `LDA P1_BLOCK` | P1 out: no movement |
| `$F03F…$F061`, `$FC9B…$FCBA` | stars from `$02A0`, 24 | from `$02CC`, 13 | OAM for P2 and 8 bullets |
| `$F666` | `INC $FE / LDA` | `JMP TitleExtra` | title rows `1 PILOT`, `2 PILOTS CO-OP`, credit |
| `$F753` | OAM clear to 0 | `JMP ClearOam` | free sprites get blank tile `$10` (no "0" top-left) |
| `$FA34` | `STA $3C / STA $53` | `JSR CoopInit` | "2 PILOTS" = co-op; resets all new state |
| `$FA5D` | `JMP $FB23` | `JMP P1OutOfLives` | P1 without ships sits out while P2 plays |
| `$FA83` | `DEC $42 / LDA #0` | `JSR P1ShipGranted` | lives HUD; P1 spawn X (co-op: left) |
| `$FAA0` | `LDA $31` | `LDA $3C` | no "PLAYER 1" banner on co-op respawns |
| `$FC17` | `JMP $EFFF` | `JMP P1ShipRedraw` | no P1 ship redraw while P1 is out |
| `$FC38` | `INC $59 / SEC` | `JSR StageCleared` | weapon boosts, co-op spawn positions, once per stage |

## 4. Galaxian Coop – new routines (addresses of this build; see `build/Galaxian_Coop.mlb`)

| Routine | Address | What it does |
|---|---|---|
| `PreSplit`, `PrePilot` | `$9E00`, `$9E2F` | constant time (939 cycles): moves bullets (8.8 speed) and writes their sprites |
| `ScrollFix` | `$9F00` | frame-start scroll; 42 cycles on both paths |
| `CoopPre` / `BulletHits` | `$807A` / `$80B5` | builds the hittable-diver list; per pilot `PilotShots` |
| `PilotShots` | `$8103` | per bullet: inline copy of `F381`'s tests (calls `F381` only for a real hit), `DiverHits`; one hit per frame; then `FireShot` |
| `DiverHits` | `$820F` | `F2EF`'s test against the listed divers; `F31E` on a hit |
| `FireShot` | `$8268` | `E5A8` fire rule for 1–4 slots |
| `ScoreAdd` / `AfterScore` | `$8367` / `$8374` | `E836` then boost + no-death points, `CheckW4`, `ExtraLifeCheck` |
| `ExtraLifeCheck`, `AwardLife` | `$83A4`, `$8423` | thousands from the score digits vs `NEXT_LIFE` (step 7); cap 9 lives |
| `StageCleared`, `CheckW4` | `$8448`, `$84BC` | W1→W2 (2000), W2→W3 (5000), co-op free W2 once; W4 at 8000 no-death |
| `CoopMid`, `P2Alive`, `P2Waiting`, `P2Exploding`, `P2Kill` | `$84E6…$8551` | P2 state machine |
| `P2VsBullets`, `P2VsDivers` | `$8561`, `$85A2` | copies of the ship hit boxes for `P2_X` (alternate frames) |
| `LifeShare`, `GiveFromP1/P2`, `LifeShareBonus` | `$869E…$873B` | SELECT edge, transfer, +200 via `E841`+`AfterScore` |
| `NmiGuard` | `$8781` | lag frame instead of reset |
| `CoopPost`, `BannerUpdate`, `BannerWanted` | `$87F6`, `$884A`, `$889F` | messages through the idle 26-byte row writer |
| `TitleBadge` | `$89F9` | `CO-OP` sprites on the settled title |
| `CoopHud`, `HudP1Lives`, `P1TotalLives`, `P2TotalLives` | `$8A4E…$8B3A` | HUD (every 4th frame), lives = reserve + ship in play |

## 5. Key design decisions

- **P2 ship as sprites**: P1's ship is background moved by a raster split; a second split on the same lines
  is impossible. The ship graphic is symmetric, so one tile per half is drawn twice (second copy flipped).
- **One bullet engine for both pilots and modes**: 4 slots per pilot. Collisions reuse the original
  `F381` (formation) and `F31E` (diver kill) with `$53` = owner, so the original scoring applies. `F381`'s
  tests are done inline first; `F381` itself only runs for a real hit. Its single side effect on a miss
  (`F374`: formation sway step reset when the bullet passes between columns, Y < `$A0`) is kept for each
  pilot's first slot.
- **Speeds**: 8.8 fixed point – W1 4.00, W2 4.40 (`$66`), W3 4.80 (`$CC`), W4 6.40 px/frame
  (100 / 110 / 120 / 160 %). At 6.4 px per frame no 12/13-px hit window can be skipped.
- **CPU budget**: the original leaves ~3300 cycles free in its worst frames. To fit 8 bullets: (a)
  bullet movement and sprites run in `PreSplit` inside the raster wait, made constant-time (every slot path
  84 cycles) and the wait shortened by the same amount, so the split timing is unchanged (verified: the
  formation area is pixel-identical with and without the shortened wait); (b) at most one bullet hit per
  frame (a kill costs ~2000+ cycles); (c) divers are checked against each bullet every other frame (≤ 13 px
  between checks = no miss); (d) P2's ship checks alternate frames; (e) diver tilt (`E65E`) every other
  frame; (f) HUD every 4th frame; (g) extra-life check only when the thousands digit changes;
  (h) overlapping NMI → lag frame (safety net).
- **Lives**: the game counts reserve ships (`$42/$43`); the HUD shows reserve + ship in play. For P1 the
  short window between a hit and the reserve decrement at `FA83` is covered by `P1_GRANTED`.
- **Life sharing**: SELECT edge from `$EE/$EF` and `$F0/$F1` (previous/current); only in `FE`=8 (E913 does
  not run while paused). A revived P1 gets its background ship redrawn with `EFFF` (as `FBEB` does).
- **Top line**: in play the original scrolls with Y=`$FF`, so screen line 0 shows nametable row 31 = the
  attribute table read as tiles → the white dashes. `ScrollFix` uses Y=`$EF` with nametable `$2800` (like
  the title screen): line 0 comes from the blank row 29 of `$2800`, line 1 onward is unchanged.
- **Top-left "0"**: free sprite slots have Y=0 (that is how the game marks them free) and tile `$00` from
  `F753`; they showed on lines 1–8. `ClearOam` gives them the blank tile `$10`.
