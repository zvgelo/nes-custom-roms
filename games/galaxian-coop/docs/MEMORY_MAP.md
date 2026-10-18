# Galaxian (Japan) / Galaxian Coop – memory map

Confidence: **C** confirmed (code and emulator), **K** from the code only, **H** hypothesis.

CPU addresses. File offset in Galaxian Coop = `0x10 + (address − $8000)`; in the original
`0x10 + (address − $E000)`.

## ROM

| CPU range | Original | Galaxian Coop |
|---|---|---|
| `$8000–$DFFF` | mirrors of the 8 KiB PRG (never referenced by the code, **C**) | new code `$8000–$8BFF`, `PreSplit` page `$9E00–$9EFF`, `ScrollFix` page `$9F00`; rest `$FF` |
| `$E000–$FFFF` | game program | game program + 37 hooks (`.patch` blocks, see REVERSE_ENGINEERING.md) |
| `$FFFA/$FFFC/$FFFE` | NMI `$E20C`, RESET `$E020`, IRQ `$E020` | unchanged |

CHR (8 KiB): table `$0000` = sprites in play / background on the title, `$1000` = background in play,
sprites on the title. Parts of CHR are also data: reset copies PPU `$1480–$17FF` → RAM `$0300–$067F`
and PPU `$098E–$0A3F` → RAM `$014E–$01FF` (**C**).

CHR changes in Galaxian Coop (all checked by `build.py` before writing):

| Tile | Use |
|---|---|
| sprite `$E1`, `$EA` (were blank logo cells) | P2 ship, top / bottom half (drawn twice, the second copy flipped) |
| CHR `$155F`, `$1568` (logo string data) | the two logo cells point to blank tile `$10` instead – identical picture |
| sprite `$60` (never displayed by the original) | W4 red laser: red edges (colour 1), orange core (colour 3), sprite palette 1 |

## RAM – original game

### Zero page

| Address | Meaning | Conf. |
|---|---|---|
| `$00–$04` | start-up music player (`FF0E`) | K |
| `$23–$24` | Famicom microphone detection (`$4016` bit 2) | K |
| `$27`, `$28` | formation counters (limit attack waves) | H |
| `$29` | "after player change" flag (alternating 2P) | K |
| `$2A` | "NMI in progress" flag | C |
| `$2B` | GAME OVER timer of one player (alternating 2P) | K |
| `$2D` | HUD streaming index (0–$15) | K |
| `$30`, `$31` | menu: START/SELECT hold counter, choice (bit 0: 0 = 1 PILOT, 1 = 2 PILOTS) | C |
| `$36–$39` | 26-byte text row to write in the NMI: VRAM address, data pointer | C |
| `$3A–$3B` | main-loop counter (idle CPU time, RNG seed) | C |
| `$3C` | alternating-2P flag (always 0 in Galaxian Coop) | C |
| `$3D` / `$3E` | original one-time extra ship still available P1 / P2 (set to 0: replaced) | K |
| `$40`, `$41` | sound effects: shot, explosion | K |
| `$42` / `$43` | **reserve** ships P1 / P2 | C |
| `$44` | P1 fire counter of the original bullet routine (unused now) | K |
| `$4C` | buttons of the active player (pad 1 in play, AI in the demo) | C |
| `$4E` | pause | C |
| `$4F` | P1 hit: 0 alive, 1..$22 explosion, $22 end of animation | C |
| `$53` | score row selector for E833 (0 P1, 1 P2) | C |
| `$54–$58` | points to add (digits; `$57` hundreds, `$58` tens) | C |
| `$59` / `$5A` | stage number | C |
| `$5B–$67` | attack timers / difficulty | H |
| `$68–$81` | sound | K |
| `$8E–$91` | flagship state | K |
| `$92–$9B` | divers in flight per column | K |
| `$9C` | sequence timer | K |
| `$9D`, `$9E` | current diver slot: OAM offset (slot×16), slot | C |
| `$9F` | formation empty | K |
| `$A0–$BF`, `$C0–$C2` | background explosion queue | K |
| `$C3–$CC` / `$CD–$D6` | formation bitmap (current / other player) | C |
| `$D7–$DF`, `$E0` | temporaries (`$E0` = bullet hit flag) | K |
| `$E1` | VRAM queue entries (max 16) | C |
| `$E2–$E3`, `$E8–$EB` | pointers, dispatcher `$E44B` | C |
| `$E4` | P1 ship X (signed, `$96..$6A`), lower raster split | C |
| `$E5` | formation sway (upper raster split) | C |
| `$EC`, `$ED` | frame counters | K |
| `$EE`/`$EF` | pad 1 previous / current | C |
| `$F0`/`$F1` | pad 2 previous / current | C |
| `$F6`, `$F7`, `$FA`, `$FB` | copies of `$2005`, `$2001`, `$2000` | C |
| `$FD`, `$FE`, `$FF` | state machine: sub-sub-state, sub-state, state | C |

