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

All hooks are `.patch` blocks in `src/asm/coop.asm`; the build checks every original byte.

| Address | Original | New | Purpose |
|---|---|---|---|
| `$E21D` | `LDA $0106,X / CMP #$E0 / BCC E22F` | `JMP NmiGuard` | overlapping NMI → one lag frame instead of a reset; watchdog after 8 |
| `$E286` | `LDY #$EB` | `LDY #$EA` | compensates ScrollFix (−22 cycles) |
| `$E2A5` | `JSR $E54D` | `JSR PreSplit` | constant-time bullet move/draw inside the raster wait |
| `$E2A8` | `LDY #$BE` | `LDY #$A3` | wait shortened by exactly `PreSplit`'s 27 × 42 cycles (RC3: 22) |
| `$E2E4` | `JSR $E2FE` | `JSR HudScores` | score/hi-score copy into the HUD buffer only in the two frames after points (RC3/RC4, CPU); RC4: HUD stream every other frame |
| `$E2CE` | `JSR $E373` | `JSR CoopPost` | P2 draw, ready bullets, banner, HUD, hi score, title badge |
| `$E542` | scroll/ctrl writes | `JMP ScrollFix` | play: Y scroll `$EF` + nametable `$2800` → blank screen line 0 |
| `$E5BA` | `JSR $E627` | `JSR P1Bullets` (RTS) | original P1 bullet replaced by the shared engine |
| `$E5DF`, `$EC59` | `INC/DEC $4F` | `INC/DEC P1_BLOCK` | a P1 who is out or shielded can't be hit |
| `$E611`, `$EC8F` | `LDA #1 / STA $4F` | `JSR SetP1Dead` | P1 hit: also `P1_BLOCK`, `PilotDown`; keeps X/Y (`E61A` uses X) |
| `$E833` | `JSR $E88D` | `JMP ScoreAdd` | every score: x2 for an overdrive pilot's shots (RC4), boost points, no-death points, overdrive READY (RC6), extra lives |
| `$E897` | `JSR $E88D` | `RTS` | reserve-ship icons never drawn (lives are `Xn` in both modes; RC1–RC5 overwrote them every 4th frame) (RC6) |
| `$E8B2` | `JSR $E88D` | `JSR StageFlags` | stage flags only in 1 PILOT; in co-op that HUD area is P2's (RC6) |
| `$E913` | `JSR $F2B3` | `JSR CoopPre` | RC6: overdrive start (`OdStart`), countdown, respawn shield in every game (1P too), `P1_BLOCK`, bullet collisions for both pilots |
| `$E91F` | `JSR $E9B1` | `JSR CoopMid` | overdrive dive boost (`DiveBoost`, RC4), firing of both pilots (after the ships moved, RC4), life sharing, P2 movement/collisions/lives |
| `$EB9C` | `JSR $E65E` | `JSR OrientHalf` | diver tilt every other frame (CPU) |
| `$EE4E` | `LDX $9E / LDY $9D` | `JMP AimDiver` | dives alternate between P1 and P2; overdrive: 3 of 4 at the overdrive pilot (RC4), +1 enemy shot per aim (`AimShots`, RC6) |
| `$E1CF` | palette byte `$27` | `$2A` | sprite palette 2 colour 3 bright green: P1's shots (RC5; RC4 `$28` yellow) |
| `$EE23` | `CLC / LDA $E4` | `JSR BulletAimX` | overdrive of P2 alone: enemy shots aim at P2 7 frames of 8 (RC6; RC4 3 of 4); both in overdrive: alternate |
| `$F45F` | `LDA $ED / AND #3 / BNE` | `JMP AtkGate` | overdrive: two extra solo-attack counter steps per 16 frames (+50 %; RC4: one) |
| `$F10E` | `LDY $59 / CPY #1 / LDY $65` | `JSR SoloLimit` | overdrive: solo-diver slot limit one attack level higher (RC6) |
| `$F48B` | – | (RC4–RC5 `JSR SoloGate`, removed in RC6) | original again: solo attacks wait for the flagship window |
| `$F5A5`, `$F5DF` | `LDA $0280` | `JSR DemoBullet` | the demo pilot sees P1's slot 0 as the original bullet (`$C8` = ready): it fires again (RC6) |
| `$FD17` | `JSR $FED4` | `JSR SoundTick` | overdrive jingle step on the triangle (RC4) |
| `$EEC0` | `LDA $4F / BNE / JSR $EED6` | `JSR P1MoveGate` | P1 hit or out: no movement (the shield does not block it) |
| `$F03F…$F061`, `$FC9B…$FCBA` | stars from `$02A0`, 24 | from `$02CC`, 13 | OAM for P2 and 8 bullets |
| `$F666` | `INC $FE / LDA` | `JMP TitleExtra` | title rows `1 PILOT`, `2 PILOTS CO-OP`, credit |
| `$F753` | OAM clear to 0 | `JMP ClearOam` | free sprites get blank tile `$10` (no "0" top-left) |
| `$FA34` | `STA $3C / STA $53` | `JSR CoopInit` | "2 PILOTS" = co-op; resets all new state |
| `$FA5D` | `JMP $FB23` | `JMP P1OutOfLives` | P1 without ships sits out while P2 plays |
| `$FA83` | `DEC $42 / LDA #0` | `JSR P1ShipGranted` | lives HUD; P1 spawn X (co-op: left) |
| `$FAA0` | `LDA $31` | `LDA $3C` | no "PLAYER 1" banner on co-op respawns |
| `$FC17` | `JMP $EFFF` | `JMP P1ShipRedraw` | no P1 ship redraw while P1 is out; `FireRearm` |
| `$FC38` | `INC $59 / SEC` | `JSR StageCleared` | weapon boosts (free W2 in every game, RC6), co-op spawn positions, arms the overdrive start, once per stage |

