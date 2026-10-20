# Galaxian (Japan) / Galaxian Coop – memory map

Confidence: **C** confirmed (code and emulator), **K** from the code only, **H** hypothesis.

CPU addresses. File offset in Galaxian Coop = `0x10 + (address − $8000)`; in the original
`0x10 + (address − $E000)`.

## ROM

| CPU range | Original | Galaxian Coop |
|---|---|---|
| `$8000–$DFFF` | mirrors of the 8 KiB PRG (never referenced by the code, **C**) | new code from `$8000`, `PreSplit` tables page `$9D00`, `PreSplit` code page `$9E00`, `ScrollFix` page `$9F00`; rest `$FF` (build.py refuses overlapping blocks) |
| `$E000–$FFFF` | game program | game program + hooks (`.patch` blocks, see REVERSE_ENGINEERING.md) and one palette byte (`$E1CF`) |
| `$FFFA/$FFFC/$FFFE` | NMI `$E20C`, RESET `$E020`, IRQ `$E020` | unchanged |

CHR (8 KiB): table `$0000` = sprites in play, `$1000` = background in play. The title switches: the
logo/menu screen uses background `$0000` and sprites `$1000`, other title phases background `$1000`
(`$FB`, **C**). Parts of CHR are also data: reset copies PPU `$1480–$17FF` → RAM `$0300–$067F` and PPU
`$098E–$0A3F` → RAM `$014E–$01FF` (**C**).

CHR changes in Galaxian Coop (all checked by `build.py` before writing):

| Tile | Use |
|---|---|
| sprite `$E1`, `$EA` (were blank logo cells) | P2 ship, left half top / bottom (drawn twice, the second copy flipped). RC5: P2's own ship (`build.P2_PIXELS`: delta nose, flat-topped pods, split fins); RC1–RC4: a copy of P1's ship |
| CHR `$155F`, `$1568` (logo string data) | the two logo cells point to blank tile `$10` instead – identical picture |
| sprite `$60` (never displayed by the original) | W4 laser: one colour (3), 3 px wide, centre column 4 like the bullet `$30`; P1 palette 2 (green, RC4 yellow), P2 palette 0 (orange). RC1–RC3: red/orange two-tone, centre column 3 (1 px left) |
| background `$1000` tile `$36` (a one-dot tile no nametable uses: traced title, demo, games, game over, end screen) | lower-case `s` of the overdrive countdown (`W4 12s`), colour 1 like the letters |
| background `$1000` tile `$34` (a one-dot tile no nametable of the original uses: traced title, demo, 1P and 2P games) | `!` of `OVERDRIVE!` (RC6), colour 1 |

Palette: the reset code loads all 32 palette bytes once from `$E1B4` (`E16B`). Sprite palettes:
`0F 30 11 27` / `0F 16 11 27` / `0F 23 11 27` / `0F 1A 11 27`; colour 3 is orange `$27` in all four
and every colour is used (P2 ship, enemies, enemy bullets, stars). Galaxian Coop changes one byte,
`$E1CF` (sprite palette 2 colour 3) `$27` → bright green `$2A` (RC4: yellow `$28`): P1's shots use
palette 2, P2's palette 0. Palette 2 colour 3 otherwise only colours 2 pixels of a purple alien while it
dives (one pixel in two of its four tiles `$44–$5F`; in the formation it is background, unchanged).

## RAM – original game

### Zero page

| Address | Meaning | Conf. |
|---|---|---|
| `$00–$04` | start-up music player (`FF0E`) | K |
| `$23–$24` | Famicom microphone easter egg: `$23` = raw `$4016` every frame, `$24` counts bit-2 toggles; 4 toggles with `$0115` = 10 → reset path `E23A` (`E580–E59C`) | C |
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
| `$0115` | reset counter (`E04F`), used by the microphone easter egg | C |
| `$0116–$012F` | **score row**: P1 `$0117–$011C`, hi `$0120–$0125`, P2 `$0129–$012E` (digits 0–9, `$10` blank). The gaps are part of displays: `E307` copies `$0117–$0125` (15 bytes, `$011D/$011E` included) into the HUD buffer → row 4 cols 4–18; `FB70`+`E4AA` write all 26 bytes `$0116–$012F` to the title screen (`$2883`) after GAME OVER. Never put variables here (RC3 did: score glitches) | C |
| `$0130–$014D` | stack (S starts at `$4D`; the NMI resets the game when S < `$30`). Deepest write in traced runs: original `$013A`, RC3/RC4 `$0133` | C |
| `$014E–$0155` | 4 tune pointers (tune address + `$0840`; slot 0 rewritten by `FD8E`) | C |
| `$0156–$01FF` | tunes 3, 2, 1 (85 / 34 / 51 bytes) copied from CHR, played from RAM by the sound driver (`FDD7`) | C |
| `$0200–$027F` | OAM: 8 diver slots × 4 sprites (slot 7 = formation-enemy explosion) | C |
| `$0280–$0283` | OAM: P1 bullet sprite (P1 slot 0) | C |
| `$0284–$029F` | OAM: 7 enemy bullets | C |
| `$0300–$0346` | text pointer table (35 entries, `F941`) | C |
| `$0347–$037F` | `$FF` filler: no pointer leads there, never read (traced) → Galaxian Coop variables | C |
| `$0380–$047D`, `$0580–$0679` | texts and title data read by the game | C |
| `$047E–$057F` | copied CHR pixel data, never read from RAM (traced) | C |
| `$067A–$067F` | `$FF` filler → Galaxian Coop variables | C |
| `$0690–$06BB` | HUD buffer → VRAM `$2074–$209F` | C |
| `$06BC–$06D5` | 26-character text row buffer | K |
| `$06D8–$07FF` | divers, VRAM queue (`$0748/58/68/78`), movement tables | K |
| `$07E8–$07FF` | 24 entries recomputed every frame by `E471`; **`$07F0` is game data** (Stage 1 bug) | C |

