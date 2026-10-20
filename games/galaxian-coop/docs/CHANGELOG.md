# Changelog – Galaxian Coop

Output of each version: `build/Galaxian_Coop.nes` from `Galaxian (Japan).nes`
(SHA-256 `1188cedf…3613e`). Earlier versions can be rebuilt from their git commit – see
[history/COMMIT_MAP.md](history/COMMIT_MAP.md) for the published commit of each stage.

## 2026-10-20 – license, README redesign and documentation audit (no change to the game)

- MIT License for the project's own work (`LICENSE` in the repository root), `THIRD_PARTY_NOTICES.md` for
  what it does not cover (the original game, quoted original bytes, screenshots).
- README redesigned (hero artwork, READY/ACTIVE side by side, weapon and overdrive tables; laser colour
  corrected: pilot's colour, not red); Polish translation `README_PL.md`.
- Documentation audit: TESTING reduced to the current RC6 state (older results in
  `docs/history/TESTING_HISTORY.md`), MEMORY_MAP status/message rows updated, superseded design notes
  labelled in REVERSE_ENGINEERING, historical sections labelled in IMPLEMENTATION_REPORT,
  `STAGE1_NOTES.md` moved to `docs/history/`, `docs/history/COMMIT_MAP.md` added.
- `docs/history/COMMIT_MAP.md` lists the published commits; development commit IDs are no longer quoted.
- Code, patch and ROM unchanged: SHA-256 `7e5d4fd1…`, BPS 5213 bytes.

## 2026-10-20 – public documentation (no change to the game)

- README rewritten for a public repository: rules of RC6 (READY → next stage → 12-second overdrive with
  the counter-attack), controls, installation by BPS patch or from source, generic emulator setup,
  screenshots. Root README in English for both games, with a legal notice.
- Screenshots in `assets/screenshots/`: frames of the RC6 ROM in the cynes emulator (×3, no filtering).
- References to one private test setup replaced by neutral wording ("manual emulator testing");
  IMPLEMENTATION_REPORT marked as historical (RC1–RC5 rules superseded).
- Code, patch and ROM unchanged: SHA-256 `7e5d4fd1…`, BPS 5213 bytes.

## 2026-10-19 – RC6: one rule set for 1 PILOT and co-op, overdrive READY → next stage (branch `game/galaxian-coop`)

Result: SHA-256 `7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca`, `patches/Galaxian_Coop.bps` (5213 bytes). Not yet tested manually.

### Changed – 1 PILOT = a co-op pilot
- **Free W2 for the first cleared stage 1 in 1 PILOT too** (was co-op only), with the same rule: also for
  a pilot exploding or waiting for its next ship, not for one hit on its last ship; once per game; a new
  game resets it. Not in the attract demo.
- **Respawn shield in 1 PILOT** (4 s, blinking, moves and fires; the same routine as co-op's P1). Not in
  the demo, not at a new game or a stage change without a death.
- **`STG nn` in 1 PILOT** (same routine and field as co-op). The original stage flags (rows 3–4, right)
  stay: they come from the same stage number and always agree.
- Audit of every mode-dependent condition: the remaining ones are the co-op exceptions (second ship and
  pad, separate lives/scores, life sharing, game over after both, target choice, HUD layout, start
  positions). Weapon levels, death rule, overdrive, x2, extra lives and the HUD fields were already shared.

### Changed – Red Laser Overdrive
- **W3 + 8000 no-death points now make the overdrive READY**, not active: the pilot stays on W3 (x1, no
  aggression, no countdown); `OVERDRIVE READY NEXT STAGE` (1P) / `P1 W4 READY NEXT STAGE` (co-op) for 2 s,
  `W4 RDY` in the pilot's HUD field.
- **It starts with the next stage, in the first frame its formation is on screen** (the game draws a new
  formation column by column during its first 21 frames of play): W4, **12 s** (720 frames; was 30 s), x2,
  jingle, `OVERDRIVE!` / `P1 OVERDRIVE!` / `P1 P2 OVERDRIVE!` (replaces `GREAT SHOT`), `W4 12s`.
- **Counter-attack in that same frame**: 3 aliens leave the formation through the game's own solo-dive
  routine (no wait for the attack timer, ~4–5 s at a stage start); their dives go for the overdrive pilot.
  Never from columns not drawn yet: an earlier version started in the stage's very first frame of play,
  when the screen showed no formation yet (only its bits were set) – found on a screenshot and changed.
- **Stronger aggression for the 12 s** (all keyed on the running countdown, nothing left afterwards):
  one more solo diver allowed at a time (`SoloLimit`, attack level +1, at most the game's top), attack
  counters 6 steps per 16 frames (RC4: 5), dives ~23 % faster (every diver +1 px at y mod 16 = 3, 8, 13;
  RC4: ~14 %), +1 enemy shot per dive aim, enemy shots at P2 7 of 8 (RC4: 3 of 4), both pilots in
  overdrive: shots alternate. RC4's "solo attacks during the flagship window" is dropped (too strong
  together with the slot limit).
- Cancelled by a death (also while READY), not given back by a revive; a stage-number wrap can't start
  it twice.

### Fixed
- **1 PILOT after a co-op game showed P2 leftovers on the right of the HUD** (manual test report; reproduced
  on RC5 and RC6): the "U" of `2UP`, a P2 score digit, P2's `W` and lives digits (rows 3–4, cols 24 and
  30) stayed from the last co-op frame, because nothing cleared that part of the HUD buffer at a game
  start. Every game start now blanks it (`HudRightClear`); the original reserve-ship icons (`E897`) are
  no longer drawn at all (they were overwritten every 4th frame before); in co-op the original stage
  flags (`E8B2`) are not written into P2's cells any more (they could flash there at a stage start or a
  P1 respawn). 1P keeps the original flags (cols 25–29; from stage 6 one flag and the stage number).