## 4. Galaxian Coop – new routines (addresses of the RC6 build; see `build/Galaxian_Coop.mlb`)

| Routine | Address | What it does |
|---|---|---|
| `PreSplit`, `PrePilot` | `$9E00`, `$9E2F` | constant time (1171 cycles): moves shots (8.8 speed, each with the level it was fired with) and writes their sprites in the pilot's palette; tables at `$9D00` |
| `ScrollFix` | `$9F00` | frame-start scroll; 42 cycles on both paths |
| `CoopPre` / `BulletHits` | `$8091`, `$813A` | overdrive start (`OdStart`) and countdown, shield countdown (every game), builds the hittable-diver list; per pilot `PilotShots` |
| `PilotShots` | `$818A` | per shot: inline copy of `F381`'s tests (calls `F381` only for a real hit), `DiverHits`; one hit per frame |
| `DiverHits`, `DiverHitsX` | `$82A6`, `$82F2` | `F2EF`'s test against the listed divers (laser: 17-px window); `F31E` on a hit |
| `FireShot`, `FireRearm` | `$832D`, `$846F` | one shot per new press for 1–4 slots; stores the level (`BUL_LV`); zap sound on W4 |
| `BulletOwnerSlot`, `BulletHitDone` | `$8227`, `$8244` | shot under test → `$0280/$0283` for the original routines (sets `BY_SHOT`); afterwards P1 slot 0's sprite is put back |
| `HudScores` | `$8AB6` | `E2FE` (copy + hi score) in the two frames after points, `E342` stream every 4th frame |
| `PilotDown`, `ResetBoost` | `$8479`, `$8456` | death / revive: W2 if unlocked else W1, W3 progress / no-death points / overdrive (READY too) reset, shots removed, shield 240 in every game (RC6) |
| `ShieldTick`, `ShieldHidden`, `P1Blink`, `P1MoveGate` | `$80D3`, `$80EE`, `$8108`, `$8124` | respawn shield countdown, blink phase, P1 blink, P1 movement gate |
| `ScoreAdd`, `ScoreDouble`, `AfterScore` | `$84AD`, `$84D0`, `$84F9` | points from `E80F`/`E821`, x2 for an overdrive pilot's shot, `E841` once, then boost + no-death points, `CheckW4`, `ExtraLifeCheck` |
| `ExtraLifeCheck`, `AwardLife` | `$8535`, `$85B4` | thousands from the score digits vs `NEXT_LIFE` (step 7); cap 9 lives |
| `StageCleared`, `PilotAlive`, `PilotComing`, `CheckW4`, `W4Tick` | `$85D9`, `$8655`, `$8663`, `$8683`, `$8775` | W1→W2 (2000), W2→W3 (4000 from W2), free W2 once per game (RC6: 1P too) for pilots in play or with a ship coming, arms the overdrive start; READY at 8000 no-death on W3, once per life; 12-s countdown (RC6) |
| `CoopMid`, `P2Update`, `DiveBoost` | `$879D`, `$87C3`, `$8BBD` | firing of both pilots after the ships moved; P2 state machine; overdrive dive boost |
| `P2Alive`, `P2Waiting`, `P2Exploding`, `P2Kill` | `$87F9`, `$87D2`, `$880E`, `$8829` | P2 states |
| `P2VsBullets`, `P2VsDivers` | `$8839`, `$887A` | copies of the ship hit boxes for `P2_X` (alternate frames) |
| `LifeShare`, `GiveFromP1`, `GiveFromP2`, `LifeShareBonus` | `$8976`, `$8997`, `$89D3`, `$8A16` | SELECT edge, transfer, +200 via `E841`+`AfterScore` (never doubled) |
| `SfxOverdrive`, `SfxZap`, `SoundTick` | `$8A5E`, `$8A69`, `$8A84` | overdrive jingle (triangle), laser zap (pulse 2), jingle step |
| `NmiGuard` | `$8AD6` | lag frame instead of reset |
| `AimDiver`, `AimShots`, `OdActive`, `OdTarget`, `AtkGate`, `SoloLimit`, `BulletAimX` | `$8B1B`, `$8B6A`, `$8B73`, `$8B7A`, `$8B92`, `$8BAC`, `$8C04` | dive target choice (+1 shot per aim in overdrive); overdrive aggression hooks |
| `OdBanner`, `OdStart`, `OdAttack` | `$86AC`, `$86C4`, `$8758` | RC6: overdrive message; start of READY overdrives in the first normal-play frame of a stage; the 3-diver counter-attack |
| `DemoBullet` | `$8326` | RC6: the demo pilot's view of the bullet (`$C8` while slot 0 is free) |
| `CoopPost`, `BannerUpdate`, `StatusRow`, `StatusField`, `BannerWanted` | `$8C35`, `$8C81`, `$8CE7`, `$8D5A`, `$8E02` | messages (row 1) through the idle row writer; status row 2 (stage, countdowns) through the VRAM queue |
| `TitleBadge` | `$8FAB` | `CO-OP` sprites on the settled title |
| `HudRightClear`, `StageFlags` | `$9057`, `$9065` | RC6: new game: HUD buffer rows 3–4 cols 20–31 blank; `E8B2` skipped in co-op |
| `CoopHud`, `HudP1Lives`, `P1TotalLives`, `P2TotalLives` | `$9000`, `$9070`, `$90EC`, `$9105` | HUD (every 4th frame), lives = reserve + ship in play |

