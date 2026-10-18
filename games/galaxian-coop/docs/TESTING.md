# Testing – Galaxian Coop

Three kinds of results are kept apart here:

1. **Automatic tests** – run by `tests/test_coop.py` in the cynes emulator (headless).
2. **Measurements** – one-off emulator scripts (CPU margin, bullet speeds, W4 stress).
3. **Manual tests** – Mesen 2, RetroArch, real hardware: **not done by the author of the
   code**; checklists below. A pass in cynes is not a confirmation for RetroArch or any other emulator.

## 1. Automatic tests

```bash
pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
python3 games/galaxian-coop/tests/test_coop.py -v
```

Last run: 2026-10-18, RC3, ROM SHA-256 `aa33c6b0…a851e8d`, Linux, Python 3.14, cynes 0.1.2:
**61/61 OK** (~235 s): 45 RC1 tests, 3 RC2 weapon tests, 8 respawn-shield tests, 5 RC3 tests.
Without cynes the 7 build tests run and the emulator tests are skipped.

Second emulator – FCEUmm core (the one RetroArch uses) through stable-retro 1.0.1:

```bash
pip install stable-retro
python3 games/galaxian-coop/tests/test_fceumm.py -v
```

**3/3 OK** on RC3: fire (one shot per press, held FIRE = one shot, pool limits, all shots from the
ship's X) and P1/P2 parity on W1–W4; P1 and P2 death with W4 shots flying: no shot in RAM or OAM during
the explosion, READY and wait, back on W1 with a shield that holds. The same file run against the RC2
code fails all three (ghost sprites of P1 and P2, P2 shots with two different X). This is FCEUmm in
stable-retro, not RetroArch itself.

cynes' power-on state is not deterministic; tests that compare two runs load one saved power-on state
into both machines.

### Build and files (7)

| Test | Checks |
|---|---|
| `test_reproducible` | two builds give identical bytes |
| `test_original_untouched` | the original ROM is not modified (SHA-256) |
| `test_header` | NES 2.0, mapper 0, 32 KiB PRG, 8 KiB CHR |
| `test_vectors` | NMI `$E20C`, RESET/IRQ `$E020` |
| `test_original_code_only_changed_at_patches` | the original program differs only inside `.patch` blocks |
| `test_stage1_hook_removed` | `$E57A` keeps its original bytes (no `$07F0` use) |
| `test_bps_patch` | BPS: original → ROM round trip; no 32-byte run of the original ROM stored in the patch |

### Emulator (54)

| Area | Tests | Checks |
|---|---|---|
| Graphics | `test_chr`, `test_chr_change_invisible_on_title` | only the documented CHR tiles change; 1200 frames of title/demo pixel-identical with the original CHR |
| Graphics fixes | `test_top_line_blank`, `test_original_has_top_line_dashes`, `test_no_stray_zero_top_left` | screen line 0 empty in play (the original draws the dashes); no `0` sprite top-left |
| Modes | `test_one_player_has_no_p2`, `test_select_in_one_player_game` | 1 PILOT: no P2, pad 2 and SELECT do nothing |
| Co-op basics | `test_independent_movement`, `test_p2_shots_score_for_p2`, `test_p2_death_respawn_and_lives` | independent movement, points to the owner, P2 death/respawn |
| Game over | `test_game_over_only_when_both_out`, `test_game_over_scatter_ignores_pad2` | full game: game over only after both; the `$07F0` regression |
| Lives HUD | `test_lives_hud_start_and_full_game`, `test_one_player_lives_hud` | `X3`/`X3` at start, total lives through a whole game in both modes |
| Life sharing | `test_share_p2_revives_p1`, `test_share_p1_revives_p2`, `test_share_blocked_cases`, `test_share_hold_and_both_pads`, `test_share_select_held_before_elimination`, `test_share_needs_new_press_after_pause`, `test_share_refused_while_partner_has_lives`, `test_share_with_both_in_play_does_nothing`, `test_revived_player_can_be_eliminated_again` | the X0/X2 rules, one transfer per press, no transfer in pause or from a held button, revived pilot plays and can be eliminated again |
| Title | `test_title_text`, `test_title_after_game_over`, `test_title_badge` | rows `1 PILOT`, `2 PILOTS CO-OP`, credit; title intact after a game over; `CO-OP` badge position, colours, glint, gone in play |
| Weapons | `test_weapon_levels`, `test_boost_thresholds`, `test_w4_red_laser`, `test_death_resets_weapon`, `test_first_stage_boost_coop`, `test_revive_comes_back_on_w1` | 1–4 shots and speeds per level for both pilots; 1999/2000 and 4999/5000 point limits, stage clear needed, W4 only from W3 at 8000 no-death points; W4 message and its removal; up to 8 bullets; death/revive reset to W1 without touching the score or the other pilot; free W2 once in co-op |
| Extra lives | `test_extra_lives`, `test_extra_life_from_share_bonus` | 7000 and 14000, each once, two thresholds in one score, P2 unaffected, HUD, reset on a new game; the +200 sharing bonus can cross a threshold |
| Messages / spawns | `test_revive_prompt`, `test_spawn_positions` | `P2 SELECT TO REVIVE P1`, `P1 OUT`, `P1 SELECT TO REVIVE P2`, cleared after a revive; P1 left/P2 right at start and next stage, 1P centred, revive 24 px beside the donor without moving it |
| RC2 fire | `test_fire_one_shot_per_press` | W1–W4, both pilots at once: FIRE held 120 frames = 1 shot; quick presses fill exactly 1/2/3/4 slots, the extra press is blocked; a freed slot fires on the next press; W4 shot is the red laser; P1 holding while P2 presses (and the reverse): independent |
| RC2 death | `test_death_resets_weapon_and_shots` | P1 and P2 dying on W2, W3, W4: W1, boost and no-death points 0, its shots removed, partner's level/points/shots kept; no shots while dead, partner fires on its level; FIRE held through the respawn gives no shot; then 1 shot at a time |
| RC2 stage 1 | `test_stage_one_boost_only_for_alive_pilots` | both alive: W2/W2 in RAM and in the HUD; P1 or P2 hit just before the clear: no free W2, not given after the respawn; P1 X0: only P2, not given after a revive; P2 X0: only P1 |
| Shield | `test_shield_p1`, `test_shield_p2` | shield 240 when hit, no countdown while away; one tick per game frame, 240 frames in total from the return; W1 after the respawn; enemy bullets do not hit; lives, weapon level, boost and no-death points kept; moves and fires, held FIRE = one shot; hit again once the shield is over |
| Shield | `test_shield_blocks_diver_collisions` | real diver collisions (found by play with enemy bullets removed) replayed: deadly without a shield, harmless with it, for P1 and P2 |
| Shield | `test_shields_independent` | both pilots hit together: both shielded at once with separate counters; P1 dying later keeps P2's shield, protection and weapon |
| Shield | `test_shield_after_life_sharing` | revive by SELECT: receiver shielded (both directions), donor not |
| Shield | `test_no_shield_at_game_or_stage_start`, `test_single_player_has_no_shield` | no shield at a new game or a new stage without a death; 1 PILOT: no shield, no blinking, hit right after the respawn |
| Shield | `test_shield_blinking` | P1 (background) and P2 (sprites): shown/hidden every frame as the 8/8 then 4/4 pattern, last phase hidden, visible from the frame the shield ends and for good; P2's shot stays visible; ship nametable rows and P2's sprites unchanged afterwards |
| RC3 ghost shots | `test_p1_death_no_ghost_shots`, `test_p2_death_no_ghost_shots` | real hit by an enemy bullet with 4 W4 shots flying, X2→X1 and X1→X0: shots and their sprites gone at once; through explosion, READY, wait or X0 (partner fighting on W4, both pads mashing FIRE) no shot of the pilot in RAM or OAM and no points; back (respawn or SELECT revive) on W1 with a shield, held FIRE gives nothing, a new press one shot |
| RC3 parity | `test_weapon_parity` | per level, P1 vs P2 identical: frames to the shot (2), Y in every frame, full flight 50/46/42/32 frames, X never changes, rapid presses fill exactly 1–4 slots with all shots from one X; both W4: 8 shots at most |
| RC3 | `test_w4_with_shields_stable`, `test_hud_scores_follow_points` | 1 min both on W4 with shields kept on: no reset, no lag frame; P1 and P2 points and a new hi score (P1 or P2) reach the HUD on screen |
| Stress | `test_w4_stress_no_overrun` (2 min, both on W4, firing), `test_stress_no_crash_or_overrun` (3 min random input) | no game reset, no crash; idle CPU margin > 100 iterations in normal play |

## 2. Measurements (emulator scripts, not part of the suite)

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

**Raster split** – with the shortened wait and `PreSplit`, screen lines 0–120 are pixel-identical to a ROM
variant with the original wait (co-op, co-op with 8 lasers, 1P; 12 frames each); title identical over 600
frames. So the P1 ship split happens at the same place.

**Bullet speed** (full flight from the ship to the top, P1, 1P mode):

| Level | Frames | px/frame | % of W1 |
|---|---|---|---|
| W1 | 49 | 4.00 | 100 |
| W2 | 45 | 4.38 | 109 |
| W3 | 41 | 4.78 | 120 |
| W4 | 31 | 6.39 | 160 |

(8.8 fixed point: 4.00 / 4.40 / 4.80 / 6.40; the sample is rounded by the start and end positions.)

## 3. Manual tests

**RC1 in manual emulator testing (by the user, 2026-10-18)** – PASS: title screen, diagonal `CO-OP` badge,
its animation and credits; no white dashes and no `0` at the top; 2-player mode with both pads and
separate ship positions; life sharing by SELECT at X0 with the +200 bonus. Found: weapon-boost bugs (held
fire, W2 after a death, free W2 after stage 1) – fixed in RC2. Other RC1 items not fully checked yet.

**RC2: not tested outside cynes yet** (no Mesen 2, RetroArch or hardware run). RC2 is
not accepted until it is tested manually in an emulator.

**RC3: not tested outside the emulators yet** (cynes, FCEUmm in stable-retro). RC3 checklist:
1. Co-op, P2 on W2+ firing while P1 explodes, waits for READY and is out (X0): no shot appears for P1
   anywhere, also not for a single frame where P2's shot hits.
2. P2 on W2–W4: every shot leaves from P2's ship (before RC3 the 2nd/3rd shot could start far left).
3. P1 and P2 on the same level side by side: same shot speed and reaction to FIRE.
4. Long play with both on W4: no stutter, no reset; scores and hi score update at once on screen.

RC2 checklist (in addition to the lists below):
1. Hold FIRE on W1–W4: one shot only; press repeatedly: up to 1/2/3/4 shots, no more.
2. Die on W2+: back on W1, your shots disappear at the moment of death; the partner keeps its level.
3. Keep FIRE held while your ship comes back: no shot until you press again.
4. Clear stage 1 in co-op with both ships alive: `W2` / `W2`; with one pilot exploding at that moment: only
   the other one gets W2.
5. Respawn shield: the ship blinks for ~4 s (fast in the last second), enemy bullets and divers pass
   through it, it moves and fires; then it can be hit again. Revive by SELECT: only the revived ship
   blinks. 1 PILOT: no blinking.
6. During P1's blinking: no flicker or garbage elsewhere on screen (P1 is hidden by turning the
   background off below the ship split).

