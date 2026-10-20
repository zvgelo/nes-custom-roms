# Testing history – Galaxian Coop (RC1–RC5)

> **Historical / superseded.** This file keeps the test notes, measurements, manual test results and
> checklists of release candidates RC1–RC5 for regression tracking and reverse engineering. The rules
> they describe – for example W3 at 5000 points, a 30-second W4 started at once by points, a death always
> back on W1, no shield and no `STG` in 1 PILOT, the free W2 only in co-op, yellow P1 shots, red lasers,
> `GREAT SHOT` / `W4 RED LASER` messages – are **not** the current behaviour. Current rules: the game's
> [README](../../README.md); current tests and results: [TESTING.md](../TESTING.md).

## Tests updated when the rules changed (RC4–RC6)

RC6 updated (rules changed, not removed): `test_boost_thresholds` (1P gets the free W2), `test_stage_counter`
(1P shows `STG`), `test_single_player_has_no_shield` → `test_shield_single_player`, the shield tests run
in 1P too, `test_w4_red_laser` / `test_overdrive_lasts_30_seconds` (READY → next stage, 12 s).

RC5 updated (not removed): `test_shot_colours` (P1 green; all 8 slots, both pilots firing in the same
frames, after a death and after a Life Sharing revive), `test_palette_only_one_colour_changed` (`$2A`).
The RC5 visual tests write pictures to `build/screenshots/` (not in git; `tools/nestest.save_png`, no
image library needed): `ships.png` (both ships side by side, ×8) and `w4_w4.png` (both pilots in
overdrive in real play, ×3).

RC4 changed rules, so these older tests were updated (not removed): `test_boost_thresholds` (W3 at
3999/4000 instead of 4999/5000), `test_weapon_levels` and `test_fire_one_shot_per_press` (P1's shots use
sprite palette 2), `test_w4_red_laser` (row 2 shows the countdown, not "W4 RED LASER"),
`test_hud_scores_follow_points` (the score copy comes in the 2 frames after a kill), the lives/HUD tests
(the HUD is refreshed within 12 frames), `test_w4_stress_no_overrun` (overdrive with aggression kept on).
The test helper `nametable()` read 32 bytes into the second nametable up to RC3; fixed.

## Measurements RC1–RC5

**RC5 (ROM `d83b9896…`)**: the PRG is RC4's except the palette byte `$E1CF` (data loaded once at reset);
CHR changes only tiles `$E1`/`$EA`. Tracer, same input on RC4 and RC5, 20 000 frames of co-op (W4 phases
included): RAM identical in every frame, identical APU writes, identical CPU cycle count (606 780 229).
Stress in cynes with the RC4 script (`stress_rc4.py`: both pilots on W4 with the overdrive and its
aggression kept on, 8 shots, x2 scoring, lives kept, firing all the time; corrected counter):

| Scenario | RC4 | RC5 |
|---|---|---|
| both on W4, 24 × 3 min | 100 | **96**, 0 resets, 0 lag frames |
| same with both shields kept on (blinking), 24 × 3 min | 74 | **73**, 0 resets, 0 lag frames |

cynes starts with a random power-on state, so these sessions are not the same games as RC4's. RC4 and
RC5 were then run in lockstep from one saved state with the same input (`stress_pair.py`, 24 + 24
sessions × 3 min, same scenario): the idle value is identical in every frame, so is each session's worst
(no frame differs): no performance change.

**RC4 (ROM `670f347b…`, corrected counter, scripts in the session scratchpad: `stress_rc4.py`,
`margin2.py`, corpus replays)**:

| Scenario | Worst frame (idle iterations, ~10 cycles each) |
|---|---|
| RC4 1 PILOT, 4 × 2 min random input | 546 (RC3 596) |
| RC4 co-op W1, same | 477 (RC3 494) |
| RC4 both pilots in overdrive (W4 + aggression kept on), firing, 24 × 3 min | **100** (~1000 cycles), 0 resets, 0 lag frames |
| same with both shields kept on, 24 × 3 min | **74** (~740 cycles), 0 resets, 0 lag frames |
| RC4 before the RC4 CPU changes, same scenario, 12 + 12 sessions | 12 / 63 – one frame almost full |