## 5. Original attack and difficulty system (RC4 analysis)

Measured in headless runs of the original ROM (`tools/trace6502.py`: ship invincible, no player fire,
36 000 frames per point) and read in the code. **F** = in the code (address), **M** = also measured,
**H** = hypothesis.

- **RAM (F)**: `$59` stage (0-based, wraps after 99); `$5B–$62` 8 solo-attack counters (+1 every 4th
  frame, reset at `F4CC,X`); `$63/$64` frame / seconds counters; `$65` attack level 0–7: `FC66` sets
  `min($59, 7)` at every wave and life start, then +1 every 1200 frames (20 s) up to 7 (`F457–F45D`);
  `$67` flagship timer; `$35` flagship attack window (150 frames); `$27` aliens left in the formation;
  `$0740+s` dive x target; `$06E8+s` shots a diver may still fire.
- **While P1 is dead** `F415` jumps to `FC66` every frame: no new attacks, and the level falls back to the
  stage's start value; in co-op this holds even while P2 plays on (F).
- **Dive starts (`F415`, F/M)**: every 4th frame the 8 counters step; a counter reaching its threshold
  (`F4CC` = 280, 400, 712, 676, 652, 616, 604, 472 frames) asks for a solo dive (one attempt per ~63
  frames at every level). The attempt is dropped while the flagship window `$35` is open (28–31 % of
  attempts) and when no diver slot is free. Solo slots: `F134[$65]` (stage 1: 3 3 4 4 5 5 6 6) or
  `F13C[$65]` (stage 2+: 3 4 4 5 5 6 6 6), minus the 2 escort slots. The flagship group starts when
  `$67` reaches `F4DC[$65]` (stage 1: off, 135, 135, 135, 120, 120, 120, 120 × 4 frames) or `F4E4[$65]`
  (stage 2+: 135, 135, 135, 120, 120, 120, 120, 105) and only with 26 or fewer aliens left. Solo divers
  are the outermost blue/purple aliens (left and right edge in turn), red ones only when none are left.