Pad bits: 7 A, 6 B, 5 SELECT, 4 START, 3 Up, 2 Down, 1 Left, 0 Right.
States `$FF`: 0 init, 1 title, 2 demo, 3 game, 4 GAME OVER, 5 end screen. Game sub-states `$FE`
(table `$E901`): 0–1 wipe, 2 start `F9D9`, 3 ship lost / wave end `FA52`, 4 `F883`, 5 wipe,
6 respawn `FA69`, 7 "READY" `FBEB`, 8 normal play `E913`.

### Pages 1–7

| Address | Meaning | Conf. |
|---|---|---|
| `$0101–$0115` | reset flags / signature | K |
| `$0104` | frame counter (bit 0: stars every second frame) | C |
| `$0116–$012F` | scores: P1 `$0117–$011C`, hi `$0120–$0125`, P2 `$0129–$012E` (digits 0–9, `$10` blank) | C |
| `$0130–$014D` | stack (S starts at `$4D`; the NMI resets the game when S < `$30`) | C |
| `$014E–$01FF` | sound data copied from CHR | K |
| `$0200–$027F` | OAM: 8 diver slots × 4 sprites (slot 7 = formation-enemy explosion) | C |
| `$0280–$0283` | OAM: P1 bullet sprite (P1 slot 0) | C |
| `$0284–$029F` | OAM: 7 enemy bullets | C |
| `$0300–$0679` | data copied from CHR: text, logo layout, tables | C |
| `$0690–$06BB` | HUD buffer → VRAM `$2074–$209F` | C |
| `$06BC–$06D5` | 26-character text row buffer | K |
| `$06D8–$07FF` | divers, VRAM queue (`$0748/58/68/78`), movement tables | K |
| `$07E8–$07FF` | 24 entries recomputed every frame by `E471`; **`$07F0` is game data** (Stage 1 bug) | C |

## RAM – Galaxian Coop

All addresses below were found unused by the original: no reference in the full disassembly (indexed
ranges included) **and** unchanged in long emulator runs of title, demo, 1P and 2P games.

### Zero page `$05–$26`

| Address | Name | Meaning |
|---|---|---|
| `$05` | `COOP` | 1 = co-op game |
| `$06` | `P1_OUT` | P1 out of the game, P2 plays on |
| `$07` | `P1_BLOCK` | `$4F` or `P1_OUT`: used instead of `$4F` in P1 input/hit checks |
| `$08` | `P2_STATE` | 0 out, 1 alive, 2 exploding, 3 waiting to respawn |
| `$09` | `P2_X` | P2 ship X (same convention as `$E4`) |
| `$0A` | `P2_TIMER` | explosion / respawn timer |
| `$0B–$0C` | `FIRE_CNT` | fire-button counters P1, P2 |
| `$0D` | `T2` | temporary (`FORM_K` during the bullet pass) |
| `$0E`, `$0F` | `CUR_SLOT`, `CUR_PL` | bullet loop: slot, pilot (PreSplit temporaries too) |
| `$10`, `$11` | `T0`, `T1` | temporaries |
| `$12` | `AIM_TOGGLE` | dives alternate between the pilots |
| `$13` | `P1_GRANTED` | P1 dead, next ship already taken from `$42` |
| `$14` | `TITLE_STEP` | extra title rows written (0–3) |
| `$15` | `P1_REDRAW` | P1 revived: background ship still to draw |
| `$16–$1D` | `BUL_Y` | player bullets Y (P1 slots 0–3, P2 slots 4–7); 0 = free |
| `$1E–$25` | `BUL_X` | player bullets X |
| `$26` | `STAGE1_DONE` | co-op: free W2 for the first stage already given |