Not tested by the author: **Mesen 2, RetroArch, real NES/Famicom**, sound, playability over
long games, two physical controllers. Please report the emulator/core, version and what worked.

### Mesen 2

1. Build: `python3 games/galaxian-coop/src/build.py` → `build/Galaxian_Coop.nes`.
2. Settings → Input: two controllers (Player 1, Player 2).
3. Title: logo, `CO-OP` badge (red, short white glint), `1 PILOT` / `2 PILOTS CO-OP`,
   `HACK BY ZVGELO ©2026`, Namco lines; SELECT moves the cursor, START starts.
4. Top line of the screen empty in play, no `0` in the top-left corner.
5. **1 PILOT**: original game, `X3` / `W1` in the HUD, pad 2 does nothing.
6. **2 PILOTS CO-OP**: P1 left, P2 right; both move and fire at the same time; points to the right score;
   deaths of each pilot; `Xn` counts down; P1 out → `P2 SELECT TO REVIVE P1` (or `P1 OUT`) → SELECT on
   pad 2 → P1 back beside P2, P2 −1 life, +200; game over only after both.
7. Boosts: after stage 1 in co-op both on `W2` (2 shots); W4 shows red lasers and `GREAT SHOT`.
8. Watch for: flicker with many sprites on one line, any short stutter with both on W4 (lag frames),
   the P1 ship's lower split at the extreme left/right positions.
9. Debugger (optional): File → Import Labels → `build/Galaxian_Coop.mlb` (format Mesen 2; import not
   tested). Watch `$05–$26`, `$45–$4A`, `$067C`/`$067E` (lag frames).

### RetroArch / other emulators

1. Copy `build/Galaxian_Coop.nes` to `Emulation/roms/nes/`, rescan in ES-DE.
2. Core: any NES core (mapper 0). Check Quick Menu → Information which core runs.
3. Port 1 / Port 2 controls: two different devices.
4. Repeat steps 3–8 of the Mesen 2 list; in manual testing especially the top line (white dashes before).
5. Note the core, RetroArch version, results and screenshots.