- **Dive movement (F/M)**: launch arc 48 frames (1 px/frame), dive: y + 1 px every frame, x accelerates
  toward the target `EE52` sets (current x ± 48–112 px toward `$E4+$78`, re-aimed whenever the x speed
  returns to 0), return to the formation an exact number of frames. **No movement speed depends on the
  stage.** A dive cycle takes ~300 frames.
- **Enemy shots (F)**: divers in states 2/7 fire at y = `$40`, `$50` … `$90`; 2 shots per aim on stage 1,
  3 from stage 2; at most 7 at once; 2 px/frame down, at most 1 px/frame sideways toward `$E4+$7C` at the
  moment of firing (`EE23`); none for 180 frames after a flagship kill.
- **Saturation (F)**: from stage 8 (`$59` = 7) everything starts at the maximum: level 7, 4 solo divers,
  flagship every 420 frames, 3 shots per aim. Stages 8–99 play the same; after 99 the game restarts at 1.

| | Stage 1 | Stage 2 | Stage 5 | Stage 10 / 20 |
|---|---|---|---|---|
| `$65` at the start (+1 / 20 s) | 0 (7 after 140 s) | 1 (7 after 120 s) | 4 (7 after 60 s) | 7 |
| solo divers at most | 1, 2 at 40 s, 3 at 80 s, 4 at 120 s | 2, 3 at 40 s, 4 at 80 s | 3, 4 at 20 s | 4 |
| flagship period | off for 20 s, 540 f, 480 f from 80 s | 540 f, 480 f from 40 s, 420 f from 120 s | 480 f, 420 f from 60 s | 420 f |
| shots per aim | 2 | 3 | 3 | 3 |
| dive starts / 1000 frames, full formation (M) | 2.8 (level 0) … 8.1 (level 7) | 2.5 … 7.6 | 6.3 … 7.6 | 7.6 |

## 6. Original sound driver (RC4 analysis)

`FD0E` runs every frame of state 3 (`FCFC` returns at once in other states). **Pulse 1** plays the four
tunes (slots `$6D–$70`, lowest active slot wins: extra ship, flagship kill, kill, game start) and the
diving siren; it is rewritten every frame. **Pulse 2** and **noise** carry the shot (`FEA8`), explosions
(`FE64`, `FE8E`) and the formation hum (`FEEB`, every 32 frames); the last write wins. **The triangle
and the DMC are never used.** Tune data: slot 0 at `$FE54`, slots 1–3 in RAM `$0156–$01FF` (copied from
CHR at reset), pointers `$014E–$0155` = address + `$0840`; byte = duration code (bits 7–5: 1…64 frames,
7 = end) + note (bits 4–0, periods at `$FE0A`); byte 0 of a tune is never played. The shot is fully
hardware-driven (envelope + sweep); `FED4` meant to ramp its noise but clears `$40` on the first frame
(harmless original quirk).

## 7. Key design decisions

Notes are labelled with the release candidate that introduced them. Where a later version changed the
behaviour, the note says **Superseded** and points to the current rule; the current rules are in the
game's [README](../README.md).

- **P2 ship as sprites**: P1's ship is background moved by a raster split; a second split on the same lines
  is impossible. The ship graphic is symmetric, so one tile per half is drawn twice (second copy flipped).