- **No stage counter in 1 PILOT** (manual test report): `STG nn` now in both modes (see Changed).
- **The attract demo never fired since RC1**: its pilot fires when `$0280` = `$C8` (bullet resting on the
  ship); the shared bullet engine hides P1's slot 0 sprite there before the logic runs. `DemoBullet`
  gives the demo the original view; the demo always uses W1 (it used the last game's W2 unlock after a
  death in the demo).

### Measurements (cynes, details in TESTING.md)
- 12-s windows at stage starts 2–5 (8 sessions per mode): dive starts 3.25 normal / 4.0 RC4 profile /
  **5.75 RC6** (+77 % vs normal), first attack at frame ~275 / ~220 / **20** (frames from the stage's first frame of play; RC6: F0, the
  formation's last column drawn), enemy shots 6.5 / 11.1 / 17.2,
  dive speed 1.00 / 1.14 / 1.23.
- CPU: 0 resets, 0 lag frames in all stress runs; worst frames 100 (both W4), 44 (both W4 + shields),
  168 / 83 (1P W4 / + shield); the previous ROM in the same runs: 83 / 37. Activation frames ≥ 225.

### Tests
- New: 1P/co-op parity (start, free W2, thresholds, overdrive, aggression, death, extra lives, stage
  counter, HUD in pause and game over, no P2 in 1P, shots), demo, shield in 1P; overdrive READY, frame-exact
  counter-attack, both pilots, cancel cases, READY on the last kill, once per start, READY HUD; tracer:
  jingle at the start frame, 1P sounds; FCEUmm: overdrive start and 1P rules.
- Updated (rules changed): `test_boost_thresholds`, `test_stage_counter`, `test_shield_blinking`,
  `test_shield_blink_silhouettes`, `test_no_shield_at_game_or_stage_start`,
  `test_shield_blocks_diver_collisions`, `test_double_score_extra_life_and_hi_score` (both modes);
  `test_single_player_has_no_shield` → `test_shield_single_player`; `test_w4_red_laser`,
  `test_overdrive_lasts_30_seconds` → `…_12_seconds`, `test_overdrive_independent_pilots`,
  `test_overdrive_aggression`, `test_hud_in_overdrive`, the tracer jingle test.

## 2026-10-18 – RC5: player visual identity (branch `game/galaxian-coop`)

Result: SHA-256 `d83b98968846b24a91d17a8564df82e5c354909b3806b5a932f28dee2f6c0c03`, `patches/Galaxian_Coop.bps` (4735 bytes). After the RC4 tests on the
manual emulator testing (11/12 PASS; FAIL: P1 yellow and P2 orange shots too easy to confuse; the ships
look too much alike).

### Changed
- **P1's shots bright green** `$2A` (were yellow `$28`), all levels, lasers too, 1 PILOT included; P2's
  stay orange `$27`. Same palette byte as RC4 (`$E1CF`, sprite palette 2 colour 3). `$2A` is much lighter
  than the green aliens (`$1A`) and unlike the white enemy bullets.
- **P2's own ship**: delta nose with a white cockpit instead of the round dome, flat-topped pods,
  split tail fins; same colours (orange, blue, white), same 13 × 16 box and centre, same 4 sprites,
  same hit boxes and positions. P1's ship is unchanged (it uses the HUD's background palette, see
  REVERSE_ENGINEERING.md §7).