### Other zero page and `$06xx`

| Address | Name | Meaning |
|---|---|---|
| `$45–$46` | `WLEVEL` | weapon level P1, P2: 0–3 = W1–W4 |
| `$47–$48` / `$49–$4A` | `NODEATH_LO/HI` | points since the last death, units of 10 |
| `$4B` | `DCOUNT` | divers in `DLIST` this frame |
| `$4D` | `BANNER_CUR` | message shown on HUD rows 1–2 |
| `$52` | `BANNER_ROW` | banner rows still to write |
| `$69` | `W4_TIMER` | frames left for the W4 message |
| `$6A` | `W4_WHO` | bit 0 P1, bit 1 P2 reached W4 |
| `$7A–$7B` / `$7C–$7D` | `BOOST_LO/HI` | boost points P1, P2, units of 10 |
| `$D9` | `DI` | loop index / temporary |
| `$E6–$E7` / `$F8–$F9` | `NEXT_LIFE_LO/HI` | next extra-life threshold in thousands (7, 14, …) |
| `$F3` | `HIT_DONE` | a bullet hit something this frame |
| `$F4` | `SHOT_N` | slot counter / PreSplit step |
| `$FC` | `LOGIC_RAN` | `$FF` when the game logic ran this frame |
| `$0680–$0687` | `BUL_F` | bullets: Y fraction (8.8 speed) |
| `$0688–$068E` | `DLIST` | OAM offsets of the divers that can be hit this frame |
| `$067A–$067B` | `LASTK` | thousands digit at the last extra-life check |
| `$067C` | `LAG_COUNT` | overlapped NMIs in a row |
| `$067D` | `PS_MASK2` | PreSplit: P2 visibility mask |
| `$067E` | `LAG_TOTAL` | overlapped NMIs since power-on (diagnostics) |

`$067A–$067F` belong to the block the reset code copies from CHR (`$0300–$067F`), but the last
string ends at `$0679` and nothing reads these bytes. `build.py` refuses overlapping new variables.
`$07F0` is not used.

## OAM

| Range | Content |
|---|---|
| `$0200–$027F` | diver slots (free slots: Y=0 as in the original, tile now blank `$10`) |
| `$0280` | P1 bullet slot 0 |
| `$0284–$029F` | enemy bullets |
| `$02A0–$02AF` | P2 ship (TL, TR flipped, BL, BR flipped); on the title: `CO-OP` badge (+`$02B0`) |
| `$02B0`, `$02B4`, `$02B8`, `$02C8` | P2 bullet slots 0–3 |
| `$02BC`, `$02C0`, `$02C4` | P1 bullet slots 1–3 |
| `$02CC–$02FF` | 13 stars (original: 24 at `$02A0–$02FF`) |

## Nametables

| Where | Content |
|---|---|
| `$2000` rows 1–2, cols 3–28 | message banner (revive prompt, W4 message) |
| `$2000` row 3/4 | HUD: P1 icon col 1, `W`+level row 3 cols 2–3, `X`+lives row 4 cols 2–3; labels; scores; P2 block cols 28–30 |
| attribute `$23C7` = `$10`, `$23CF` = `$01` | co-op: P2 HUD icon in palette 1 (reset to 0 for 1P) |
| `$2800` rows 16, 18, 28 | title rows `1 PILOT`, `2 PILOTS CO-OP`, `HACK BY ZVGELO ©2026` |
| `$2800` row 29 | must stay blank: its last pixel row is screen line 0 in play (ScrollFix) |