- **One bullet engine for both pilots and modes**: 4 slots per pilot. Collisions reuse the original
  `F381` (formation) and `F31E` (diver kill) with `$53` = owner, so the original scoring applies. `F381`'s
  tests are done inline first; `F381` itself only runs for a real hit. Its single side effect on a miss
  (`F374`: formation sway step reset when the bullet passes between columns, Y < `$A0`) is kept for each
  pilot's first slot.
- **Speeds**: 8.8 fixed point – W1 4.00, W2 4.40 (`$66`), W3 4.80 (`$CC`), W4 6.40 px/frame
  (100 / 110 / 120 / 160 %). Divers are tested against a shot every other frame: up to W3 a shot moves
  ≤ 9.6 px in two frames (+ 2 px of the diver) inside the 13-px window. A W4 laser moves 12.8 px, so RC4
  gives lasers a 17-px window (4 px higher, as the laser sprite is 4 px taller than the bullet);
  RC2–RC3 lasers could pass through a diver.
- **RC4 scores (`$0116–$012F`)**: RC3 moved `AIM_TOGGLE`/`P1_REDRAW` to `$011D/$011E` and RC2 put
  `SHIELD`/`SCORE_NEW` at `$0126–$0128`, believing only the reset code wrote there. But `E307` copies
  `$0117–$0125` (P1 score, the two gap bytes, `$011F`, hi score) into the HUD buffer, so the cells right
  of P1's score showed the dive toggle (letters are red in that palette: "G", "." in photos from manual testing)
  and a "0"; and `FB70` writes the whole 26-byte row to the title after GAME OVER (shield values `$F0`
  showed there). The RAM scores were never wrong. The variables now live in the CHR-copy filler
  `$0347–$037F`; `build.py` checks every new variable against `src/original_ram.txt` (traced runtime use
  of the original) besides the zero-page list.
