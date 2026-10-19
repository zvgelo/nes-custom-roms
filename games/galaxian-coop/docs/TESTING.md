# Testing – Galaxian Coop

Three kinds of results are kept apart here:

1. **Automatic tests** – `tests/test_coop.py` in the cynes emulator (headless), `tests/test_fceumm.py` in
   the FCEUmm core (stable-retro), `tests/test_trace.py` in the 6502 tracer `tools/trace6502.py` (sound).
2. **Measurements** – one-off emulator scripts (CPU margin, bullet speeds, W4 stress).
3. **Manual tests** – Mesen 2, RetroArch, real hardware: **not done by the author of the
   code**; checklists below. A pass in cynes is not a confirmation for RetroArch or any other emulator.

## 1. Automatic tests

```bash
pip install -r games/galaxian-coop/tests/requirements.txt   # cynes, numpy
python3 games/galaxian-coop/tests/test_coop.py -v
```

Last run: 2026-10-19, RC6, ROM SHA-256 `7e5d4fd1ee57fd0dba4901a37002b024bee4f8987bf471b8d7341b9c0ea232ca`, Linux, Python 3.14, cynes 0.1.2:
**112/112 OK** (~640 s): the 89 RC5 tests (2 renamed, several updated for RC6, below) and 23 RC6 tests. Without cynes
the 7 build tests run and the emulator tests are skipped.

**RC6 – 1 PILOT / co-op parity** (each compares the same scenario in both modes, by RAM, nametable and
picture, and requires equal results): `test_parity_start` (X3, W1, no shield, flags, next life 7000,
`$3D` = 0, STG 01), `test_parity_free_w2` (in play, exploding with a ship coming, once per game, last ship,
new game), `test_parity_progression` (1999/2000, 3999/4000, no boost without a clear, W3 → READY at
8000, not from W2), `test_parity_overdrive` (start, banner, `W4 12s`, 4 lasers, x2, 720 frames, back to
W3, x1, once per life), `test_solo_overdrive_aggression`, `test_parity_death_weapon`, `test_parity_extra_lives`
(7000/14000/21000, cap 9, no original extra ship at 5000), `test_solo_stage_counter` (01–07, death, 99 → 01,
flags agree), `test_solo_hud_pause_and_game_over`, `test_solo_no_p2_in_overdrive`, `test_parity_shots`,
`test_solo_w4_stress_no_overrun`, `test_shield_single_player`, `test_demo_has_no_shield_or_boost` (also:
the demo fires again).

**RC6 – overdrive**: `test_ready_waits_for_next_stage` (READY: W3, x1, `W4 RDY`, the enemies identical
with and without READY), `test_overdrive_counter_attack_frames` (frame-exact, 1P and co-op: F0 = the frame the new formation's
last column is drawn, ≤ 24 frames after the first frame of play; F0 W4 12/59 +
jingle + 3 divers state 0 → 1; F1 `OVERDRIVE!` in the picture with the divers' sprites; F1–F3 they move;
the three dive targets computed from P1's position (EE52's formula); without READY the first attack only
after > 200 frames), `test_overdrive_both_pilots_counter_attack` (both start together, targets P2, P1, P2),
`test_ready_cancelled` (death, revive, game over, new game), `test_ready_on_the_last_kill`,
`test_overdrive_once_per_activation` (one jingle, one message, 6 counter steps per 16 frames from F0, no
start at the following stage, enemies identical after the end with or without the overdrive's
history), `test_ready_hud`; updated: `test_w4_red_laser`, `test_overdrive_lasts_12_seconds` (exactly 720),
`test_overdrive_independent_pilots`, `test_overdrive_aggression` (≥ +40 % starts, speed +18…28 %),
`test_hud_in_overdrive`, `test_double_score_extra_life_and_hi_score` (both modes).