The overdrive aggression makes the W4 scenario much denser than RC3's (7 divers, a flagship group
starting, 8 lasers, 6–7 enemy shots at once), so the RC3 figures (116 / 127, no aggression) are not the
same test. The heaviest saved frames were profiled by replaying them on ROM variants with single
routines stubbed out; the RC4 CPU changes were: HUD buffer streamed every 4th frame (was every frame;
the whole HUD still reaches the screen within 8 frames, a change within 12), the score copy moved to the
2 frames after a kill, the diver hit loop rewritten (23 instead of 30 cycles per diver and shot), the
dive boost doing one diver per frame, the status row on frames 2 mod 4. On the 16 heaviest saved frames
the worst went from 14 to 54 iterations (same states). Stack: deepest write `$0133` (as RC3; the
original `$013A`).

**Sprite limit (RC4)**: in natural co-op play (6000 frames each, W1 and W4, FCEUmm and cynes, which both
drop the 9th sprite on a line) no player shot was ever hidden; with enemies frozen by a test (their
sprites left on screen) shots were hidden on the formation's lines – a test artefact, now avoided.

**CPU margin (RC1)** – the main loop only counts (`INC $3A`, ~10 cycles per iteration); the smallest count
between two NMIs is the CPU time left in the worst frame. 4 sessions × 2 min random input each:

| ROM / mode | Worst frame (iterations) |
|---|---|
| Original, 1 player | 349 |
| Galaxian Coop, 1 PILOT (W1) | 350 |
| Galaxian Coop, 2 PILOTS CO-OP (W1) | 329 |

**Measurement correction (RC3).** The idle counter `$3A/$3B` is incremented in two instructions; an NMI
between `INC $3A` (wrap to 0) and `INC $3B` makes one reading 256 too low and the next 256 too high.
All figures marked RC1/RC2 below were taken without correcting this, so their worst-frame values are
too low (the RC2 "1 iteration" frames measure 257–332 when read correctly). RC3 scripts and the two
stress tests read the interrupted PC and correct it.

**RC3 (ROM `aa33c6b0…`, corrected counter)**:

| Scenario | Worst frame (idle iterations, ~10 cycles each) |
|---|---|
| Original, 1 player, 4 × 2 min random input | 349 |
| RC3 1 PILOT, same | 596 |
| RC3 co-op W1, same | 494 |
| RC3 W4 stress, both firing, 24 × 3 min | **116** (~1160 cycles), 0 resets, 0 lag frames |
| RC3 W4 stress with both shields kept on, 24 × 3 min | **127** (~1270 cycles), 0 resets, 0 lag frames |
| RC2 W4 stress, 12 × 3 min, corrected | 67 (~670 cycles), with shields 92 |

The 15 heaviest saved W4 frames (identical replays, same states before/after the change): worst 78 → 115,
mean 172 → 207 iterations with the `HudScores` change. The heaviest frames all had the VRAM queue full,
3–5 divers and 7–8 shots; the original's routines dominate (diver update ~2950 cycles, attack start up
to ~3800, movement tables ~1700, HUD/hi score ~820 before the change); the co-op bullet engine ~1400.

**RC2 (ROM `14fd8266…`)** – normal play, 4 × 2 min random input: 1 PILOT 459, co-op 327 iterations in the
worst frame (the new fire rule changes how these random games go, so 1P is not directly comparable).
W4 stress, 24 sessions × 3 min, both pilots on W4 firing: **0 resets, 0 lag frames**, worst frame 1 idle iteration (~10 cycles), per-session worst 1–242. The same with both shields kept
active (blinking every frame, collision checks skipped): **0 resets, 0 lag frames**, worst frame 3 iterations (~30 cycles), per-session worst 3–185. The margin in the very worst W4 frames is smaller than in RC1 (15): the frame is used almost to the end, and the lag-frame guard (`NmiGuard`) is the safety net; it did not trigger in any of the 48 sessions.

**RC1 W4 stress** – both pilots kept on W4 and fed lives, firing all the time, random movement, 3 min per
session, 24 sessions (seeds 0–23): **0 resets, 0 lag frames**; the worst frame left 15 idle iterations
(~150 cycles); per-session worst values 15–247. Before the last optimisations (extra-life gate, no ready-
bullet redraw on hit frames) the worst frame had 0 iterations left.

The NMI routine can run past the next NMI only in such W4 frames (formation kill + full VRAM queue).
The game then shows one lag frame (`NmiGuard`, counted in `LAG_TOTAL` `$067E`) instead of the original's
reset; the reset still happens after 8 overlapping NMIs in a row.

## Manual test results RC1–RC4