- **RC4 overdrive (W4)** – *Superseded by RC6* (READY by points, start with the next stage once its formation is drawn, 12 s; see "RC6 overdrive start" below). RC4: 30 s of normal play (seconds `W4_SEC` × 60 frames `W4_FRM`, counted in
  `CoopPre` only in sub-state 8: a pause, the READY / respawn / stage-change sequences don't count), once
  per life (`W4_USED`), then W3. Every shot keeps the level it was fired with (`BUL_LV`: speed, laser
  tile), so lasers in flight finish as lasers; new shots use W3's 3 slots. x2: `ScoreAdd` computes the
  points (`E80F`/`E821`), doubles them when `BY_SHOT` (set by `BulletOwnerSlot`) and the owner is on W4
  (tens/hundreds with carry into the thousands digit `$56`), adds them once with `E841` and runs
  `AfterScore` once (boost/no-death points, extra lives, HUD).
- **RC4 aggression** – *partly superseded by RC6* (the stronger profile below; the "no stored flag" design is kept): no stored flag – every hook tests `W4_SEC` of both pilots, so all effects stop
  with the last overdrive (and are byte-for-byte inert without one, tested). +25 % solo attack attempts
  (`AtkGate`; the flagship timer is not stepped twice), solo attacks not blocked by the flagship window
  (`SoloGate`; the slot limits stay the stage's), dives +14 % (`DiveBoost`: on odd frames +1 px for a
  diver at y & 7 = 4 or 5, i.e. once per 8 px; never across a fire row or a hit band), aim bias toward a pilot in
  overdrive alone (`AimDiver` 3 of 4 dives, `BulletAimX` 3 of 4 shots). Measured from one saved
  moment, 90 s, P2 in overdrive: dive starts 27 → 38 (+41 %), dive speed 1.00 → 1.14 px/frame, dives
  heading to P2's side 26 % → 50 %, enemy shots toward P2 7 % → 49 %. Damage is unchanged; shields stay.
- **RC4 shot colours** – *Superseded by RC5* (P1 green `$2A` instead of yellow `$28`, same palette slot): no sprite palette had a free colour; changing palette 2 colour 3 (purple
  aliens' small diving details) was the least visible option. Every alternative changed something
  bigger: the P2 ship's nose (palette 0 colour 3), enemy bullets and stars (palette 0 colour 1).
- **RC5 player colours and ships** (analysis of all sprites drawn in 36 000 frames of co-op and 1P play,
  tile × palette × colour index; palettes from `$E1B4`):

  | Palette | Colours 1 / 2 / 3 | Used by |
  |---|---|---|
  | BG 0 | `$16` red / `$30` white / `$2C` cyan | HUD text, **P1's ship** (BG tiles `$60–$63`, rows 26–27) |
  | sprite 0 | `$30` white / `$11` blue / `$27` orange | P2's ship (all 3), P2's shots (3), enemy bullets `$37` (1), score pop-ups `$80–$8B` (1), stars (1) |
  | sprite 1 | `$16` red / `$11` blue / `$27` orange | red divers, flagships `$A4–$BF`, explosions `$70–$7F` (colour 3 on many pixels), stars |
  | sprite 2 | `$23` purple / `$11` blue / `$27` orange | purple divers (colour 3: 2 px per diver), **P1's shots** (3), stars |
  | sprite 3 | `$1A` green / `$11` blue / `$27` orange | green divers (colour 3: 2 px per diver), stars |

  Stars (tile `$32`) use colour 1 only, so colour 3 of a palette is never a star. P1's green had to
  replace an existing colour 3: palette 2 (the RC4 slot) changes 2 px of the rarer purple diver; palette 3
  would change the much more frequent green divers, palette 1 the explosions and flagships, palette 0 P2's
  nose. `$2A` (cynes RGB 76, 208, 32) is clearly lighter than the green aliens' `$1A` (8, 124, 0) and
  unlike the white enemy bullets. P2 keeps `$27` (no change). P1's ship stays as it is: it is BG palette 0
  (the HUD's); the other BG palettes have blue as colour 2, so moving the ship rows to them would turn its
  white pods blue, and changing BG palette 0 would recolour the HUD. P2's sprites get their own picture
  (`build.P2_PIXELS`, built from the left half as before), checked at build time to be symmetric and to
  have exactly P1's box (columns 2–14, rows 0–15), so the hit boxes (code, unchanged), the shot origin
  (centre column) and the OAM layout stay as in RC4. The PRG of RC5 differs from RC4 only by the
  palette byte: the CPU work is identical (tracer: 20 000 frames with identical RAM and cycle count).
- **RC6 one rule set for both modes** (audit of every condition on `COOP` / `IsCoop`): before RC6 1 PILOT
  differed in three places – the free W2 (`StageCleared` asked `IsCoop`), the respawn shield
  (`PilotDown` / `CoopPre` asked `COOP`) and `STG nn` (`StageWanted`). These now ask "a game"
  (`STATE` = 3), so the attract demo stays as it was. Everything else was already one routine for both:
  `FireShot`/`PreSplit` (slots, speeds), `ResetBoost` (death rule), `CheckW4`/`W4Tick`/`ScoreDouble`,
  `ExtraLifeCheck`/`AwardLife` (the original one-time ship `$3D` is 0 in both), `HudP1Lives`, the status
  row. The remaining mode checks are the co-op exceptions: P2 (`P2Update`, `P2Draw`, PreSplit's mask,
  `BulletHits`' pilot order), `LifeShare`, `P1OutOfLives` (game over after both), `AimDiver` /
  `BulletAimX` (target choice), `CoopHud` (co-op layout; 1P: the original flags on the right), `StageFlags` (no flags in co-op), start positions, banner wording.
- **RC6 1P HUD after co-op** (manual test report): the HUD buffer `$0690–$06BB` (streamed by `E342` to rows
  3–4, cols 20–31) is written by `CoopHud` in co-op (P2's `2UP`, score, icon, `Wn`, `Xn`). Nothing cleared
  it at a game start: the original only writes its reserve icons (`E897`, cols 21–23) and stage flags
  (`E8B2`, cols 25–29) there, and RC1–RC5's `SoloHud` blanked cols 21–23 every 4th frame. So a 1 PILOT
  game after a co-op game kept cols 20, 24, 30, 31 of the last co-op frame: the "U" of 2UP, a P2 score
  digit, P2's W digit and lives digit (reproduced on RC5 and RC6 before the fix; a 1P game from power-on
  was clean). Fix at the cause: `CoopInit` (every game start, before `FA41`) blanks those 24 buffer cells
  (`HudRightClear`); `E897` returns at once (the icons were never wanted); `E8B2` runs only outside co-op
  (`StageFlags`) – in co-op it had written flags (and from stage 6 digits) into P2's cells at stage starts
  and P1 respawns until `CoopHud` overwrote them, visible when the HUD stream hit that frame. P2's RAM
  (`$0129` score row, reset by `FCE2` at every start, `LIVES2`, `P2_STATE` 0) was already clean.
- **RC6 attract demo**: its pilot (`F518`: `F552` dodges, `F592`/`F5DB` aim and fire) presses fire when
  `$0280` = `$C8`, the original bullet resting on the ship. Since RC1 `$0280` is P1 slot 0's sprite,
  which `PreSplit` sets to `$F8` (free, hidden) before the logic, so the demo never fired. `DemoBullet`
  (at `F5A5`/`F5DF`) returns `$C8` while slot 0 is free, else its Y. In the demo P1's level is forced to
  W1 (a demo death set it to the last game's W2 unlock, or the reset copy's `$FF` before any game).
- **RC6 overdrive start and counter-attack**: the state machine is READY (`OD_PEND`, set by `CheckW4`)
  → ACTIVE (`OdStart`, after `StageCleared` set `OD_ARM`: the first E913 call with FE = 8 in which the
  new formation is fully drawn) → EXPIRED
  (`W4Tick`) / CANCELLED (`ResetBoost`). `OdStart` runs before `W4Tick`, so the start frame is the first
  of the 720. Attacks in the original start only in `F415` (every frame of play): every 4th frame the 8
  counters `$5B–$62` step; one reaching `F4CC,x` asks for a solo dive (`F48F` → `F151` from the left /
  `F173` from the right), which takes a free solo slot in `F10E` (slots 3 up to `F134`/`F13C[$65]`: 1–4
  solo divers by attack level) and the outermost alien of a column (`F1C8`: formation bit cleared, diver
  state 1, launch arc). `FC66` resets the counters at every stage and life start, so the first attack
  of a stage comes after 280+ frames (measured ~275 at stages 2–5). **The formation is drawn only after
  the stage starts**: `FC49` sets its bits `$C3–$CC`, but the nametable is empty; `EEE5` queues column
  `$C2` (9..0, then 12 idle frames; a ring `$A0–$BF`, write index `$C0`) and `EF7E` redraws one queued
  column per frame from the bits (read index `$C1`) – the formation's flapping animation does the
  drawing, so it appears column by column in the first ~21 frames of play (measured: 124 of 132 cells the
  frame before, all in the next). `OdStart` therefore collects the queued columns in `OD_COLS` and starts
  when all 10 were queued and the ring is empty – always 21 frames after the first frame of play in the
  measured starts (natural and forced clears). A launch from an undrawn column would show an alien
  leaving an empty spot. `OdAttack` calls `F151`, `F173`,
  `F151` directly in the start frame (with `$65` = 3 for the slot limit, then restored): 3 divers on
  stages 2+, 2 on a stage 1 after the wrap; the formation is already set (`FC49` at the clear), so no
  uninitialised object is touched. `AIM_TOGGLE` = 0 sends the next three dive aims to the overdrive
  pilot. Not while P1 is hit (`F415` itself does nothing then).
- **RC6 aggression profile** (all keyed on `W4_SEC`, like RC4): `SoloLimit` (one more solo diver allowed:
  the measured dive-start rate is bound by free slots, not by attempts – RC4's extra attempts gave +46 %),
  `AtkGate` 6 counter steps per 16 frames, `DiveBoost` +1 px for every diver at y mod 16 = 3, 8, 13
  (deterministic +23 %; RC4's one diver per frame gave 14 % and depended on how many dived),
  `AimShots` +1 shot per aim (the 7 enemy-shot slots stay the limit), `BulletAimX` 7 of 8 / alternate.
  RC4's `SoloGate` (attacks during the flagship window) was removed: with `SoloLimit` it gave +87 %.
- **RC4 firing order**: shots are fired in `CoopMid` after both ships moved, so a new shot starts where
  its ship is drawn in that frame (it used the ship position of the previous frame: 1–2 px behind a
  moving ship, for both pilots).

- **CPU measurement (corrected in RC3)**: the idle counter `$3A/$3B` is two instructions (`INC $3A`, then
  `INC $3B` on a wrap); an NMI between them makes one reading 256 too low and the next 256 too high.
  The measurement scripts and tests now read the interrupted PC (cynes state / NMI stack frame) and
  correct it. The RC1/RC2 "worst frame" figures (15 and 1 iterations) were such artefacts.
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
- **`$0280/$0283` (RC3)**: the original hit routines (`F381`, `F2D1/F2EF`, `F31E`) read "the bullet" from
  `$0280/$0283`, the original P1 bullet sprite. `BulletOwnerSlot` puts any pilot's shot there before a
  call; `$0280` is also P1 slot 0's sprite and `PreSplit` had already drawn it, so after a P2 hit the next
  frame showed a P1 shot where P2's shot hit (worst while P1 was dead or out: "P1 shooting from off
  screen"). `BulletHitDone` now restores the slot. `PilotDown` also hides the shot sprites at once (they
  were drawn earlier in the same frame).
- **Zero page `$23/$24` (RC3)**: the pad routine (`E580–E59C`, every frame) stores the raw `$4016` value in
  `$23` and counts microphone toggles in `$24` (Famicom microphone easter egg: 4 toggles with the reset
  counter `$0115` = 10 jump to the reset path `E23A`). Up to RC2 `BUL_X` was `$1E–$25`, so P2's shots 2 and
  3 had their X overwritten (shots flying from X 64) and a shot's X in `$24` could reach that jump. `BUL_X`
  is now `$0E–$15`; `build.py` refuses any variable on one of the 115 zero-page addresses the original
  uses directly.
- **Fire (RC2)**: the original rule `E5A8` (counter 3 while released, a press fires when it reaches 0)
  let the counter wrap from 0 to `$FF`: a held button fired again every 256 frames (~4.3 s). The first
  version of the shared engine also skipped the counter while no slot was free, so a release was missed.
  `FireShot` now updates the counter every frame, stops it at 0 (press used up) and re-arms it only on a
  release; a press while all shots fly, or while the pilot is away, is used up. `FireRearm` clears it when
  a ship comes back with the button held (P1's READY sequence does not run `FireShot`).
- **Stage clear (RC2; free W2 since RC6 in both modes)**: the clear comes from `FA52`→`FC1A`, the same path as a lost P1 ship (`E94D`
  `LDA $9F / ORA $4F`), so a pilot can be hit (exploding or waiting) at that moment. Such a pilot got the
  free W2 before and kept it after the respawn; RC2–RC3 required `PilotAlive`. RC4 (user decision, with W2
  now kept after a death): the free W2 needs `PilotComing` (in play, or hit with a reserve ship); point
  boosts still need `PilotAlive`.
- **Respawn shield (co-op; RC6: every game, 1P too, not the demo)**: `PilotDown` sets 240 frames; `ShieldTick` (from `CoopPre`, once per
  game-logic frame) counts only while the ship is in play, so the 4 s start when the ship is back. P1:
  the shield is ORed into `P1_BLOCK`, which only the two hit checks read; P2: `P2Alive` skips both
  collision routines. Blinking: P2's sprites are hidden in `P2Draw`; P1 is background, so `P1Blink`
  writes `$2001` = `$16` (background off, sprites on) right after the ship split – the ship and nothing else
  is below it during play – and `E280` writes `$1E` at the next frame start. No nametable or OAM writes,
  no extra sprites, timing of both splits unchanged.
- **Top line**: in play the original scrolls with Y=`$FF`, so screen line 0 shows nametable row 31 = the
  attribute table read as tiles → the white dashes. `ScrollFix` uses Y=`$EF` with nametable `$2800` (like
  the title screen): line 0 comes from the blank row 29 of `$2800`, line 1 onward is unchanged.
- **Top-left "0"**: free sprite slots have Y=0 (that is how the game marks them free) and tile `$00` from
  `F753`; they showed on lines 1–8. `ClearOam` gives them the blank tile `$10`.