**RC6 – 1P HUD (manual test report)**: `test_mode_switch_hud` (no emulator restart: 1P → 2P → 1P → 2P → 1P →
1P; each game's rows 2–4 equal RAM in the nametable and the picture, `STG 01`, 1P's right part equal to a
fresh 1P game, P2's cells blank in the picture), `test_solo_long_game_hud` (1P after a co-op game: stages
1–4, score over 10 000 and 20 000, extra lives, W2/W3/READY/W4 x2 with `STG` shown, death + shield +
W2, GAME OVER, title; every frame: no P2 leftover, no stray tile on the right), `test_coop_hud_no_stage_flags`
(co-op up to stage 7 with P1 deaths: no flag in P2's part of the buffer or the nametable). Both bug tests
were run against builds without the fix and fail there.

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

Second emulator – FCEUmm core (the one RetroArch uses) through stable-retro 1.0.1:

```bash
pip install stable-retro
python3 games/galaxian-coop/tests/test_fceumm.py -v
```

**8/8 OK** on RC6 (RC5: 5/5; RC6 adds `test_overdrive_starts_with_next_stage` – READY keeps W3, F0 of the
next stage W4 12/59 and 3 divers launched, F1–F3 moving – and `test_single_player_rules` – free W2 and
the shield in 1 PILOT): fire (one shot per press, held FIRE = one shot, pool limits, all shots from the
ship's X) and P1/P2 parity on W1–W4; P1 and P2 death with W4 shots flying: no shot in RAM or OAM during
the explosion, READY and wait, back on W1 with a shield that holds; **RC4 `test_shot_origins_every_slot`**:
both pilots firing on W1–W4 while their ships move left and right, 3600 frames: every slot of both pilots
fires, every new shot starts at its ship's x (+`$7C`), keeps its x in RAM and OAM for the whole flight,
and is drawn there (pixels: centre column x+4, 1 px bullet / 3 px laser symmetric about it), P1 in one
colour and palette 2, P2 in another and palette 0 (RC5: P1 green – G well above R and B –, P2 orange –
R > G > B); no shot hidden by the 8-sprites-per-line limit. **RC5 `test_ship_silhouettes`**: P1's and
P2's pixel masks match their expected pictures while the ships move (≥ 190 of 200 frames; a ship at the
cropped edge may not fit), 3 colours each, only white shared. The RC2 code fails the first three tests. This is FCEUmm in stable-retro (the core shows 224 ×
240 pixels: 8 cropped on each side), not RetroArch itself.

Tracer (`tools/trace6502.py`: 6502 core, NROM, PPU stub with nametables and palette, logs every RAM,
VRAM and APU write; not cycle-exact, no picture or sound output) – **5/5 OK**:

| Test | Checks |
|---|---|
| `test_overdrive_jingle_once` | RC6: no jingle while READY; the triangle (unused by the original) gets exactly the 7 arpeggio periods from the frame W4 starts at the next stage (the counter-attack frame), no second jingle during 600 more frames of kills; no original code writes the triangle |
| `test_solo_overdrive_sounds` | RC6: 1 PILOT: the jingle once at the start, the zap once per W4 press |
| `test_overdrive_shot_sound` | W1/W3 press: FEA8's shot (`$4004–$4007` = `05 84 16 08` + noise); W4 press: the zap (`82 92 50 08`, no noise); one sound per press; both pilots in one frame: the same zap twice, nothing else; no new code writes pulse 1 |
| `test_tunes_unchanged` | the first 6 s of a 1P game: pulse 1 writes (tunes, siren) identical to the original |
| `test_tune_ram_intact_in_play` | `$0150–$01FF` (tune data in RAM) unchanged through 3000 frames of co-op with overdrive |

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
| RC2 stage 1 | `test_stage_one_boost_for_pilots_in_game` (RC4: was `…_only_for_alive_pilots`) | both alive: W2/W2 in RAM and in the HUD; P1 or P2 hit just before the clear with a reserve ship: W2, back with W2 (RAM and HUD); hit on the last ship: none, eliminated; P1 X0: only P2, not given after a revive; P2 X0: only P1 |
| Shield | `test_shield_p1`, `test_shield_p2` | shield 240 when hit, no countdown while away; one tick per game frame, 240 frames in total from the return; W1 after the respawn; enemy bullets do not hit; lives, weapon level, boost and no-death points kept; moves and fires, held FIRE = one shot; hit again once the shield is over |
| Shield | `test_shield_blocks_diver_collisions` | real diver collisions (found by play with enemy bullets removed) replayed: deadly without a shield, harmless with it, for P1 and P2 |
| Shield | `test_shields_independent` | both pilots hit together: both shielded at once with separate counters; P1 dying later keeps P2's shield, protection and weapon |
| Shield | `test_shield_after_life_sharing` | revive by SELECT: receiver shielded (both directions), donor not |
| Shield | `test_no_shield_at_game_or_stage_start`, `test_single_player_has_no_shield` | no shield at a new game or a new stage without a death; 1 PILOT: no shield, no blinking, hit right after the respawn |
| Shield | `test_shield_blinking` | P1 (background) and P2 (sprites): shown/hidden every frame as the 8/8 then 4/4 pattern, last phase hidden, visible from the frame the shield ends and for good; P2's shot stays visible; ship nametable rows and P2's sprites unchanged afterwards |
| RC3 ghost shots | `test_p1_death_no_ghost_shots`, `test_p2_death_no_ghost_shots` | real hit by an enemy bullet with 4 W4 shots flying, X2→X1 and X1→X0: shots and their sprites gone at once; through explosion, READY, wait or X0 (partner fighting on W4, both pads mashing FIRE) no shot of the pilot in RAM or OAM and no points; back (respawn or SELECT revive) on W1 with a shield, held FIRE gives nothing, a new press one shot |
| RC3 parity | `test_weapon_parity` | per level, P1 vs P2 identical: frames to the shot (2), Y in every frame, full flight 50/46/42/32 frames, X never changes, rapid presses fill exactly 1–4 slots with all shots from one X; both W4: 8 shots at most |
| RC3 | `test_w4_with_shields_stable`, `test_hud_scores_follow_points` | 1 min both on W4 with shields kept on: no reset, no lag frame; P1 and P2 points and a new hi score (P1 or P2) reach the HUD on screen |
| Stress | `test_w4_stress_no_overrun` (2 min, both on W4 with overdrive and aggression kept on, firing), `test_stress_no_crash_or_overrun` (3 min random input) | no game reset, no lag frame, no crash; idle CPU margin > 100 iterations in normal play |
| RC4 score HUD | `test_score_hud_values` | 18 scores (0 … 14000) for P1 with the reverse list for P2: rows 3 and 4 of the nametable equal what RAM requires in every cell (scores, hi score = the best, labels, `Wn`, `Xn`, blanks right of the scores); rendered digits read back from the picture |
| RC4 score HUD | `test_score_hud_photo_cases` | photos from manual testing after real play (dives): 2130/2810/5000 on W1, 4140/5010 on W2, in pause and after it; P1 out (X0) at 14530, P2 on W4 at 20000 with `P2 SELECT TO REVIVE P1` on screen |
| RC4 score HUD | `test_score_hud_long_session`, `test_title_score_row_clean` | 3 min both scoring: HUD = RAM at every check, rows 0–1 only blank/banner text, row 2 only the status row; after GAME OVER the title's score row holds digits and blanks only |
| RC4 weapons | `test_w3_needs_4000_after_w2`, `test_persistent_w2`, `test_life_share_keeps_w2_rule`, `test_stage_one_boost_natural` | 3999/4000 after W2, no surplus (3500 on W1 → 0 after W2), free W2 at 800 then W3 at a 4800 total; death from W2/W3/W4 → W2 if unlocked, W1 if not, progress/no-death/overdrive reset, then 4000 needed again; revive follows the same rule; 5 natural stage-1 clears by a bot: W2 exactly for the pilots in play at the clear, unchanged through the stage change, HUD right |
| RC4 overdrive | `test_overdrive_lasts_30_seconds`, `test_overdrive_pause_and_stage_change`, `test_overdrive_independent_pilots`, `test_overdrive_shots_finish_their_flight`, `test_new_game_clears_overdrive` | 1800 normal-play frames (`W4 30s` … `W4 01s` on row 2, then blank and W3), once per life even with ≥ 8000 no-death points, again after a death; pause and stage change don't count and don't renew; two independent countdowns, a death ends only that one; lasers in flight keep 6.4 px/frame and the laser tile, new shots W3 (3 slots), slot 4 not reused; a new game clears all of it |
| RC4 x2 | `test_double_score_in_overdrive`, `test_double_score_extra_life_and_hi_score` | P1 on W4 scores only doubled values, P2 on W1 only base values; both doubled when both on W4; x1 right after W4 ends; life-sharing bonus +200 from a donor on W4; doubled points reach the 7000 extra life and the hi score, HUD right |
| RC4 aggression | `test_overdrive_aggression` | from one saved moment, 90 s with shields: P2 in overdrive vs none: dive starts +15 % or more (measured +41 %), dive speed +8…20 % (measured +14 %), more dives heading to P2 and more enemy shots aimed at P2; without overdrive two runs are identical (the hooks change nothing) |
| RC4 shots | `test_shots_centred_on_ships`, `test_raster_split_below_formation` | W1 and W4, every slot, both pilots, edge and middle positions: shot x + 4 = the ship's visible centre (RC5: also P2's new silhouette), picture symmetric about it; the P1 ship split stays between the formation and the ship with 8 lasers flying |
| RC5 ships | `test_ship_silhouettes`, `test_p2_sprites_and_oam_use`, `test_ship_hitboxes_unchanged` | expected pictures from CHR / `build.P2_PIXELS` and the palettes: P1 and P2 matched pixel by pixel (position and RGB) in 260 frames each while moving, edges included; masks differ (10–60 px), same box (columns 2–14, rows 0–15); P2 = 4 sprites at `$02A0–$02AF` (tiles `$E1`/`$EA`, right half H-flipped, x = P2_X + `$79`, y `$D0`), no other OAM entry uses them, shots only in their 8 OAM slots (all 8 used), 13 stars; an enemy bullet sweeping −12…+12 px hits P1 and P2 from the same 11 offsets |
| RC5 colours | `test_shot_colours`, `test_laser_shape_and_colours`, `test_enemy_colours_unchanged`, `test_palette_only_one_colour_changed` | P1 green `$2A` (not the aliens' `$1A`, not the white enemy bullets), P2 orange `$27`, OAM palette and pixel of every slot on W1–W4, both pilots firing together and alternately, after a death and after a revive (both directions); every W4 laser drawn alone is exactly the 3 × 8 laser in its pilot's colour; enemy sprites in 3000 frames of real play (divers of all colours, flagships, explosions, enemy bullets): every visible pixel has the original colour except palette 2 colour 3 (`$2A`); palette RAM = original except that byte |
| RC5 shield / HUD | `test_shield_blink_silhouettes`, `test_hud_in_overdrive` | during the 4-s blink each ship is in every frame either its exact picture or not drawn (no partial or mixed picture), the partner exact; afterwards both exact, P1's nametable rows as before the death; both pilots in overdrive (started by points): HUD cells, digits on the picture and status row `W4 nns` / `STG 01` / `W4 nns`, also while lasers fly through the HUD rows |
| RC4 HUD | `test_stage_counter` | `STG 01`, `02`, `03` after natural stage changes; a death and life sharing keep it; `STG 99`, then `01` (the game's own wrap); nothing else on row 2; 1P: row 2 blank |

## 2. Measurements (emulator scripts, not part of the suite)

**RC6 (ROM `7e5d4fd1…`)**, scripts in the session scratchpad (`aggr.py`, `window.py`, `stress.py`, `actcpu.py`,
`aimshare.py`), corrected idle counter:

Aggression, 12-s windows at the start of stages 2–5 (8 sessions per mode, same state for all three):

| | normal stage | RC4 profile, same start | RC6 |
|---|---|---|---|
| dive starts / 720 frames (1P = co-op) | 3.25 | 4.0 (+23 %) | 5.75 (+77 %) |
| first attack (frames from the stage's first frame of play) | ~275 | ~220 | 20 (F0: formation drawn) |
| enemy shots / 720 frames | 6.5 | 11.1 | 17.2 |
| dive speed (px/frame) | 1.00 | 1.14 | 1.23 |

Steady state (co-op, P2 in overdrive kept on, 6 × 60 s, same states): dive starts 4.31 → 6.30 (RC4) →
6.85 (RC6) per 1000 frames; speed 1.00 → 1.14 → 1.23; enemy shots heading toward P2 1 % → 52 % → 88 %;
fired 8.7 → 12.3 → 19.1 per 1000 frames. Dive target decisions (tracer, `EE52` calls counted, 20 000
frames): P2 alone in overdrive 75 % at P2, P1 alone 75 % at P1, both 50/50, none 50/50. Tuning variants
measured on the way: slot limit +1 with RC4's flagship-window bypass +87–101 % starts (too strong),
without the slot limit +49 %; dive boost one/two diver slots per frame 14–16 %, three slots with 4-px
cells 33 %.

CPU (12 sessions × 3 min per line; overdrive and aggression kept on, 8 shots, x2, lives kept):

| Scenario | RC6 worst frame | previous ROM, same script | lag | resets |
|---|---|---|---|---|
| co-op, both W4, firing | 100 | 83 | 0 | 0 |
| co-op, both W4 + both shields | 44 | 37 | 0 | 0 |
| 1P W4 | 168 | – | 0 | 0 |
| 1P W4 + shield | 83 | – | 0 | 0 |
| activation frames F0–F7, 40 starts after real play | ≥ 225 (F0) | – | 0 | – |

(cynes sessions start from a random power-on state; RC5's own sessions gave 96 / 73.)

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

**Raster split** – with the shortened wait and `PreSplit`, screen lines 0–120 are pixel-identical to a ROM
variant with the original wait (co-op, co-op with 8 lasers, 1P; 12 frames each); title identical over 600
frames. So the P1 ship split happens at the same place. RC4: `PreSplit` takes 1171 cycles (27 loop
iterations removed, the split 37 cycles later than the original, < 1 scanline); the automatic test
`test_raster_split_below_formation` checks it lands between the formation and the ship.

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

**RC3 in manual emulator testing (by the user)** – PASS: no ghost shots after P1's death, P1/P2 same shot
speeds, one shot per press, death resets the weapon and removes shots, shield ~4 s, W4 lasers and
GREAT SHOT, smooth with both on W4, HUD updates. FAIL: some P2 shots on W2–W4 not starting at the ship;
W2 after stage 1 not always for both; wrong characters in P1's score (photos) – see CHANGELOG RC4.

**RC4 in manual emulator testing (by the user)** – 11/12 PASS: scores and hi score without glitches, all shot
positions, free W2 after stage 1, W2 kept after a death, W3 after 4000 more, stage counter, overdrive
(30 s, countdown, sounds, x2, aggression, back to W3), no slowdown, game over and back to the menu.
FAIL: P1 yellow / P2 orange shots too easy to confuse; remark: the two ships look too much alike.

**RC6: not tested outside the emulators yet** (cynes, FCEUmm in stable-retro, tracer). RC6 checklist:
1. 1 PILOT: after clearing stage 1 → `W2`; die → back on W2, the ship blinks ~4 s and can't be hit; `STG 01`,
   `02` … above the hi score (the flags on the right agree); no P2 anything, SELECT does nothing.
2. Overdrive READY: on W3 score 8000 without dying → `OVERDRIVE READY NEXT STAGE` (co-op `P1 W4 READY NEXT
   STAGE`) for ~2 s, `W4 RDY` above your HUD; still 3 shots, normal points, normal enemies.
3. Clear the stage: in the first moment of the next one `OVERDRIVE!`, the jingle, `W4 12s`, and at once
   three aliens break from the formation toward you – no calm start; attacks stay heavy for 12 s.
4. After 12 s: `W3`, the field blank, normal enemies; lasers in flight finish.
5. Die while READY → no overdrive at the next stage; a revive by SELECT doesn't bring it back.
6. Co-op both READY in one stage: both start together (`P1 P2 OVERDRIVE!`), attacks split between you.
7. The attract demo shoots again (as the original).
8. Smoothness with both on W4 and shields: no stutter, no reset; HUD digits clean.

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

Not tested by the author: **Mesen 2, RetroArch, real NES/Famicom**, sound, playability over
long games, two physical controllers. Please report the emulator/core, version and what worked.

### Mesen 2

1. Build: `python3 games/galaxian-coop/src/build.py` → `build/Galaxian_Coop.nes`.
2. Settings → Input: two controllers (Player 1, Player 2).
3. Title: logo, `CO-OP` badge (red, short white glint), `1 PILOT` / `2 PILOTS CO-OP`,
   `HACK BY ZVGELO ©2026`, Namco lines; SELECT moves the cursor, START starts.
4. Top line of the screen empty in play, no `0` in the top-left corner.
5. **1 PILOT**: one ship with the same rules as a co-op pilot (RC6): `X3` / `W1` / `STG 01`, free W2 after
   stage 1, shield after a respawn; pad 2 does nothing.
6. **2 PILOTS CO-OP**: P1 left, P2 right; both move and fire at the same time; points to the right score;
   deaths of each pilot; `Xn` counts down; P1 out → `P2 SELECT TO REVIVE P1` (or `P1 OUT`) → SELECT on
   pad 2 → P1 back beside P2, P2 −1 life, +200; game over only after both.
7. Boosts: after stage 1 on `W2` (2 shots, both modes); W4: `W4 RDY`, then at the next stage `OVERDRIVE!`
   with the counter-attack and `W4 12s`.
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