**RC1 in manual emulator testing (by the user, 2026-10-18)** – PASS: title screen, diagonal `CO-OP` badge,
its animation and credits; no white dashes and no `0` at the top; 2-player mode with both pads and
separate ship positions; life sharing by SELECT at X0 with the +200 bonus. Found: weapon-boost bugs (held
fire, W2 after a death, free W2 after stage 1) – fixed in RC2. Other RC1 items not fully checked yet.

**RC2: not tested outside cynes yet** (no Mesen 2, RetroArch or hardware run). RC2 is
not accepted until it is tested manually in an emulator.

**RC3 in manual emulator testing (by the user)** – PASS: no ghost shots after P1's death, P1/P2 same shot
speeds, one shot per press, death resets the weapon and removes shots, shield ~4 s, W4 lasers and
GREAT SHOT, smooth with both on W4, HUD updates. FAIL: some P2 shots on W2–W4 not starting at the ship;
W2 after stage 1 not always for both; wrong characters in P1's score (photos) – see CHANGELOG RC4.

**RC4 in manual emulator testing (by the user)** – 11/12 PASS: scores and hi score without glitches, all shot
positions, free W2 after stage 1, W2 kept after a death, W3 after 4000 more, stage counter, overdrive
(30 s, countdown, sounds, x2, aggression, back to W3), no slowdown, game over and back to the menu.
FAIL: P1 yellow / P2 orange shots too easy to confuse; remark: the two ships look too much alike.

## Manual checklists RC2–RC5

RC5 checklist:
1. P1's shots bright green, P2's orange on W1–W4 (lasers too), in 1 PILOT and co-op; easy to tell apart
   from each other, from the green aliens and from the white enemy bullets.
2. P2's ship: delta nose with a white cockpit, flat-topped pods, split tail fins; P1's ship unchanged.
   Both recognisable at a glance, also side by side and when they overlap.
3. Respawn shield: both ships blink for ~4 s and come back whole (no missing or stray pixels).
4. Diving purple aliens: 2 small pixels are green (were orange; RC4 yellow) – note if it is distracting.
5. Same smoothness as RC4 with both pilots in overdrive.

RC4 checklist:
1. Score: P1 and P2 scores, hi score, `Xn`, `Wn` contain only correct digits during long play, in pause,
   with P1 out and the revive message, after a game over on the title screen.
2. Shots: P1 yellow, P2 orange on W1–W4; every shot (all 4 slots) leaves from the middle of its ship,
   also while moving and at the screen edges; W4 lasers centred.
3. Stage 1 cleared with both ships in play: `W2` / `W2`. A pilot exploding or waiting for its ship at that
   moment (with a ship left) also gets W2 and comes back with it; one hit on its last ship gets none.
4. W3 needs 4000 points after W2 plus a cleared stage. After a death a pilot who had W2 comes back on W2.
5. Overdrive: jingle once, `GREAT SHOT`, `W4 30s` countdown above the pilot (P2's above `2UP`), zap sound per
   shot, doubled points, more and faster attacks aimed at that pilot; after 30 s back to W3, x1, calm
   enemies; pause stops the countdown; once per life.
6. `STG 01`, `02` … above the hi score in co-op; nothing on that line in 1 PILOT.
7. Smooth play with both pilots in overdrive; no stutter, no reset.

RC3 checklist:
1. Co-op, P2 on W2+ firing while P1 explodes, waits for READY and is out (X0): no shot appears for P1
   anywhere, also not for a single frame where P2's shot hits.
2. P2 on W2–W4: every shot leaves from P2's ship (before RC3 the 2nd/3rd shot could start far left).
3. P1 and P2 on the same level side by side: same shot speed and reaction to FIRE.
4. Long play with both on W4: no stutter, no reset; scores and hi score update at once on screen.

RC2 checklist (in addition to the lists below):
1. Hold FIRE on W1–W4: one shot only; press repeatedly: up to 1/2/3/4 shots, no more.
2. Die on W2+: back on W1, your shots disappear at the moment of death; the partner keeps its level.
3. Keep FIRE held while your ship comes back: no shot until you press again.
4. Clear stage 1 in co-op with both ships alive: `W2` / `W2`; with one pilot exploding at that moment (ship
   left): both get W2 (RC4).
5. Respawn shield: the ship blinks for ~4 s (fast in the last second), enemy bullets and divers pass
   through it, it moves and fires; then it can be hit again. Revive by SELECT: only the revived ship
   blinks. 1 PILOT: no blinking.
6. During P1's blinking: no flicker or garbage elsewhere on screen (P1 is hidden by turning the
   background off below the ship split).