## RAM – Galaxian Coop

All addresses below were found unused by the original: no direct reference in the disassembly
(`ORIGINAL_ZP` in build.py) **and** never read or written by original code in traced runs
(`src/original_ram.txt`, made by `tests/ram_audit.py` with `tools/trace6502.py`: 8 runs × 100 000 frames
of title, demo, 1P and 2P games, game over and end screen). build.py refuses any new variable on those
addresses, on the stack page `$0130–$014D` and any overlap between variables. A traced list is evidence,
not proof: paths the runs did not reach (late stages) could use more.

RC4 audit correction: the first tracer of RC4 returned 0 for CHR reads through `$2007`, so the RAM copies
of CHR data looked empty and `$0156–$01FF` looked free (it holds three tunes). Fixed before any release;
`tests/test_trace.py` now checks that the tune RAM and the music output are unchanged.

### Zero page `$05–$26`

| Address | Name | Meaning |
|---|---|---|
| `$05` | `COOP` | 1 = co-op game |
| `$06` | `P1_OUT` | P1 out of the game, P2 plays on |
| `$07` | `P1_BLOCK` | `$4F` or `P1_OUT` or the P1 shield: used instead of `$4F` in the two P1 hit checks (movement, firing and dive aiming test `$4F`/`P1_OUT` only) |
| `$08` | `P2_STATE` | 0 out, 1 alive, 2 exploding, 3 waiting to respawn |
| `$09` | `P2_X` | P2 ship X (same convention as `$E4`) |
| `$0A` | `P2_TIMER` | explosion / respawn timer |
| `$0B–$0C` | `FIRE_CNT` | fire-button counters P1, P2: 2 = released, a press fires on its 2nd frame, 0 = press used up |
| `$0D` | `T2` | temporary (`FORM_K` during the bullet pass) |
| `$0E–$15` | `BUL_X` | player bullets X (RC2 and earlier: `$1E–$25`, overlapping the original's `$23/$24`) |
| `$16–$1D` | `BUL_Y` | player bullets Y (P1 slots 0–3, P2 slots 4–7); 0 = free |
| `$1E`, `$1F` | `CUR_SLOT`, `CUR_PL` | bullet loop: slot, pilot (PreSplit temporaries too) |
| `$20`, `$21` | `T0`, `T1` | temporaries |
| `$22` | `TITLE_STEP` | extra title rows written (0–3) |
| `$23–$24` | – | the original's (microphone check), not used |
| `$25` | `P1_GRANTED` | P1 dead, next ship already taken from `$42` |
| `$26` | `STAGE1_DONE` | free W2 for the first stage already given (RC6: 1P and co-op) |

### Other zero page and `$06xx`

| Address | Name | Meaning |
|---|---|---|
| `$45–$46` | `WLEVEL` | weapon level P1, P2: 0–3 = W1–W4 |
| `$47–$48` / `$49–$4A` | `NODEATH_LO/HI` | points since the last death, units of 10 |
| `$4B` | `DCOUNT` | divers in `DLIST` this frame |
| `$4D` | `BANNER_CUR` | message shown on HUD row 1 |
| `$52` | `BANNER_ROW` | banner rows still to write (2 only at a game start: row 2 blanked too) |
| `$69` | `W4_TIMER` | frames left for the overdrive message (`OD_MSG`) |
| `$6A` | `W4_WHO` | pilots the message names: bit 0 P1, bit 1 P2 |
| `$7A–$7B` / `$7C–$7D` | `BOOST_LO/HI` | boost points P1, P2, units of 10 |
| `$D9` | `DI` | loop index / temporary |
| `$E6–$E7` / `$F8–$F9` | `NEXT_LIFE_LO/HI` | next extra-life threshold in thousands (7, 14, …) |
| `$F3` | `HIT_DONE` | a bullet hit something this frame |
| `$F4` | `SHOT_N` | slot counter / PreSplit step |
| `$F5` | `OD_SND` | overdrive jingle: frames left |
| `$FC` | `LOGIC_RAN` | `$FF` when the game logic ran this frame |
| `$0680–$0687` | `BUL_F` | bullets: Y fraction (8.8 speed) |
| `$0688–$068E` | `DLIST` | OAM offsets of the divers that can be hit this frame |
| `$0350` | `AIM_TOGGLE` | dives alternate between the pilots (RC3: `$011D`) |
| `$0351` | `P1_REDRAW` | P1 revived: background ship still to draw (RC3: `$011E`) |
| `$0352–$0353` | `SHIELD` | respawn shield frames left P1, P2 (240 = 4 s; RC6: 1P too) (RC2/RC3: `$0126`) |
| `$0354` | `SCORE_NEW` | frames in which `E2FE` still copies the scores (RC3: `$0128`) |
| `$0355–$0356` | `W2_OWNED` | pilot unlocked W2 in this game: a death or revive gives W2, not W1 |
| `$0357–$0358` | `W4_USED` | overdrive already used in this life |
| `$0359–$035A` / `$035B–$035C` | `W4_SEC` / `W4_FRM` | overdrive seconds left (RC6: 12..1, RC4–RC5: 30..1; 0 = off) / frames left in the second (60..1) |
| `$035D–$0364` | `BUL_LV` | weapon level each shot was fired with (speed and look for its whole flight) |
| `$0365` / `$0366–$0367` | `STG_SHOWN` / `TMR_SHOWN` | value shown in the HUD status row fields (`$FE` blank, `$FF` unknown) |
| `$0368` | `BY_SHOT` | 1 while a shot's hit is scored (x2 only for shots) |
| `$0369–$0370` | – | free since RC6 (RC4–RC5: `DIVE_CELL` / `DIVE_RR` of the dive boost) |
| `$0371–$0372` | `OD_PEND` | overdrive READY (W3 + 8000 no-death points), starts with the next stage (RC6) |
| `$0373` | `OD_ARM` | a stage was cleared: READY overdrives start in the next normal-play frame (RC6) |
| `$0374` | `OD_MSG` | overdrive message on row 1: 1 READY, 2 started (RC6) |
| `$0375` | `OD_NOW` | an overdrive just started: status row due at once (RC6) |
| `$0376–$0377` | `OD_COLS` | formation columns 0–9 queued for drawing since the stage started (bit per column): the overdrive starts once all are drawn (RC6) |
| `$067A–$067B` | `LASTK` | thousands digit at the last extra-life check |
| `$067C` | `LAG_COUNT` | overlapped NMIs in a row |
| `$067D` | `PS_MASK2` | PreSplit: P2 visibility mask |
| `$067E` | `LAG_TOTAL` | overlapped NMIs since power-on (diagnostics) |

`$0347–$037F` and `$067A–$067F` belong to the block the reset code copies from CHR (`$0300–$067F`):
`$FF` filler after the text pointer table and after the last text. Every reset rewrites them, so the
variables there are set at the start of a game before use (`BUL_LV` is also masked to 0–3 in PreSplit).
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
| `$2000` row 0 | the original's row writer writes its blank row to cols 3–28 every idle frame: unusable |
| `$2000` row 1, cols 3–28 | message line (revive prompt, `… W4 READY NEXT STAGE`, `… OVERDRIVE!`), written by the row writer `E4AA`; RC4–RC5 also `GREAT SHOT` (superseded) |
| `$2000` row 2 | status row (never written by the original in play): P1 overdrive field cols 2–7 (`W4 RDY` or `W4 12s` … `W4 01s`), `STG 01` cols 13–18 (both modes since RC6), P2 overdrive field cols 22–27; VRAM queue, only on change; blanked once at a game start |
| `$2000` row 3/4 | HUD: P1 icon col 1, `W`+level row 3 cols 2–3, `X`+lives row 4 cols 2–3; labels; scores; cols 20–31 from the buffer `$0690–$06BB`: co-op P2 block (`2UP`, score, icon, `Wn`, `Xn`), 1 PILOT the original stage flags only (blanked at every game start, RC6) |
| attribute `$23C7` = `$10`, `$23CF` = `$01` | co-op: P2 HUD icon in palette 1 (reset to 0 for 1P) |
| `$2800` rows 16, 18, 28 | title rows `1 PILOT`, `2 PILOTS CO-OP`, `HACK BY ZVGELO ©2026` |
| `$2800` row 29 | must stay blank: its last pixel row is screen line 0 in play (ScrollFix) |