- Side effect (as in RC4, other colour): 2 px of a diving purple alien are green instead of orange.

### Not changed
- Program code: the PRG differs from RC4 only by the palette byte (data). Speeds, slots, damage,
  scoring, overdrive time and sounds are as in RC4. Tracer: identical RAM, APU writes and CPU cycles
  over 20 000 frames.

### Tests
- 7 new cynes tests (ship pictures pixel by pixel, P2's OAM use, hit boxes, laser shape and colours,
  enemy colours in real play, shield blink pictures, HUD in overdrive); `test_shot_colours` rewritten;
  FCEUmm: shot hue check and a ship silhouette test. Screenshots in `build/screenshots/`
  (`tools/nestest.save_png`).

## 2026-10-18 – RC4: score HUD fix, overdrive, shot colours, stage counter (branch `game/galaxian-coop`)

Result: SHA-256 `423f4be6d698caeff618a6a035cdd752eb007ffa8281c5af60a0f715be25af6c`,
`patches/Galaxian_Coop.bps` (4735 bytes). Bugs and requests after RC3 tests in manual emulator testing.

### Fixed
- **Wrong characters in P1's score** ("2130G0", "4140.0", extra tiles after 14530): RC3 had put two
  variables at `$011D/$011E`, which the original copies with the score row into the HUD (`E307`), so
  the dive toggle and a 0 showed right of P1's score (letters are red in that palette). RC2 had also
  put the shield and HUD flag at `$0126–$0128`, which the original writes to the title screen after GAME
  OVER. The score values in RAM were always right. All five variables moved to unused RAM; `build.py`
  now checks new variables against a traced list of the RAM the original uses (`src/original_ram.txt`).
- **Lasers 1 px left of the ship's centre** (also of the x the hit tests use): new centred laser tile.
- **Shots started 1–2 px behind a moving ship** (both pilots): shots are fired after the ships moved.
- **W4 lasers could pass through a diving enemy** (tested every other frame, 12.8 px apart vs a 13-px
  window): lasers have a 17-px window, matching the 4 px longer laser sprite.
- Test helper `nametable()` read the wrong offset of the cynes state (one RC2 test compared other bytes).

### Changed
- **W3**: 4000 boost points counted from when W2 was given (was 5000); no surplus carried over.
- **Free W2 also for a pilot waiting for its ship**: a pilot hit just before the first stage clear in
  co-op, with a reserve ship coming (exploding or waiting), now gets the free W2 and comes back with it;
  only a pilot hit on its last ship or already out gets none (was: only pilots in play at that moment).
- **W2 kept after a death** once unlocked (W1 only if never unlocked); same for a revive by SELECT. A death
  resets W3 progress, no-death points and overdrive.
- **W4 is now "Red Laser Overdrive"**: 30 s of play (pause and stage changes don't count), once per life,
  then W3; lasers in flight finish with their speed and look; x2 points for the pilot's own kills; rising
  jingle on activation (triangle) and a laser zap per shot (pulse 2); enemies more aggressive while any
  overdrive runs (+25 % attack attempts, solo attacks not held back by the flagship window, dives ~14 %
  faster, dives and enemy shots biased toward the overdrive pilot); nothing stays after it ends.
- **Shot colours**: P1 yellow, P2 orange on all levels (sprite palette 2 colour 3 → yellow `$28`).
- **HUD row 2**: stage counter `STG 01` (co-op) and each pilot's overdrive countdown `W4 30s`; messages now
  use row 1 only ("W4 RED LASER" second line dropped; the countdown shows W4).
- CPU: HUD buffer streamed every 4th frame (whole HUD within 8 frames), score copy in the two frames
  after a kill, cheaper diver hit loop. Worst frames: see TESTING.md.

### Not reproduced
- "Not all P2 shots on W2–W4 start at the ship": no case in cynes or FCEUmm (RAM, OAM and pixels, every
  slot, moving ships); the two real offsets found (laser 1 px left, shots 1–2 px behind a moving ship) are
  fixed.
- "Both living pilots don't always get W2 after stage 1": in 45 natural stage-1 clears a pilot missed W2
  only when exploding or waiting for its next ship at that moment (P1's next ship waits until all divers
  are back, which can take long in co-op).

### Tests
- cynes: 82 tests (21 new, 7 updated for the changed rules), FCEUmm: 4 (1 new), tracer (sound, tune RAM): 4 (new).

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

## 2026-10-18 – Stage 2 (published as part of `b054f37`, branch `game/galaxian-coop`)

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
