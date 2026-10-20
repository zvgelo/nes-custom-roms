# Testing – Galaxian Coop

Current state: **RC6**, ROM SHA-256 `7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca`.
Older results, measurements and checklists (RC1–RC5, superseded rules) are in
[history/TESTING_HISTORY.md](history/TESTING_HISTORY.md).

| Suite | Runs in | Tests | Last result (2026-10-20, Linux, Python 3.14) |
|---|---|---:|---|
| `tests/test_coop.py` | [cynes](https://pypi.org/project/cynes/) 0.1.2 (headless NES emulator) | 112 | **112/112 OK** (~650 s) |
| `tests/test_fceumm.py` | FCEUmm core through `stable-retro` 1.0.1 | 8 | **8/8 OK** |
| `tests/test_trace.py` | 6502 tracer `tools/trace6502.py` (no extra packages) | 5 | **5/5 OK** |

Automatic tests are not a substitute for play testing: see [Manual test checklist](#manual-test-checklist).

## Running the tests

From the repository root, with the original ROM in `games/galaxian-coop/private/` (or its path in
`GALAXIAN_ROM`):

```bash
pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
python3 games/galaxian-coop/tests/test_coop.py -v
python3 games/galaxian-coop/tests/test_trace.py -v
pip install stable-retro
python3 games/galaxian-coop/tests/test_fceumm.py -v
```

Without the ROM every test that needs it is skipped; without cynes only the 8 build tests of
`test_coop.py` run; without `stable-retro` the FCEUmm suite is skipped. The tests build the ROM
themselves in a temporary folder. cynes' power-on state is not deterministic, so tests that compare two
runs load one saved state into both machines.

## Test catalogue (current behaviour)

Some test names come from earlier versions (e.g. `test_w4_red_laser`, `test_revive_comes_back_on_w1`);
what they check today is described here. The suite was updated together with the rules – no test was
removed without a replacement (see the history file).

### Build and files (`test_coop.py`, 8)

| Test | Checks |
|---|---|
| `test_reproducible` | two builds give identical bytes |
| `test_original_untouched` | the original ROM is not modified (SHA-256) |
| `test_header`, `test_vectors` | NES 2.0, mapper 0, 32 KiB PRG, 8 KiB CHR; NMI `$E20C`, RESET/IRQ `$E020` |
| `test_original_code_only_changed_at_patches` | the original program differs only inside `.patch` blocks |
| `test_stage1_hook_removed` | `$E57A` keeps its original bytes (no `$07F0` use) |
| `test_bps_patch` | BPS: original → ROM round trip; no 32-byte run of the original ROM stored in the patch |
| `test_chr` | only the documented CHR tiles change |

### Emulator (`test_coop.py`, cynes, 104)

| Area | Tests | Checks |
|---|---|---|
| Picture fixes | `test_chr_change_invisible_on_title`, `test_top_line_blank`, `test_original_has_top_line_dashes`, `test_no_stray_zero_top_left` | title/demo pixel-identical with the original CHR; screen line 0 empty in play (the original draws dashes there); no `0` sprite top-left |
| Title | `test_title_text`, `test_title_after_game_over`, `test_title_badge` | `1 PILOT`, `2 PILOTS CO-OP`, credit; title intact after a game over; `CO-OP` badge |
| Modes | `test_one_player_has_no_p2`, `test_select_in_one_player_game`, `test_solo_no_p2_in_overdrive` | 1 PILOT: no P2 sprite, shot, points or state, pad 2 and SELECT do nothing, also with P1 in overdrive |
| 1P / co-op parity | `test_parity_start`, `test_parity_free_w2`, `test_parity_progression`, `test_parity_overdrive`, `test_parity_death_weapon`, `test_parity_extra_lives`, `test_parity_shots` | the same scenario in both modes gives the same result: start `X3`/`W1`, free W2 (once, also for a pilot with a ship coming, not on the last ship), 1999/2000 and 3999/4000 thresholds, READY at 8000, overdrive (12 s, x2, 4 lasers, once per life), death rule, extra lives 7000/14000/21000 and cap 9, shot timing and speeds |
| Co-op basics | `test_independent_movement`, `test_p2_shots_score_for_p2`, `test_p2_death_respawn_and_lives`, `test_spawn_positions` | independent ships, points to the owner, P2 respawn, start positions |
| Game over | `test_game_over_only_when_both_out`, `test_game_over_scatter_ignores_pad2` | game over only after both pilots; the old `$07F0` regression |
| Fire and weapons | `test_weapon_levels`, `test_fire_one_shot_per_press`, `test_weapon_parity`, `test_shots_centred_on_ships`, `test_boost_thresholds`, `test_w3_needs_4000_after_w2`, `test_first_stage_boost_coop`, `test_stage_one_boost_for_pilots_in_game`, `test_stage_one_boost_natural` | 1–4 shots at 100/110/120/160 %; one shot per press; P1 and P2 identical; shots centred on the ship; W2/W3 thresholds and the free W2 (also after natural stage-1 clears by a bot) |
| Death | `test_death_resets_weapon`, `test_death_resets_weapon_and_shots`, `test_persistent_w2`, `test_revive_comes_back_on_w1`, `test_life_share_keeps_w2_rule`, `test_p1_death_no_ghost_shots`, `test_p2_death_no_ghost_shots` | back on W2 if unlocked else W1; progress reset, score kept; shots removed; no ghost shots while away; a revive follows the same rule |
| Overdrive | `test_w4_red_laser`, `test_ready_waits_for_next_stage`, `test_ready_on_the_last_kill`, `test_ready_cancelled`, `test_ready_hud`, `test_overdrive_counter_attack_frames`, `test_overdrive_both_pilots_counter_attack`, `test_overdrive_once_per_activation`, `test_overdrive_lasts_12_seconds`, `test_overdrive_pause_and_stage_change`, `test_overdrive_independent_pilots`, `test_overdrive_shots_finish_their_flight`, `test_new_game_clears_overdrive` | READY keeps W3 (x1, no aggression); start with the next stage, frame-exact: F0 = the frame the new formation's last column is drawn, W4 12 s, jingle, 3 divers launched; one start per stage clear; exactly 720 frames; pause and stage changes don't count; independent pilots; lasers finish their flight; cancelled by death; cleared by a new game |
| Score x2 | `test_double_score_in_overdrive`, `test_double_score_extra_life_and_hi_score` | only the overdrive pilot's own kills doubled; x1 right after W4; the sharing bonus never doubled; doubled points reach extra lives and the hi score (both modes) |
| Aggression | `test_overdrive_aggression`, `test_solo_overdrive_aggression` | from one saved moment: dive starts ≥ +40 %, dive speed +18…28 %, attacks aimed at the overdrive pilot; without an overdrive two runs are identical |
| Shield | `test_shield_p1`, `test_shield_p2`, `test_shield_single_player`, `test_shield_blocks_diver_collisions`, `test_shields_independent`, `test_shield_after_life_sharing`, `test_no_shield_at_game_or_stage_start`, `test_shield_blinking`, `test_shield_blink_silhouettes` | 240 frames from the return, both modes; bullets and divers pass; moves and fires; blink pattern and exact ship pictures; none at a game or stage start |
| Life sharing | `test_share_p2_revives_p1`, `test_share_p1_revives_p2`, `test_share_blocked_cases`, `test_share_hold_and_both_pads`, `test_share_select_held_before_elimination`, `test_share_needs_new_press_after_pause`, `test_share_refused_while_partner_has_lives`, `test_share_with_both_in_play_does_nothing`, `test_revived_player_can_be_eliminated_again`, `test_revive_prompt`, `test_extra_life_from_share_bonus` | the X0/X2 rule, one transfer per new press, not in pause, +200 for the donor, prompt messages |
| Lives and extra lives | `test_lives_hud_start_and_full_game`, `test_one_player_lives_hud`, `test_extra_lives` | `Xn` through whole games; extra life at 7000 and 14000, two thresholds in one score |
| HUD | `test_hud_scores_follow_points`, `test_score_hud_values`, `test_score_hud_photo_cases`, `test_score_hud_long_session`, `test_title_score_row_clean`, `test_hud_in_overdrive`, `test_stage_counter`, `test_solo_stage_counter`, `test_solo_hud_pause_and_game_over`, `test_mode_switch_hud`, `test_solo_long_game_hud`, `test_coop_hud_no_stage_flags` | nametable and picture equal RAM (scores, hi score, `Xn`, `Wn`, `STG nn`, `W4 RDY` / `W4 nns`); pause and game over; 1P after co-op without P2 leftovers; no stage flags in P2's part in co-op |
| Graphics | `test_ship_silhouettes`, `test_p2_sprites_and_oam_use`, `test_ship_hitboxes_unchanged`, `test_shot_colours`, `test_laser_shape_and_colours`, `test_enemy_colours_unchanged`, `test_palette_only_one_colour_changed`, `test_raster_split_below_formation` | ship pictures pixel by pixel, same hit boxes; P1 green / P2 orange shots and lasers; enemy colours unchanged except 2 px; the P1 ship split stays below the formation |
| Demo | `test_demo_has_no_shield_or_boost` | the attract demo: no shield, no boost, no P2, and it fires as in the original |
| CPU | `test_w4_with_shields_stable`, `test_w4_stress_no_overrun`, `test_stress_no_crash_or_overrun`, `test_solo_w4_stress_no_overrun` | minutes of both pilots (or 1P) in overdrive with aggression and shields: no reset, no lag frame, idle margin above zero |

### FCEUmm core (`test_fceumm.py`, 8)

| Test | Checks |
|---|---|
| `test_weapon_parity_and_fire` | one shot per press, held FIRE = one shot, pool limits, P1/P2 parity on W1–W4 |
| `test_shot_origins_every_slot` | both pilots moving and firing on W1–W4: every shot starts at its ship and keeps its x; P1 green, P2 orange; no shot hidden by the sprite limit |
| `test_ship_silhouettes` | both ship pictures while moving, 3 colours each, only white shared |
| `test_p1_death_no_ghost_shots`, `test_p2_death_no_ghost_shots` | death with W4 shots flying: no shot while away; back with a shield that holds |
| `test_overdrive_starts_with_next_stage` | READY keeps W3; F0 of the next stage: W4 12 s and 3 divers launched, moving in F1–F3 |
| `test_single_player_rules` | 1 PILOT: free W2 for stage 1 and the 4-s shield |
| `test_mode_switch_hud` | co-op → GAME OVER → 1 PILOT: P2's HUD cells blank in the picture, stage flag drawn |

This is FCEUmm as built into `stable-retro` (224 × 240 picture: 8 px cropped on each side), not
RetroArch itself.

### Tracer (`test_trace.py`, 5)

`tools/trace6502.py`: a 6502 core with an NROM/PPU stub that logs every RAM, VRAM and APU write; not
cycle-exact, no picture or sound output.

| Test | Checks |
|---|---|
| `test_overdrive_jingle_once` | no jingle while READY; the 7-note triangle arpeggio once, from the frame the overdrive starts; no original code writes the triangle |
| `test_solo_overdrive_sounds` | 1 PILOT: the same jingle and the laser zap per press |
| `test_overdrive_shot_sound` | W1–W3: the original shot sound; W4: the zap; one sound per press; nothing writes pulse 1 |
| `test_tunes_unchanged` | the first 6 s of a 1P game: music writes identical to the original |
| `test_tune_ram_intact_in_play` | tune data in RAM unchanged through 3000 frames of co-op with overdrive |

## Screenshots

`../assets/screenshots/01-title.png` … `08-player-colors.png` are frames of the RC6 ROM in the cynes
emulator, saved with `tools/nestest.save_png` (×3, nearest neighbour). Title, 1P and co-op play, W2 after
a stage-1 clear and the life-sharing prompt come from play driven by the test helpers (scripted input;
lives kept up during play). For READY and overdrive (05, 06, 08) the scores, lives, stage number and
weapon level were set in RAM to values reachable in normal play (e.g. P1 12 350 points, `X4` after the
7000 extra life, W3, `STG 03`); the READY itself came from a real kill and the overdrive from the next
stage's start. Before saving, the HUD was checked against RAM (`assert_hud`).

## Measurements (RC6)

One-off emulator scripts, not part of the suite; the CPU figures use the idle counter corrected for an
NMI between its two increments (see the history file).

**Aggression** – 12-second windows at the start of stages 2–5, 8 sessions per mode, the same saved state
for all three columns:

| | normal stage | RC4 profile, same start | RC6 |
|---|---|---|---|
| dive starts / 720 frames (1P = co-op) | 3.25 | 4.0 (+23 %) | 5.75 (+77 %) |
| first attack (frames from the stage's first frame of play) | ~275 | ~220 | 20 (F0: formation drawn) |
| enemy shots / 720 frames | 6.5 | 11.1 | 17.2 |
| dive speed (px/frame) | 1.00 | 1.14 | 1.23 |

Steady state (co-op, P2 in overdrive kept on, 6 × 60 s): dive starts 4.31 → 6.30 (RC4) → 6.85 (RC6) per
1000 frames; speed 1.00 → 1.14 → 1.23; enemy shots heading toward P2 1 % → 52 % → 88 %. Dive target
decisions (tracer, 20 000 frames): one pilot in overdrive 75 % at that pilot; both 50/50; none 50/50.

**CPU** – 12 sessions × 3 min per line, overdrive and aggression kept on, 8 shots, x2, lives kept:

| Scenario | worst frame (idle iterations, ~10 cycles each) | lag frames | resets |
|---|---|---|---|
| co-op, both in overdrive, firing | 100 | 0 | 0 |
| co-op, both in overdrive + both shields | 44 | 0 | 0 |
| 1P in overdrive | 168 | 0 | 0 |
| 1P in overdrive + shield | 83 | 0 | 0 |
| overdrive start frames F0–F7, 40 starts after real play | ≥ 225 | 0 | – |

**Shot speed** (full flight from the ship to the top, P1): W1 49 frames (4.00 px/frame), W2 45 (4.40),
W3 41 (4.80), W4 31 (6.40) – 100 / 110 / 120 / 160 %.

**Raster split** – with the shortened wait and `PreSplit`, the screen above the P1 ship split is
pixel-identical to a variant with the original wait; `PreSplit` takes 1171 cycles and the split lands
37 cycles later than the original, < 1 scanline (`test_raster_split_below_formation` checks it).

## Manual test checklist

For any NES emulator (mapper 0). Automatic tests ran only in cynes, FCEUmm (stable-retro) and the tracer;
manual play testing was done in an emulator. **Not tested:** Mesen 2, other emulators and cores, real
NES/Famicom hardware, long human play sessions with two physical controllers.

1. **Title**: logo, `CO-OP` badge (red, short white glint), `1 PILOT` / `2 PILOTS CO-OP`,
   `HACK BY ZVGELO ©2026`; SELECT moves the cursor, START starts. Top line of the screen empty in play,
   no `0` in the top-left corner.
2. **1 PILOT**: `X3` / `W1` / `STG 01`; after clearing stage 1 `W2`; after a death back on W2, the ship
   blinks ~4 s and can't be hit; `STG 02` … (the flags on the right agree); pad 2 and SELECT do nothing.
3. **2 PILOTS CO-OP**: P1 left, P2 right, both move and fire at the same time; green P1 and orange P2
   shots; points to the right score; game over only after both are out.
4. **Life sharing**: P1 out → `P2 SELECT TO REVIVE P1` (or `P1 OUT`) → SELECT on pad 2 → P1 back beside
   P2, P2 −1 life and +200, P1 shielded.
5. **Overdrive READY**: on W3 score 8000 without dying → `OVERDRIVE READY NEXT STAGE` (co-op
   `P1 W4 READY NEXT STAGE`) for ~2 s, `W4 RDY` above the score; still 3 shots, normal points and enemies.
6. **Overdrive start**: clear the stage; as soon as the new formation is complete: `OVERDRIVE!`, the
   jingle, `W4 12s`, and three aliens break from the formation at once; attacks stay heavy for 12 s, then
   W3, normal enemies; lasers in flight finish. A death while READY cancels it.
7. **Both pilots READY in one stage**: both start together (`P1 P2 OVERDRIVE!`), attacks split.
8. **1 PILOT after a co-op game**: nothing of P2 on the right of the HUD.
9. **Attract demo**: the demo ship fires (as in the original).
10. **Smoothness** with both pilots in overdrive and shields: no stutter, no reset; HUD digits clean;
    watch for sprite flicker when many sprites share a line.

Optional debugging in Mesen 2: Debugger → File → Import Labels → `build/Galaxian_Coop.mlb` (label import
not tested). Useful RAM: `$05–$26`, `$45–$4A`, `$0371–$0377` (overdrive state), `$067C`/`$067E` (lag
frames).

Please report the emulator or core, its version and what worked.
