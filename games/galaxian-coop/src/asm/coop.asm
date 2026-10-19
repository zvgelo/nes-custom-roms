; Galaxian Coop - simultaneous 2-player co-op for Galaxian (Japan), NES
; Assembled by tools/asm6502.py, applied by src/build.py.
;
; Layout: NROM-256. $8000-$DFFF = new code, $E000-$FFFF = original 8 KiB PRG.
; Every patch over original code uses .patch with the original bytes, which
; build.py verifies before writing.

; ---------------------------------------------------------------- original RAM
PAD1        = $EF       ; controller 1, bit7=A ... bit0=Right
PAD2        = $F1       ; controller 2
SHIP_X      = $E4       ; P1 ship x offset (signed, $96..$6A), BG scroll split
P1_DEAD     = $4F       ; 0 = P1 alive, else explosion / respawn counter
STATE       = $FF       ; top state: 1 title, 2 demo, 3 game, 4 game over
SUBSTATE    = $FE       ; game sub-state, 8 = normal play
OAM         = $0200

; ---------------------------------------------------------------- new RAM
; $05-$22 is never referenced by the original program (static scan) and stayed
; zero in emulator runs; reset clears it (E032).
COOP        = $05       ; 1 = co-op game (title "2 PLAYERS")
P1_OUT      = $06       ; 1 = P1 has no lives left but P2 plays on
P1_BLOCK    = $07       ; P1_DEAD | P1_OUT: replaces $4F in P1 input/hit checks
P2_STATE    = $08       ; 0 out, 1 alive, 2 exploding, 3 waiting to respawn
P2_X        = $09       ; same convention as SHIP_X
P2_TIMER    = $0A
FIRE_CNT    = $0B       ; fire-button counters P1, P2 ($0B-$0C), rule of E5A8
T2          = $0D
BUL_X       = $0E       ; $0E-$15: shots X
CUR_SLOT    = $1E       ; bullet loop: slot index
CUR_PL      = $1F       ; bullet loop: pilot (0 P1, 1 P2)
T0          = $20
T1          = $21
TITLE_STEP  = $22       ; extra title rows already queued (0-3)
; $23-$24 belong to the original (Famicom microphone check in E580-E59C).
P1_GRANTED  = $25       ; P1 dead, next ship already taken from LIVES1 (FA83)
; $0347-$037F: $FF filler in the block the reset code copies from CHR
; ($0300-$067F): after the text pointer table ($0301-$0346), before the
; first text ($0380); no pointer leads there and nothing reads it (traced
; runs, MEMORY_MAP.md). Written by the reset copy: set before use.
; Not $0116-$012F: that is the score row, which E307 copies to the HUD and
; FB70 writes to the title screen (RC3 had variables there: score glitches).
AIM_TOGGLE  = $0350     ; alternates the dive target between the players
P1_REDRAW   = $0351     ; P1 revived by life sharing: ship tiles still to draw
PAD1_PREV   = $EE       ; pads in the previous frame (E54D)
PAD2_PREV   = $F0
SELECT_BIT  = $20

; player bullets: 4 slots per pilot, P1 = slots 0-3, P2 = slots 4-7
BUL_Y       = $16       ; $16-$1D: Y, 0 = free
STAGE1_DONE = $26       ; the free W2 for clearing stage 1 was given (1P and co-op)
; zero page below: never referenced by the original program and left at 0
; in emulator runs of title, demo, 1P and 2P games (see MEMORY_MAP.md)
WLEVEL      = $45       ; $45-$46: weapon level P1, P2: 0-3 = W1-W4
NODEATH_LO  = $47       ; $47-$4A: points since the last death (units of 10)
NODEATH_HI  = $49
DCOUNT      = $4B       ; divers in DLIST
BANNER_CUR  = $4D       ; message shown on HUD rows 1-2 (0 = none)
BANNER_ROW  = $52       ; next banner row to write (0 = up to date)
W4_TIMER    = $69       ; frames left for the overdrive message (OD_MSG)
W4_WHO      = $6A       ; pilots the message is about: bit 0 = P1, bit 1 = P2
BOOST_LO    = $7A       ; $7A-$7D: boost points P1, P2 (units of 10)
BOOST_HI    = $7C
DI          = $D9       ; loop index / temporary
HIT_DONE    = $F3       ; a bullet already hit something this frame
SHOT_N      = $F4       ; slots left in the current pilot's pass
OD_SND      = $F5       ; overdrive jingle: frames left (0 = silent)
LOGIC_RAN   = $FC       ; $FF when E913 ran this frame (bullets move next NMI)
; PreSplit temporaries (it runs before the game logic, whose temporaries
; these are): T0 speed fraction, T1 whole pixels, T2 tile, DI attributes,
; CUR_PL slot counter, CUR_SLOT visibility mask, SHOT_N step, HIT_DONE P2 mask
FORM_K      = $0D       ; T2 during the bullet pass: $E5 + $2E (F381's offset)
NEXT_LIFE_LO = $E6      ; $E6-$E7 / $F8-$F9: next extra-life threshold, thousands
NEXT_LIFE_HI = $F8
; $0680-$068E: unused by the game (static scan and emulator runs)
BUL_F       = $0680     ; $0680-$0687: Y fraction (8.8 speed)
DLIST       = $0688     ; $0688-$068E: OAM offsets of the divers that can be hit
LIFE_STEP   = 7         ; extra life every 7000 points
; $067A-$067F: the end of the block the reset code copies from CHR to RAM
; ($0300-$067F); the last string ends at $0679 and no code reads these.
SHIELD      = $0352     ; $0352-$0353: respawn shield frames left P1, P2
SHIELD_FRAMES = 240     ; 4 s at 60 Hz (3.99 s at NTSC 60.0988 Hz)
SCORE_NEW   = $0354     ; frames E2FE still copies the scores
W2_OWNED    = $0355     ; $0355-$0356: pilot unlocked W2 this game (1): a death
                        ; brings it back on W2, not W1
W4_USED     = $0357     ; $0357-$0358: overdrive already used in this life
W4_SEC      = $0359     ; $0359-$035A: overdrive seconds left (30..1, 0 = off)
W4_FRM      = $035B     ; $035B-$035C: frames left in the current second (60..1)
BUL_LV      = $035D     ; $035D-$0364: weapon level each shot was fired with
STG_SHOWN   = $0365     ; stage number on HUD row 2 (STATUS_BLANK / _UNKNOWN)
TMR_SHOWN   = $0366     ; $0366-$0367: overdrive seconds on HUD row 2 (same)
BY_SHOT     = $0368     ; 1 while a bullet's hit is scored (x2 only for shots)
; $0369-$0370: free (RC4-RC5 dive boost state, DIVE_CELL / DIVE_RR)
OD_PEND     = $0371     ; $0371-$0372: overdrive ready (W3 + 8000 no-death
                        ; points): starts with the next stage (OdStart)
OD_ARM      = $0373     ; a stage was cleared: ready overdrives start in the
                        ; first normal-play frame (FE = 8) after it
OD_MSG      = $0374     ; message on HUD row 1 for W4_TIMER frames: OD_MSG_*
OD_NOW      = $0375     ; an overdrive just started: status row due at once
OD_COLS     = $0376     ; $0376-$0377: formation columns 0-9 redrawn since the
                        ; stage started (bit per column; OdStart waits for all)
LASTK       = $067A     ; $067A-$067B: thousands digit at the last life check
LAG_COUNT   = $067C     ; NMIs that overlapped the previous one, in a row
PS_MASK2    = $067D     ; PreSplit: P2 visibility mask
LAG_TOTAL   = $067E     ; overlapped NMIs since power-on (diagnostics)
MAX_LIVES   = 9         ; one HUD digit; further extra lives are not given

; per-player variables of the original alternating 2P mode, reused for co-op
CUR_PLAYER  = $53       ; selects the score row in E833 (0 P1, 1 P2)
LIVES1      = $42
LIVES2      = $43
BONUS1      = $3D       ; extra ship still available
BONUS2      = $3E
P1_BUL_Y    = $0280
P1_BUL_X    = $0283
EBUL_Y      = $0284     ; 7 enemy bullets, 4 bytes apart
EBUL_X      = $0287
DIVER_STATE = $0738     ; 8 diving-enemy slots, sprites at OAM + slot*16
HIT_FLAG    = $E0       ; set by F381/F2EF/F31E when a bullet hits

; ---------------------------------------------------------------- new OAM use
; Stars used $02A0-$02FF (24 sprites); they now start at $02CC (13 sprites).
P2_OAM      = $02A0     ; 4 sprites: TL, TR, BL, BR
; bullet sprites: P1 $0280 (original slot), $02BC, $02C0, $02C4
;                  P2 $02B0, $02B4, $02B8, $02C8
LASER_TILE  = $60       ; W4 red laser, sprite palette 1 (CHR set by build.py)
BULLET_TILE = $30
EXPL_TILE   = $70       ; enemy explosion frames $70/$74/$78/$7C (2x2 each)
P2_TILE_TOP = $E1       ; sprite table tiles freed from the title logo
P2_TILE_BOT = $EA
P2_ATTR     = $00       ; sprite palette 0: orange nose, blue pods, white core
SHIP_OAM_Y  = $D0       ; BG ship's top row is scanline 209
RESPAWN_DELAY = 120     ; frames between P2's explosion and respawn
P1_SPAWN_X  = $F4       ; co-op start/respawn: P1 12 px left of centre,
P2_SPAWN_X  = $0C       ; P2 12 px right (ships 13 px wide: no overlap)
REVIVE_GAP  = 24        ; a revived pilot appears this far beside the partner

; ================================================================ hooks
; Sprite palette 2 colour 3: orange $27 -> bright green $2A (palette table
; loaded once at reset, E16B). All sprite palettes had colour 3 = $27 and
; every colour slot is used; palette 2 colour 3 only colours 2 pixels of a
; purple alien while it dives (one in each of two of its 4 diver tiles
; $44-$5F). It gives P1's shots their own colour: P1 green, P2 orange
; (RC4: yellow $28, too close to the orange). $2A is lighter than the green
; aliens ($1A) and unlike the white enemy bullets (tile $37, palette 0 colour 1).
.patch $E1CF, "27"
        .byte $2A

; Sound driver frame (FD0E, state 3 only: FCFC returned earlier otherwise):
; the overdrive jingle steps right after the shot sound's own step.
.patch $FD17, "20 D4 FE"            ; JSR $FED4
        jsr SoundTick

; E913 is the gameplay frame (called in play, respawn and demo states).
; First call: P1 bullet vs enemies. CoopPre refreshes P1_BLOCK, runs it, then
; runs the same routine for the P2 bullet.
.patch $E913, "20 B3 F2"            ; JSR $F2B3
        jsr CoopPre
; Last relevant call is the diving-enemy update; P2 runs right after.
.patch $E91F, "20 B1 E9"            ; JSR $E9B1
        jsr CoopMid

; P1 movement: blocked while P1 is hit or out of the game, not by the shield
; (P1_BLOCK also holds the shield). In 1P / demo the same as LDA $4F.
.patch $EEC0, "A5 4F D0 F5 20 D6 EE"    ; LDA $4F / BNE EEB9 / JSR EED6
        jsr P1MoveGate
        nop
        nop
        nop
        nop
; P1's bullet (E627, called first in E5BA) is replaced by the shared
; bullet engine: same firing rule, 1-3 shots, 100/110/120 % speed.
.patch $E5BA, "20 27 E6"            ; JSR $E627
        jsr P1Bullets
; Every score goes through E833 (A = points index, $53 = pilot). ScoreAdd
; runs it, then adds the points to boost progress and checks extra lives.
.patch $E833, "20 8D E8"            ; JSR $E88D
        jmp ScoreAdd
; FC38: the formation is empty, the game advances the stage counter ($59).
; Weapon boosts are decided here, once per cleared stage.
.patch $FC38, "E6 59 38"            ; INC $59 / SEC
        jsr StageCleared
.patch $E5DF, "E6 4F C6 4F"         ; enemy bullet vs P1
        inc P1_BLOCK
        dec P1_BLOCK
.patch $EC59, "E6 4F C6 4F"         ; diving enemy vs P1
        inc P1_BLOCK
        dec P1_BLOCK
; P1_BLOCK = P1 hit, out, or shielded: no enemy bullet or diver hits P1.
; The two "P1 is hit" stores also set P1_BLOCK, so P1 can't be hit twice
; in one frame (as in the original, which re-read $4F).
.patch $E611, "A9 01 85 4F"
        jsr SetP1Dead
        nop
.patch $EC8F, "A9 01 85 4F"
        jsr SetP1Dead
        nop

; FA7D takes P1's next ship from the reserve (DEC $42) at the start of the
; respawn sequence; the lives HUD needs to know that happened.
.patch $FA83, "C6 42 A9 00"         ; DEC $42 / LDA #0
        jsr P1ShipGranted
        nop
; FA52 handles a lost P1 ship; FA5D is reached when P1 has no ships left.
.patch $FA5D, "4C 23 FB"            ; JMP $FB23 (game over)
        jmp P1OutOfLives
; "PLAYER 1/2" banner on respawn was keyed on the menu choice ($31); key it
; on the alternating-mode flag instead so co-op doesn't show it.
.patch $FAA0, "A5 31"
        lda $3C
; P1 ship redraw after a respawn: skipped once P1 is out of the game.
.patch $FC17, "4C FF EF"            ; JMP $EFFF
        jmp P1ShipRedraw

; E2FE copies P1's score and the hi score into the HUD buffer and updates the
; hi score (~350 cycles) in every frame, then streams the buffer into the
; VRAM queue (E342). In a game the scores only change in AfterScore (all
; points, also the life-sharing bonus), at a new game (CoopInit, then FA3E)
; and when P2 sets the hi score (CoopHiScore): copy in the two frames after
; points (not in the kill frame itself, RC4) and the next one after a new
; game or P2 hi score (E2FE copies the hi score before updating it, so a new
; hi score reaches the buffer one frame later); stream every other frame.
.patch $E2E4, "20 FE E2"                ; JSR $E2FE
        jsr HudScores

; NMI arriving while the previous one still runs: the original treats it as
; a crash and resets the game (E22F). Treat it as one lag frame instead:
; set the frame-start scroll, return to the running NMI. After 8 such frames
; in a row the original reset still happens (real hang).
.patch $E21D, "BD 06 01 C9 E0 90 0B"     ; LDA $0106,X / CMP #$E0 / BCC E22F
        jmp NmiGuard
        nop
        nop
        nop
        nop

; CPU: player bullets are moved and drawn in a constant-time routine placed
; in the NMI's busy wait before the ship's raster split (E2AA loop): the
; wait is shortened by exactly as many 42-cycle iterations as PreSplit
; takes, rounded down, so the split never happens earlier (the formation's
; bottom row is only a few lines above it) and at most 41 cycles later.
.patch $E2A5, "20 4D E5"            ; JSR $E54D (read pads)
        jsr PreSplit
.patch $E2A8, "A0 BE"               ; LDY #$BE
        ldy #$BE - PRESPLIT_ITER

; CPU: E65E turns a diving enemy's sprite towards the player every frame
; (division loop E6F9, ~250 cycles per diver). Done every other frame per
; diver (by slot parity) to make room for up to 8 player bullets; flight
; paths and hit boxes are unchanged, only the tilt updates at 30 Hz.
.patch $EB9C, "20 5E E6"            ; JSR $E65E
        jsr OrientHalf

; Overdrive aggression (OdActive: any pilot's overdrive running). Hooks
; into the original attack logic, all inactive without an overdrive.
; F415 (every frame): counters of solo attacks step every 4th frame; also on
; frames where $ED & 7 = 2: 6 steps per 16 frames, +50 % attack attempts
; (RC4: 5 per 16). The extra step skips F49C (the flagship timer), so
; flagship waves keep their period.
.patch $F45F, "A5 ED 29 03 D0 A7"   ; LDA $ED / AND #3 / BNE F40C (RTS)
        jmp AtkGate
        nop
        nop
        nop
; (RC4-RC5 also let solo attacks start during the flagship attack window
; $35 in overdrive; RC6 raises the solo-slot limit instead, SoloLimit, and
; keeps the original window: measured +59 % dive starts instead of +87 %.)
; F10E picks a free solo-diver slot up to F134/F13C[$65] (the attack level
; sets how many solo divers may fly at once); in overdrive one level higher
; (RC6; at most 7, the game's own top: slots 3-6).
.patch $F10E, "A4 59 C0 01 A4 65"   ; LDY $59 / CPY #1 / LDY $65
        jsr SoloLimit
        nop
        nop
        nop
; Enemy bullets aim at $E4 (EE23): in co-op at P2 instead when only P2 is in
; overdrive (7 frames out of 8; both: alternately).
.patch $EE23, "18 A5 E4"            ; CLC / LDA $E4
        jsr BulletAimX

; Dive target (EE4E computes the x a diver heads for from SHIP_X).
.patch $EE4E, "A6 9E A4 9D"         ; LDX $9E / LDY $9D
        jmp AimDiver
        nop

; HUD right part (buffer $0690-$069B / $06B0-$06BB = rows 3-4, cols 20-31):
; the original draws reserve-ship icons there (E897, cols 21-23) and the
; stage flags (E8B2, cols 25-29; from stage 6 one flag and the number, row
; 4 cols 26-27), at a game start (FA41/FA44), a respawn (FB0E/FB11) and a
; stage start (FBF8/FBFB). Lives are shown as "Xn" in both modes, so E897
; does nothing now (RC6; RC1-RC5 overwrote its icons every 4th frame,
; SoloHud). The flags stay in 1 PILOT; in co-op the area is P2's (CoopHud),
; so E8B2 does nothing there (RC1-RC5: flags and stage digits could show for
; a few frames in P2's score at a stage start or a respawn).
.patch $E897, "20 8D E8"            ; JSR $E88D (E897: reserve-ship icons)
        rts
        nop
        nop
.patch $E8B2, "20 8D E8"            ; JSR $E88D (E8B2: stage flags)
        jsr StageFlags

; Demo pilot (F518): it fires when $0280 = $C8, the original bullet resting
; on the ship. $0280 is now P1 slot 0's sprite, which PreSplit hides ($F8)
; before the logic runs, so the demo never fired (RC1-RC5). DemoBullet gives
; the original's view of slot 0.
.patch $F5A5, "AD 80 02"            ; LDA $0280
        jsr DemoBullet
.patch $F5DF, "AD 80 02"            ; LDA $0280
        jsr DemoBullet

; NMI: E2CE calls the game logic dispatcher; P2 is drawn right after it.
.patch $E2CE, "20 73 E3"            ; JSR $E373
        jsr CoopPost

; Game start (F9D9, only when STATE=3): A = selected mode ($31 & 1).
; Original stored it in $3C (alternating 2P flag) and $53 (current player).
; Both are already 0 here; co-op keeps them 0 so P1's pad drives P1.
.patch $FA34, "85 3C 85 53"         ; STA $3C / STA $53
        jsr CoopInit
        nop

; Stars: 19 sprites at $02B4-$02FF instead of 24 at $02A0-$02FF.
.patch $F03F, "A2 5C"
        ldx #$30
.patch $F041, "FE A0 02"
        inc $02CC,x
.patch $F044, "BD A0 02"
        lda $02CC,x
.patch $F04B, "DE A3 02"
        dec $02CF,x
.patch $F051, "9D A0 02"
        sta $02CC,x
.patch $F05B, "BD A3 02"
        lda $02CF,x
.patch $F061, "9D A3 02"
        sta $02CF,x
.patch $FC9B, "A0 5C A2 17"
        ldy #$30
        ldx #$0C
.patch $FCA6, "99 A3 02"
        sta $02CF,y
.patch $FCAB, "99 A1 02"
        sta $02CD,y
.patch $FCB5, "99 A2 02"
        sta $02CE,y
.patch $FCBA, "99 A0 02"
        sta $02CC,y

; F753 clears OAM $0200-$029F to all zeros. Y=0 is how the game marks a
; free slot, so those sprites stay on screen lines 1-8 at X=0, and with
; tile $00 (the digit 0) they showed a "0" in the top-left corner (also in
; the original). Clear with tile $10 (blank) instead; Y/attr/X stay 0.
.patch $F753, "A2 00 8A 9D 00 02 E8 E0 A0 D0 F8 60"
        jmp ClearOam
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop

; Title screen: F5FF builds it in nametable $2800, one 26-byte row per
; frame (F92B/F937 -> E4AA). Its last step F666 ends the sequence; it now
; first queues three extra rows from ROM, one per frame.
.patch $F666, "E6 FE A9"            ; INC $FE / LDA #0 ...
        jmp TitleExtra

; Top line: in play the game scrolls with Y=$FF, so the PPU draws screen
; line 0 from nametable row 31 = the attribute table read as tiles (bytes
; $00 -> bottom row of the "0" digit: 32 white dashes). This is in the
; original ROM too. Like the title screen does, use Y=$EF with base
; nametable $2800 instead: line 0 comes from the blank row 29 of $2800 and
; the PPU switches to $2000 row 0 for line 1, so lines 1-239 are unchanged.
; ScrollFix costs exactly 22 cycles more than the code it replaces; one
; 22-cycle iteration of the delay loop before the first raster split is
; removed, so the mid-frame split timing stays identical.
.patch $E542, "A5 F7 8D 05 20 A5 FB 8D 00 20 60"
        jmp ScrollFix
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
.patch $E286, "A0 EB"
        ldy #$EA

; ================================================================ scroll fix
; Own page, so the branch never crosses a page boundary (fixed cycle count).
; Both paths: 42 cycles including the JMP to here (original tail: 20).
.org $9F00
ScrollFix:
        lda $F7                 ; 3
        cmp #$FF                ; 2
        bne ScrollFixKeep       ; 2 / 3
        lda #$EF                ; 2
        sta $2005               ; 4
        lda $FB                 ; 3
        ora #$02                ; 2  base nametable $2800
        sta $2000               ; 4
        nop                     ; 8 + 3 padding
        nop
        nop
        nop
        bit $00
        rts                     ; 6
ScrollFixKeep:
        sta $2005               ; 4
        lda $FB                 ; 3
        sta $2000               ; 4
        nop                     ; 14 padding
        nop
        nop
        nop
        nop
        nop
        nop
        rts                     ; 6

; ================================================================ PreSplit
; Constant time: every path through a slot is 35 + 84 cycles, so the whole
; routine (without the pad read E54D it calls) takes PRESPLIT_CYCLES. Own
; page: no branch or indexed read here crosses a page boundary.
;   per slot 119; loop steps 4*7 + 3*5 + 3 = 46;
;   per pilot 21 + 4*119 + 46 + 6 = 549;
;   total 6 (extra JSR) + 33 + (11 + 549) + (12 + 549) + 11 = 1171
; Each shot moves with the speed and look of the level it was fired with
; (BUL_LV), in the colour of its pilot (PilotAttr).
PRESPLIT_CYCLES = 1171
PRESPLIT_ITER   = PRESPLIT_CYCLES / 42          ; 27: the split moves 37 cycles later
.org $9E00
PreSplit:
        jsr $E54D               ; read pads (the call this replaces)
        lda STATE               ; 3
        and #7                  ; 2
        tax                     ; 2
        lda PreSplitVis1,x      ; 4  P1 bullets shown in demo and game
        sta CUR_SLOT            ; 3
        lda COOP                ; 3
        and #1                  ; 2
        tay                     ; 2
        lda PreSplitVis2,x      ; 4  P2 bullets only in a co-op game
        and PreSplitCoop,y      ; 4
        sta PS_MASK2            ; 4
        ldy #0                  ; 2
        lda CUR_SLOT            ; 3
        jsr PrePilot            ; 6
        ldy #1                  ; 2
        lda PS_MASK2            ; 4
        jsr PrePilot            ; 6
        lda #0                  ; 2
        sta LOGIC_RAN           ; 3
        rts                     ; 6

; Y = pilot, A = visibility mask ($FF / 0). Bullets move only if the game
; logic ran in the previous frame (speed AND LOGIC_RAN), e.g. not in pause.
PrePilot:
        sta CUR_SLOT            ; 3
        lda PilotAttr,y         ; 4
        sta DI                  ; 3
        lda PreSplitBase,y      ; 4
        tax                     ; 2
        lda #4                  ; 2
        sta CUR_PL              ; 3   -> 21
PrePilotLoop:
        lda BUL_LV,x            ; 4  level the shot was fired with (0-3 even
        and #3                  ; 2  before the first game: no page crossing)
        tay                     ; 2
        lda SpeedFrac,y         ; 4
        and LOGIC_RAN           ; 3
        sta T0                  ; 3
        lda SpeedInt,y          ; 4
        and LOGIC_RAN           ; 3
        sta T1                  ; 3
        lda BulTile,y           ; 4
        sta T2                  ; 3   -> 35
        ldy BulOamLo,x          ; 4
        lda BUL_Y,x             ; 4
        and CUR_SLOT            ; 3
        bne PrePilotFly         ; 2 / 3
        lda #$F8                ; free / hidden: 13 so far
        sta OAM,y               ; 5
        lda BUL_X,x             ; 4
        sta OAM+3,y             ; 5
        lda T2                  ; 3
        sta OAM+1,y             ; 5
        lda DI                  ; 3
        sta OAM+2,y             ; 5
        nop                     ; 36 cycles of padding
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
        jmp PrePilotNext        ; 3   -> 84
PrePilotFly:                    ; 14 so far
        lda BUL_F,x             ; 4
        clc                     ; 2
        adc T0                  ; 3
        sta BUL_F,x             ; 5
        lda T1                  ; 3
        adc #0                  ; 2  + 1 px when the fraction overflows
        sta SHOT_N              ; 3
        lda BUL_Y,x             ; 4
        sec                     ; 2
        sbc SHOT_N              ; 3
        bcc PrePilotGone        ; 2 / 3
        sta BUL_Y,x             ; 4
        sta OAM,y               ; 5
        lda BUL_X,x             ; 4
        sta OAM+3,y             ; 5
        lda T2                  ; 3
        sta OAM+1,y             ; 5
        lda DI                  ; 3
        sta OAM+2,y             ; 5
        jmp PrePilotNext        ; 3   -> 84
PrePilotGone:                   ; left the screen: 48 so far
        lda #0                  ; 2
        sta BUL_Y,x             ; 4
        lda #$F8                ; 2
        sta OAM,y               ; 5
        lda BUL_X,x             ; 4
        sta OAM+3,y             ; 5
        lda T2                  ; 3
        sta OAM+1,y             ; 5
        bit $00                 ; 3
        jmp PrePilotNext        ; 3   -> 84
PrePilotNext:
        inx                     ; 2
        dec CUR_PL              ; 5
        beq PrePilotDone        ; 2 (3 the last time)
        jmp PrePilotLoop        ; 3
PrePilotDone:
        rts                     ; 6
PreSplitCodeEnd:

; PreSplit's tables, in a page of their own (indexed reads never cross a page)
.org $9D00
PreSplitTables:
PreSplitVis1:   .byte 0, 0, $FF, $FF, 0, 0, 0, 0
PreSplitVis2:   .byte 0, 0, 0, $FF, 0, 0, 0, 0
PreSplitCoop:   .byte 0, $FF
PreSplitBase:   .byte 0, 4
; bullet tables (here so PrePilot's indexed reads never cross a page)
; W1-W4: 4.00 / 4.40 / 4.80 / 6.40 px per frame = 100 / 110 / 120 / 160 %
SpeedInt:       .byte 4, 4, 4, 6
SpeedFrac:      .byte $00, $66, $CC, $66
MaxShots:       .byte 1, 2, 3, 4
BulTile:        .byte BULLET_TILE, BULLET_TILE, BULLET_TILE, LASER_TILE
; Shots and lasers only use colour 3: P1 sprite palette 2 (colour 3 made
; green, see $E1CF), P2 palette 0 (colour 3 orange, as the P2 ship's nose).
PilotAttr:      .byte 2, 0
BulOamLo:       .byte $80, $BC, $C0, $C4, $B0, $B4, $B8, $C8
PreSplitEnd:

; ================================================================ new code
.org $8000

; Z=0 when a co-op game is running.
IsCoop:
        lda STATE
        cmp #3
        bne IsCoopNo
        lda COOP
        rts
IsCoopNo:
        lda #0
        rts

CoopInit:
        sta COOP
        lda #0
        sta P1_OUT
        sta P1_BLOCK
        sta P2_X
        sta P2_TIMER
        sta AIM_TOGGLE
        sta P1_GRANTED
        sta P1_REDRAW
        lda #2                  ; scores are reset right after (FA3E)
        sta SCORE_NEW
        jsr HudRightClear
        jsr HudAttrReset
        jsr ResetPilots
        lda #0                  ; the original one-time extra ship is replaced
        sta BONUS1              ; by an extra life every 7000 points
        sta BONUS2
        lda COOP
        beq CoopInitDone
        lda #RESPAWN_DELAY      ; enter play together with P1
        sta P2_TIMER
        lda #3
CoopInitDone:
        sta P2_STATE
        rts

; P1 lost the last ship. In co-op with P2 still in the game, P1 sits out:
; continue the normal "ship lost" path with one fake ship (FA7D takes it).
P1OutOfLives:
        jsr IsCoop
        beq P1GameOver
        lda P2_STATE
        beq P1GameOver
        lda #1
        sta P1_OUT
        sta LIVES1
        jmp $FA60
P1GameOver:
        jmp $FB23

P1ShipRedraw:
        ldx #0                  ; the ship is back (or a stage starts)
        jsr FireRearm
        jsr IsCoop
        beq P1ShipRedrawGo
        lda P1_OUT
        bne P1ShipRedrawSkip
P1ShipRedrawGo:
        jmp $EFFF
P1ShipRedrawSkip:
        rts

; Replaces "DEC $42 / LDA #0" at FA83; FA87 then stores A in SHIP_X:
; 0 (centre) in 1P, P1_SPAWN_X in co-op.
P1ShipGranted:
        dec LIVES1
        lda #1
        sta P1_GRANTED
        jsr IsCoop
        beq P1ShipGrantedSolo
        lda #P1_SPAWN_X
        rts
P1ShipGrantedSolo:
        lda #0
        rts

; Replaces "LDA #1 / STA $4F" where P1 gets hit. Returns A = 1 and keeps
; X and Y: E611 goes on with STA $0284,X (removes the enemy bullet).
SetP1Dead:
        txa
        pha
        tya
        pha
        ldx #0
        jsr PilotDown
        lda #0
        sta P1_GRANTED
        pla
        tay
        pla
        tax
        lda #1
        sta P1_DEAD
        sta P1_BLOCK
        rts

; ---------------------------------------------------------------- E913 start
; The respawn shield works in every game (1P and co-op), not in the demo.
CoopPre:
        lda #$FF
        sta LOGIC_RAN
        jsr OdStart             ; before W4Tick: the start frame is the first
        jsr W4Tick              ; of the overdrive's 720
        lda STATE
        cmp #3
        bne CoopPreDemo
        jsr ShieldTick
        lda COOP
        beq CoopPreBlock        ; 1P: A = 0
        lda P1_OUT
        beq CoopPreBlock
        lda P2_STATE
        bne CoopPreP2In
        lda #0                  ; both out: hand over to the original game
        sta LIVES1              ; over path (E937 -> FA52 -> FB23); $22 is
        lda P1_DEAD             ; past the end of the explosion animation
        bne CoopPreP2In
        lda #$22
        sta P1_DEAD
CoopPreP2In:
        lda P2_X                ; P1 is gone: enemies home in on P2
        sta SHIP_X
        lda #1
CoopPreBlock:
        ora P1_DEAD
        ora SHIELD              ; respawn shield: no hits on P1
        sta P1_BLOCK
        jmp BulletHits
CoopPreDemo:
        lda P1_DEAD
        sta P1_BLOCK
        jmp BulletHits

; Respawn shields count down only while the ship is in play (not while it
; explodes or waits), once per game-logic frame; a pause stops them.
ShieldTick:
        lda SHIELD
        ora SHIELD+1
        beq ShieldTickDone      ; no shield running (most frames)
        ldx #1
ShieldTickLoop:
        lda SHIELD,x
        beq ShieldTickNext
        jsr PilotAlive
        bne ShieldTickNext
        dec SHIELD,x
ShieldTickNext:
        dex
        bpl ShieldTickLoop
ShieldTickDone:
        rts

; Shield blinking: 8 frames shown / 8 hidden, the last second 4 / 4; the
; last phase is a hidden one, so the ship stays visible exactly from the
; frame the shield ends. Never outside normal play.
; A = shield frames left (not 0); Z=0 when hidden now.
ShieldHidden:
        tay
        lda SUBSTATE
        cmp #8
        bne ShieldHiddenNo
        dey                     ; frames left - 1: 0-59 = last second
        tya
        cmp #60
        bcs ShieldHiddenSlow
        and #4
        eor #4
        rts
ShieldHiddenSlow:
        and #8
        eor #8
        rts
ShieldHiddenNo:
        lda #0
        rts

; P1's ship is background below the ship split (E2CB), which happens just
; before CoopPost: turning the background off now hides the ship for the
; rest of this frame; sprites stay on. E280 turns it on again next frame.
; No nametable or OAM change.
P1Blink:
        lda STATE
        cmp #3
        bne P1BlinkDone
        lda P1_DEAD
        ora P1_OUT
        bne P1BlinkDone         ; exploding or out: nothing to blink
        lda SHIELD
        beq P1BlinkDone
        jsr ShieldHidden
        beq P1BlinkDone
        lda #$16                ; $1E (E280) without the background
        sta $2001
P1BlinkDone:
        rts

; EEC0: P1 moves unless hit or out (RTS of EEC0's caller as BNE EEB9 did).
P1MoveGate:
        lda P1_DEAD
        ora P1_OUT
        beq P1MoveGateGo
        pla
        pla
        rts
P1MoveGateGo:
        jmp $EED6

; Scoring for P2: E833 adds to the score row picked by $53.
SwapToP2:
        lda #1
        sta CUR_PLAYER
        rts
SwapToP1:
        lda #0
        sta CUR_PLAYER
        rts

; ---------------------------------------------------------------- bullets
; Shared by both pilots and both modes. A free slot has Y=0. Firing keeps
; the original rule (E5A8): with a shot available, A or B held counts a
; counter down from 3 and fires when it reaches 0, so every press fires once.

; Bullets vs enemies (was F2B3 for P1's single bullet). The original hit
; routines read the bullet from $0280/$0283; each bullet is put there in
; turn, with $53 = its owner so the points go to the right pilot.
BulletHits:
        ldy #0                  ; divers F2EF would test: state not 0/$0B/$0C,
        ldx #0                  ; slots 0..6 (DiverHits walks the list from its
BulletHitsList:                 ; end: slot 6 first, F2D1's order)
        lda DIVER_STATE,x
        beq BulletHitsListNext
        cmp #$0B
        beq BulletHitsListNext
        cmp #$0C
        beq BulletHitsListNext
        txa
        asl a
        asl a
        asl a
        asl a
        sta DLIST,y             ; OAM offset = slot * 16
        iny
BulletHitsListNext:
        inx
        cpx #7
        bne BulletHitsList
        sty DCOUNT
        lda $E5
        clc
        adc #$2E
        sta FORM_K
        lda #0
        sta HIT_DONE
        jsr IsCoop
        bne BulletHitsCoop
        ldx #0
        jsr PilotShots
        jmp BulletHitsEnd
BulletHitsCoop:                 ; one hit per frame at most (a kill costs
        lda $0104               ; ~3500 cycles; the original had one bullet):
        and #1                  ; which pilot goes first alternates per frame
        tax
        jsr PilotShots
        lda $0104
        and #1
        eor #1
        tax
        jsr PilotShots
BulletHitsEnd:
        jmp $F2CA               ; per-frame timer step that F2B3 also did

; Collisions for pilot X's bullets (moved and drawn by PreSplit before the
; logic). Firing is done later in the frame (CoopMid), after the ships moved.
PilotShots:
        stx CUR_PL
        txa
        asl a
        asl a
        sta CUR_SLOT
        lda #4
        sta SHOT_N
PilotShotsLoop:
        lda HIT_DONE            ; one hit per frame
        beq PilotShotsCheck
        rts
PilotShotsCheck:
        ldx CUR_SLOT
        lda BUL_Y,x
        bne PilotShotsY
        jmp PilotShotsNext
PilotShotsY:
        ; formation: F381's own tests (F381-F3B8) without its side effects on
        ; a miss. Its one side effect on a miss, F374 (bullet between two
        ; columns, Y < $A0: formation sway step $07FF = 0), is kept for each
        ; pilot's first slot, where the original single bullet was; other
        ; bullets below the formation (Y >= $6C) skip the test at once.
        cmp #$6C
        bcc PilotShotsForm
        cmp #$A0
        bcs PilotShotsDivers
        txa
        and #3
        bne PilotShotsDivers
PilotShotsForm:
        lda BUL_X,x
        sec
        sbc FORM_K
        cmp #$A0
        bcs PilotShotsDivers
        tay                     ; column offset
        and #$0F
        cmp #$0D
        bcs PilotShotsBetween
        lda BUL_Y,x
        sec
        sbc #$6C
        bcs PilotShotsDivers
        eor #$FF
        adc #1                  ; carry is clear: A = $6C - Y
        cmp #$48
        bcs PilotShotsDivers
        tax
        lda FormRow,x           ; row = ($6C - Y) / 12, as F3A5
        tax
        tya
        lsr a
        lsr a
        lsr a
        lsr a
        tay                     ; column
        lda $F40D,x
        and $C3,y
        beq PilotShotsDivers
        jsr BulletOwnerSlot
        jsr $F381               ; the original hit routine does the rest
        jsr BulletHitDone
        bcs PilotShotsHit
        bcc PilotShotsDivers
PilotShotsBetween:
        lda BUL_Y,x
        cmp #$A0
        bcs PilotShotsDivers
        lda #0
        sta $07FF
PilotShotsDivers:
        lda DCOUNT              ; divers: each bullet every other frame,
        beq PilotShotsNext      ; by slot parity. At <= 13 px between two
        lda CUR_SLOT            ; checks no 13-px diver window is missed.
        eor $0104
        lsr a
        bcs PilotShotsNext
        jsr DiverHits
        bcc PilotShotsNext
PilotShotsHit:
        lda #1
        sta HIT_DONE
        ldx CUR_SLOT            ; bullet used up, sprite hidden at once
        lda #0
        sta BUL_Y,x
        ldy BulOamLo,x
        lda #$F8
        sta OAM,y
PilotShotsNext:
        inc CUR_SLOT
        dec SHOT_N
        beq PilotShotsDone
        jmp PilotShotsLoop
PilotShotsDone:
        rts

; Put bullet CUR_SLOT where the original routines read it ($0280/$0283),
; owner in $53, hit flag cleared.
BulletOwnerSlot:
        ldx CUR_SLOT
        lda BUL_Y,x
        sta P1_BUL_Y
        lda BUL_X,x
        sta P1_BUL_X
        lda #0
        cpx #4
        rol a                   ; carry = slot >= 4: 0 for P1, 1 for P2
        sta CUR_PLAYER
        lda #1                  ; the points of this hit come from a shot
        sta BY_SHOT
        lda #0
        sta HIT_FLAG
        rts

; After a hit routine: C=1 if it hit something; $53 back to 0. $0280/$0283
; held the tested shot (any pilot's) for the original routine; they are also
; P1 slot 0's sprite, so put that back as PreSplit drew it (hidden when the
; slot is free) - else another shot showed there for a frame.
BulletHitDone:
        lda BUL_Y
        bne BulletHitDoneY
        lda #$F8
BulletHitDoneY:
        sta P1_BUL_Y
        lda BUL_X
        sta P1_BUL_X
        lda #0
        sta CUR_PLAYER
        sta BY_SHOT
        lda HIT_FLAG
        cmp #1
        rts

FormRow:        .byte 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5

; F2D1 for bullet CUR_SLOT, against the listed divers only. Same test as
; F2EF: hit when (by+6-ey) < 13 and (bx+2-ex) < 12 (unsigned); then F31E
; destroys and scores the diver (one kill per bullet and frame). C=1: hit.
; A bullet is tested every other frame: at up to 4.8 px per frame (and a
; diver's 1-2 px down) the 13-px window can't be skipped. A W4 laser moves
; 12.8 px in two frames: its window is 4 px taller (17), upwards, as the
; laser sprite is 4 px taller than the bullet; RC2-RC3 used 13 and a laser
; could pass through a diver. One loop per window (immediate compares,
; counting down: 23 cycles per diver that isn't hit).
DiverHits:
        ldx CUR_SLOT
        lda BUL_X,x
        clc
        adc #2
        sta T1
        lda BUL_LV,x
        cmp #3
        lda BUL_Y,x
        bcs DiverHitsLaser
        adc #6                  ; C = 0
        sta T0
        ldx DCOUNT
        beq DiverHitsNone
DiverHitsLoop:
        ldy DLIST-1,x
        lda T0
        sec
        sbc OAM,y
        cmp #$0D
        bcs DiverHitsNext
        jsr DiverHitsX          ; returns only when there was no hit
DiverHitsNext:
        dex
        bne DiverHitsLoop
DiverHitsNone:
        clc
        rts
DiverHitsLaser:
        adc #9                  ; C = 1: + 10
        sta T0
        ldx DCOUNT
        beq DiverHitsNone
DiverHitsLoopL:
        ldy DLIST-1,x
        lda T0
        sec
        sbc OAM,y
        cmp #$11
        bcs DiverHitsNextL
        jsr DiverHitsX
DiverHitsNextL:
        dex
        bne DiverHitsLoopL
        clc
        rts

; The diver at OAM offset Y passed the y test: x test, then the kill, which
; returns from DiverHits itself (C from BulletHitDone). Keeps X on a miss.
DiverHitsX:
        lda T1
        sec
        sbc OAM+3,y
        cmp #$0C
        bcs DiverHitsXNo
        stx DI
        tya
        lsr a
        lsr a
        lsr a
        lsr a
        tax                     ; slot
        lda DIVER_STATE,x       ; may have been hit by an earlier bullet
        beq DiverHitsXSkip
        cmp #$0B
        beq DiverHitsXSkip
        cmp #$0C
        beq DiverHitsXSkip
        pla                     ; leave DiverHits from here
        pla
        stx $9E
        sty $9D
        jsr BulletOwnerSlot
        ldx $9E
        jsr $F31E
        jmp BulletHitDone
DiverHitsXSkip:
        ldx DI
DiverHitsXNo:
        rts

P1Bullets:                      ; E627 replacement: P1's bullets are done in
        rts                     ; PilotShots (start of E913) for every mode

; A = P1 slot 0 as the original bullet: $C8 ready on the ship, else its Y.
DemoBullet:
        lda BUL_Y
        bne DemoBulletDone
        lda #$C8
DemoBulletDone:
        rts

; Fire a new bullet for pilot X if a slot among the allowed ones is free.
; One shot per new press of A/B. FIRE_CNT: 2 after a release; a press fires
; on its 2nd frame (E5A8's timing); 0 = press used up, so holding the button
; never fires again. The counter is updated every frame, whatever the slots:
; a press while all shots are flying (or while the pilot can't fire) is used
; up as well. (E5A8 let the counter wrap: a held button fired every 256
; frames, and it skipped the counter while no shot was free.)
FireShot:
        jsr FireInput
        bne FireShotHeld
        lda #2                  ; released: next press may fire
        sta FIRE_CNT,x
        rts
FireShotHeld:
        lda FIRE_CNT,x
        beq FireShotDone        ; this press was used up
        dec FIRE_CNT,x
        bne FireShotDone
        jsr CanFire
        bne FireShotDone
        ldy WLEVEL,x
        lda MaxShots,y
        sta T1
        txa
        asl a
        asl a
        tay                     ; first slot
FireShotFind:
        lda BUL_Y,y
        beq FireShotFree
        iny
        dec T1
        bne FireShotFind
        rts                     ; all shots flying
FireShotFree:
        sty CUR_SLOT
        jsr ShipBulletX
        ldy CUR_SLOT
        sta BUL_X,y
        lda #$C8                ; on the ship; PreSplit moves it before it is
        sta BUL_Y,y             ; first drawn (the original showed it at $C4)
        lda #0
        sta BUL_F,y
        lda WLEVEL,x            ; the shot keeps this level's speed and look
        sta BUL_LV,y            ; for its whole flight (W4 may end meanwhile)
        cmp #3
        beq FireShotLaser
        jmp $FEA8               ; shot sound
FireShotLaser:
        jmp SfxZap              ; overdrive laser sound
FireShotDone:
        rts

; Z=1 when pilot X may fire (in play).
CanFire:
        cpx #0
        bne CanFireP2
        lda P1_DEAD             ; not P1_BLOCK: a shielded P1 fires
        ora P1_OUT
        rts
CanFireP2:
        lda P2_STATE
        cmp #1
        rts

; A = fire buttons of pilot X (P1: $4C, also used by the demo; P2: pad 2)
FireInput:
        cpx #0
        bne FireInputP2
        lda $4C
        and #$C0
        rts
FireInputP2:
        lda PAD2
        and #$C0
        rts

; A = bullet X on pilot X's ship (as E64A: ship x + $7C)
ShipBulletX:
        cpx #0
        bne ShipBulletXP2
        lda SHIP_X
        clc
        adc #$7C
        rts
ShipBulletXP2:
        lda P2_X
        clc
        adc #$7C
        rts

; Sprites: flying bullets; one "ready" bullet on the ship of a pilot in play
; with a shot available (the original showed its bullet there); rest hidden.
; W4 bullets use the red laser tile.
BulletsDraw:
        lda STATE
        cmp #2
        beq BulletsDrawP1       ; demo: P1 only
        cmp #3
        bne BulletsDrawDone
BulletsDrawP1:
        ldx #0
        jsr DrawPilotBullets
        jsr IsCoop
        beq BulletsDrawDone
        ldx #1
        jmp DrawPilotBullets
BulletsDrawDone:
        rts

; The bullet resting on the ship (first free slot among the allowed ones)
; for a pilot in play; flying bullets were drawn by PilotShots.
DrawPilotBullets:
        jsr CanFire
        bne DrawReadyDone
        ldy WLEVEL,x
        lda MaxShots,y
        sta T1
        lda BulTile,y
        sta T2
        txa
        asl a
        asl a
        tay
DrawReadyFind:
        lda BUL_Y,y
        beq DrawReadyFree
        iny
        dec T1
        bne DrawReadyFind
DrawReadyDone:
        rts
DrawReadyFree:
        lda BulOamLo,y
        tay
        jsr ShipBulletX
        sta OAM+3,y
        lda #$C8
        sta OAM,y
        lda T2
        sta OAM+1,y
        lda PilotAttr,x
        sta OAM+2,y
        rts

; ---------------------------------------------------------------- progress
; New game: free bullets, weapon level 0, no boost points, next extra life
; at 7000, fire counters at 3.
ResetPilots:
        ldx #7
        lda #0
        sta STAGE1_DONE
        sta BANNER_ROW
        lda #BANNER_UNKNOWN     ; rows 1-2 rewritten (blank) at game start
        sta BANNER_CUR
        lda #0
        sta W4_TIMER
        sta W4_WHO
        sta OD_SND
        sta BY_SHOT
        sta OD_ARM
        sta OD_MSG
        sta OD_NOW
        lda #STATUS_UNKNOWN     ; status row: drawn again (after the banner
        sta STG_SHOWN           ; blanked it)
        sta TMR_SHOWN
        sta TMR_SHOWN+1
        lda #0
ResetPilotsBullets:
        sta BUL_Y,x
        sta BUL_LV,x
        dex
        bpl ResetPilotsBullets
        ldx #1
ResetPilotsLoop:
        lda #0                  ; W2 not unlocked yet
        sta W2_OWNED,x
        jsr ResetBoost
        lda #LIFE_STEP
        sta NEXT_LIFE_LO,x
        lda #0
        sta NEXT_LIFE_HI,x
        lda #0                  ; fire: a release first
        sta FIRE_CNT,x
        sta SHIELD,x            ; no shield at the start of a game
        lda #$10                ; score starts blank ("    00")
        sta LASTK,x
        dex
        bpl ResetPilotsLoop
        rts

; Pilot X back to its base weapon (death, revive, new game): W2 once it
; unlocked W2 in this game, else W1. Boost (W3 progress) and no-death points
; to 0, overdrive off (also one only ready: cancelled, not given back by a
; revive) and usable again in the new life.
ResetBoost:
        lda W2_OWNED,x
        sta WLEVEL,x
        lda #0
        sta BOOST_LO,x
        sta BOOST_HI,x
        sta NODEATH_LO,x
        sta NODEATH_HI,x
        sta W4_USED,x
        sta W4_SEC,x
        sta OD_PEND,x
        rts

; Pilot X's ship is back: a fire button held now (held through the respawn
; or the READY sequence, where FireShot does not run) must be released first.
FireRearm:
        jsr FireInput
        beq FireRearmDone
        lda #0
        sta FIRE_CNT,x
FireRearmDone:
        rts

; Pilot X lost a ship, or comes back by a revive: base weapon (ResetBoost),
; its flying shots removed (PreSplit hides free slots), and a 4 s shield in
; a game, 1P or co-op (not in the demo). Uses A, Y. (FireShot keeps watching
; the button while the pilot is away; FireRearm when the ship is back.)
PilotDown:
        jsr ResetBoost
        lda STATE               ; 4 s shield once the ship is back
        cmp #3                  ; (ShieldTick waits until then)
        bne PilotDownDemo
        lda #SHIELD_FRAMES
        bne PilotDownShield
PilotDownDemo:
        lda #0
PilotDownShield:
        sta SHIELD,x
        txa                     ; its 4 shots: freed, and their sprites hidden
        pha                     ; now (PreSplit drew them earlier this frame)
        asl a
        asl a
        tax
        jsr PilotDownShot
        jsr PilotDownShot
        jsr PilotDownShot
        jsr PilotDownShot
        pla
        tax
        rts
PilotDownShot:
        lda #0
        sta BUL_Y,x
        ldy BulOamLo,x
        lda #$F8
        sta OAM,y
        inx
        rts

; E833 replacement entry. Outside a game E88D returned from E833's caller.
ScoreAdd:
        pha
        lda STATE
        cmp #3
        beq ScoreAddGo
        pla
        rts
ScoreAddGo:
        pla
        tax                     ; E836-E83F: points -> $57 hundreds, $58 tens
        lda $E80F,x
        sta $57
        lda $E821,x
        sta $58
        jsr ScoreDouble         ; overdrive: x2 for the shooter's kills
        jsr $E841               ; add $54-$58 to row $53 (once)
        jsr AfterScore
        lda #0                  ; $54-$56 are 0 for every other add
        sta $56
        rts

; Pilot $53 in overdrive (W4) and the points come from one of its shots
; (BY_SHOT; not a collision, not the life-sharing bonus): double $56-$58.
; Points are at most 800, so x2 needs the thousands digit $56 (0 or 1).
ScoreDouble:
        lda BY_SHOT
        beq ScoreDoubleDone
        ldx CUR_PLAYER
        lda WLEVEL,x
        cmp #3
        bne ScoreDoubleDone
        lda $58                 ; tens x2, carry into the hundreds
        asl a
        cmp #10
        bcc ScoreDoubleTens     ; C = 0
        sbc #10                 ; C = 1
ScoreDoubleTens:
        sta $58
        lda $57                 ; hundreds x2 + carry
        rol a
        cmp #10
        bcc ScoreDoubleHund     ; C = 0
        sbc #10                 ; C = 1
ScoreDoubleHund:
        sta $57
        lda #0
        rol a
        sta $56                 ; thousands
ScoreDoubleDone:
        rts

; Shared tail of every score (enemies, life-sharing bonus): $56 = thousands
; (only after x2, else 0), $57 = hundreds, $58 = tens of the points just
; added to pilot $53.
AfterScore:
        lda #3                  ; HudScores: copy the scores in the next two
        sta SCORE_NEW           ; frames (E2FE shows a new hi score late)
        ldx CUR_PLAYER
        lda $57
        asl a
        sta T0
        asl a
        asl a
        clc
        adc T0
        clc
        adc $58                 ; points / 10 (at most 99 + 100 = 199)
        ldy $56
        beq AfterScoreUnits
        clc
        adc #100
AfterScoreUnits:
        sta T0
        clc
        adc BOOST_LO,x
        sta BOOST_LO,x
        bcc AfterScoreNoDeath
        inc BOOST_HI,x
        bne AfterScoreNoDeath
        dec BOOST_HI,x          ; saturate at $FFxx
AfterScoreNoDeath:
        lda T0
        clc
        adc NODEATH_LO,x
        sta NODEATH_LO,x
        bcc AfterScoreW4
        inc NODEATH_HI,x
        bne AfterScoreW4
        dec NODEATH_HI,x
AfterScoreW4:
        jsr CheckW4
; Extra life for every 7000 points: compare the score's thousands with the
; next threshold; several thresholds in one score are all given. Skipped
; while the thousands digit is unchanged (a score adds at most 1600, which
; always changes it).
ExtraLifeCheck:
        ldy #0
        cpx #0
        beq ExtraLifeGate
        ldy #$12                ; P2 row $0129 = $0117 + $12
ExtraLifeGate:
        lda $0119,y
        cmp LASTK,x
        bne ExtraLifeNew
        rts
ExtraLifeNew:
        sta LASTK,x
ExtraLifeRow:
        lda $0117,y             ; hundred-thousands ($10 = blank)
        and #$0F
        tay
        lda Mul100Lo,y
        sta T1
        lda Mul100Hi,y
        sta T2
        ldy #0
        cpx #0
        beq ExtraLifeRow2
        ldy #$12
ExtraLifeRow2:
        lda $0118,y             ; ten-thousands
        and #$0F
        sta T0
        asl a
        asl a
        adc T0
        asl a                   ; x10
        clc
        adc T1
        sta T1
        bcc ExtraLifeThousands
        inc T2
ExtraLifeThousands:
        lda $0119,y             ; thousands
        and #$0F
        clc
        adc T1
        sta T1
        bcc ExtraLifeCompare
        inc T2
ExtraLifeCompare:
        lda T1
        cmp NEXT_LIFE_LO,x
        lda T2
        sbc NEXT_LIFE_HI,x
        bcc ExtraLifeDone
        lda NEXT_LIFE_LO,x
        clc
        adc #LIFE_STEP
        sta NEXT_LIFE_LO,x
        bcc ExtraLifeAward
        inc NEXT_LIFE_HI,x
ExtraLifeAward:
        jsr AwardLife
        jmp ExtraLifeCompare
ExtraLifeDone:
        rts

Mul100Lo:       .byte <0, <100, <200, <300, <400, <500, <600, <700, <800, <900
Mul100Hi:       .byte >0, >100, >200, >300, >400, >500, >600, >700, >800, >900

; +1 life for pilot X, if in the game and below MAX_LIVES (X preserved).
AwardLife:
        cpx #0
        bne AwardLifeP2
        lda P1_OUT
        bne AwardLifeDone
        jsr P1TotalLives
        cmp #MAX_LIVES
        bcs AwardLifeDone
        inc LIVES1
        bne AwardLifeSound
AwardLifeP2:
        lda P2_STATE
        beq AwardLifeDone
        jsr P2TotalLives
        cmp #MAX_LIVES
        bcs AwardLifeDone
        inc LIVES2
AwardLifeSound:
        lda #1                  ; extra-ship jingle (as E888)
        sta $6D
AwardLifeDone:
        rts

; Stage cleared (replaces INC $59 / SEC at FC38): at most one weapon level
; per pilot and stage. W1->W2 needs 2000 boost points, W2->W3 4000 more
; (counted from 0 when W2 was given: no surplus is carried over); the
; points then restart. W2 once given stays the base level after a death. In
; every game (1P and co-op; not the demo) the first cleared stage gives W2 to
; every pilot still in the game, once per game. W4 is checked right away
; (CheckW4). Point boosts only for a pilot alive and in play now. The free W2
; also goes to a pilot who was hit but has a ship coming (exploding or
; waiting, with a reserve ship): it starts that ship with W2. A pilot out, or
; hit on its last ship, gets none, and no free W2 later either. Both pilots
; are handled before the one-time flag is set (in 1P P2 is out: none).
StageCleared:
        inc $59
        jsr CoopSpawnPositions
        ldx #1
StageClearedLoop:
        lda STATE
        cmp #3
        bne StageClearedAlive
        lda STAGE1_DONE
        bne StageClearedAlive
        lda WLEVEL,x            ; free W2 for a W1 pilot; W2-W4 pilots go
        bne StageClearedAlive   ; through the normal points check
        jsr PilotComing
        beq StageClearedGrant
        bne StageClearedNext
StageClearedAlive:
        jsr PilotAlive
        bne StageClearedNext
        lda WLEVEL,x
        cmp #2
        bcs StageClearedNext    ; W3 -> W4 is by no-death points only
        tay
        lda BOOST_HI,x
        cmp BoostNeedHi,y
        bcc StageClearedNext
        bne StageClearedGrant
        lda BOOST_LO,x
        cmp BoostNeedLo,y
        bcc StageClearedNext
StageClearedGrant:
        inc WLEVEL,x
        lda #1                  ; W2 (or more) reached: W2 is kept from now on
        sta W2_OWNED,x
        lda #0
        sta BOOST_LO,x
        sta BOOST_HI,x
        jsr CheckW4
StageClearedNext:
        dex
        bpl StageClearedLoop
        lda STATE
        cmp #3
        bne StageClearedDone
        lda #1
        sta STAGE1_DONE
        sta OD_ARM              ; ready overdrives start with the next stage
        lda #0                  ; (once its formation is on screen)
        sta OD_COLS
        sta OD_COLS+1
StageClearedDone:
        sec
        rts

; Co-op: both ships back to their start positions for the next stage.
CoopSpawnPositions:
        jsr IsCoop
        beq CoopSpawnDone
        lda P1_OUT
        ora P1_DEAD
        bne CoopSpawnP2
        lda #P1_SPAWN_X
        sta SHIP_X
CoopSpawnP2:
        lda P2_STATE
        cmp #1
        bne CoopSpawnDone
        lda #P2_SPAWN_X
        sta P2_X
CoopSpawnDone:
        rts

; Z=1 when pilot X is in the game (not eliminated).
; Z=1 when pilot X is in play and not hit.
PilotAlive:
        cpx #0
        bne PilotAliveP2
        lda P1_OUT
        ora P1_DEAD
        rts
PilotAliveP2:
        lda P2_STATE
        cmp #1
        rts

; Z=1 when pilot X is in play, or hit with a reserve ship coming (exploding
; or waiting). Z=0 when out or hit on its last ship.
PilotComing:
        jsr PilotAlive
        beq PilotComingDone
        cpx #0
        bne PilotComingP2
        lda P1_OUT
        bne PilotComingDone
        lda LIVES1
        jmp PilotComingLives
PilotComingP2:
        lda P2_STATE
        beq PilotComingOut
        lda LIVES2
PilotComingLives:
        beq PilotComingOut
        lda #0
PilotComingDone:
        rts
PilotComingOut:
        lda #1
        rts

; RC6 overdrive states per pilot: READY -> ACTIVE -> EXPIRED / CANCELLED.
; READY (OD_PEND): on W3, 8000 points scored without dying, overdrive not
; used in this life (W4_USED). The pilot stays on W3 (no x2, no aggression,
; no countdown); "OVERDRIVE READY NEXT STAGE" on row 1, "W4 RDY" on row 2.
; ACTIVE: from the first normal-play frame of the next stage (OdStart): W4,
; 12 s, x2, aggression, jingle, "OVERDRIVE!" and the counter-attack.
; EXPIRED: W4Tick, after 720 normal-play frames: W3. CANCELLED: a death or a
; revive (ResetBoost) clears READY and ends ACTIVE; a new game clears all.
; X = pilot, kept.
CheckW4:
        lda WLEVEL,x
        cmp #2
        bne CheckW4Done
        lda W4_USED,x
        ora OD_PEND,x
        bne CheckW4Done
        lda NODEATH_HI,x
        cmp #>800
        bcc CheckW4Done
        bne CheckW4Grant
        lda NODEATH_LO,x
        cmp #<800
        bcc CheckW4Done
CheckW4Grant:
        lda #1
        sta OD_PEND,x
        lda #OD_MSG_READY
        jmp OdBanner
CheckW4Done:
        rts
W4Bit:          .byte 1, 2
W4_FRAMES = 120
W4_SECONDS = 12                 ; 12 x 60 = 720 logic frames (11.98 s NTSC)
OD_MSG_READY = 1
OD_MSG_GO    = 2

; Row-1 message A (OD_MSG_*) about pilot X for W4_FRAMES frames; pilots
; with the same message are named together. Keeps X.
OdBanner:
        cmp OD_MSG
        beq OdBannerAdd
        sta OD_MSG
        lda #0
        sta W4_WHO
OdBannerAdd:
        lda W4Bit,x
        ora W4_WHO
        sta W4_WHO
        lda #W4_FRAMES
        sta W4_TIMER
        rts

; The first frame of the next stage (after a cleared stage, OD_ARM) with the
; enemies on screen: at a stage start the nametable has no formation yet;
; the game redraws one formation column per frame from the queue $A0-$BF
; (EF7E, bits $C3), and EEE5 queues column $C2 = 9..0 in turn (then 12 idle
; frames). So in normal play (FE = 8) the columns queued are collected in
; OD_COLS; with all 10 seen and the queue empty ($C1 = $C0) every column has
; been drawn: ~10-23 frames after the stage's first playable frame. In that
; frame every pilot with an overdrive READY and in play gets it: W4, 12 s
; (W4Tick counts this frame as the first), x2 and the aggression (all keyed
; on W4_SEC, so they start together), the jingle, "OVERDRIVE!" (row 1,
; written in the next NMI with this frame's sprites) and the countdown
; (status row at the next chance, OD_NOW), then the counter-attack. Runs
; once per cleared stage (a stage-number wrap can't repeat it).
OdStart:
        lda OD_ARM
        beq OdStartDone
        lda SUBSTATE
        cmp #8
        bne OdStartDone
        lda STATE
        cmp #3
        bne OdStartDone
        ldx $C2                 ; column queued in the last animation step
        cpx #10
        bcs OdStartReady
        lda OD_COLS
        ora ColBitLo,x
        sta OD_COLS
        lda OD_COLS+1
        ora ColBitHi,x
        sta OD_COLS+1
OdStartReady:
        lda OD_COLS
        cmp #$FF
        bne OdStartDone
        lda OD_COLS+1
        cmp #$03
        bne OdStartDone
        lda $C1                 ; queue drained: the last column is drawn
        cmp $C0
        bne OdStartDone
        lda #0
        sta OD_ARM
        sta T2                  ; pilots started now
        ldx #1
OdStartLoop:
        lda OD_PEND,x
        beq OdStartNext
        lda #0
        sta OD_PEND,x
        jsr PilotAlive
        bne OdStartNext
        lda #3
        sta WLEVEL,x
        lda #1
        sta W4_USED,x
        sta T2
        sta OD_NOW
        lda #W4_SECONDS
        sta W4_SEC,x
        lda #60
        sta W4_FRM,x
        lda #OD_MSG_GO
        jsr OdBanner
OdStartNext:
        dex
        bpl OdStartLoop
        lda T2
        beq OdStartDone
        jsr SfxOverdrive
        jmp OdAttack
OdStartDone:
        rts
ColBitLo:       .byte $01, $02, $04, $08, $10, $20, $40, $80, $00, $00
ColBitHi:       .byte $00, $00, $00, $00, $00, $00, $00, $00, $01, $02

; Counter-attack at the start of an overdrive: three solo dives launched
; now by the game's own routines, as F415 launches them, without waiting
; for its attack counters: F151 (outermost alien from the left), F173 (from
; the right), F151 again. Each takes a free solo slot (F10E: slots 3 up to
; F134/F13C[$65]) and returns at once when none is free or no alien is
; left; the dive is the normal one (launch arc, then the dive aimed by
; EE4E). At a stage start the attack level $65 allows only 1-2 solo slots;
; for these launches it is 3 (slots 3-5: 3 divers from stage 2 on, 2 on a
; stage 1 after the wrap; the game uses up to 4 solo slots at level 7),
; then put back. Not while P1 is hit (F415's own rule). AIM_TOGGLE = 0:
; AimDiver gives the next three dive targets to the overdrive pilot (both
; in overdrive: alternately).
OdAttack:
        lda #0
        sta AIM_TOGGLE
        lda P1_DEAD
        bne OdAttackDone
        lda $65
        pha
        lda #3
        sta $65
        jsr $F151
        jsr $F173
        jsr $F151
        pla
        sta $65
OdAttackDone:
        rts

; Overdrive countdown, once per game-logic frame of normal play only (FE=8):
; a pause (no E913), the READY / respawn / stage-change sequences and a
; pilot who is not in play (a death ends W4: ResetBoost) don't use it up.
; Seconds and frames-in-second instead of one 16-bit frame count: the HUD
; shows the seconds without a division.
W4Tick:
        lda SUBSTATE
        cmp #8
        bne W4TickDone
        ldx #1
W4TickLoop:
        lda W4_SEC,x
        beq W4TickNext
        dec W4_FRM,x
        bne W4TickNext
        lda #60
        sta W4_FRM,x
        dec W4_SEC,x
        bne W4TickNext
        lda #2                  ; time up: W3 again (shots already flying keep
        sta WLEVEL,x            ; the level they were fired with: BUL_LV)
W4TickNext:
        dex
        bpl W4TickLoop
W4TickDone:
        rts

BoostNeedLo:    .byte <200, <400        ; 2000 / 4000 points
BoostNeedHi:    .byte >200, >400

; ---------------------------------------------------------------- after E9B1
; Firing happens here, after both ships moved (P1: EEC0, P2: P2Move), so a
; new shot starts from the ship position that is drawn with it (it was one
; frame behind, 1-2 px off a moving ship, in RC1-RC3).
CoopMid:
        jsr $E9B1
        jsr DiveBoost
        lda STATE
        cmp #3
        beq CoopMidFire
        lda #0                  ; demo: the original single shot (W1), whatever
        sta WLEVEL              ; level the last game left
CoopMidFire:
        ldx #0
        jsr FireShot            ; P1 (also 1P and the demo)
        jsr IsCoop
        beq CoopMidDone
        jsr LifeShare
        jsr P2Update
        ldx #1
        jmp FireShot            ; P2
CoopMidDone:
        rts

P2Update:
        lda P2_STATE
        cmp #1
        beq P2Alive
        cmp #2
        beq P2Exploding
        cmp #3
        beq P2Waiting
P2Bullets:                      ; bullets are moved in PreSplit
        rts

; Respawn after RESPAWN_DELAY frames, only during normal play (not while
; the original P1 respawn / wave sequence runs). LIVES2 counts reserve
; ships exactly like LIVES1: the ship entering play is taken from it.
P2Waiting:
        lda P2_TIMER
        cmp #RESPAWN_DELAY
        bcs P2WaitingReady
        inc P2_TIMER
        jmp P2Bullets
P2WaitingReady:
        lda SUBSTATE
        cmp #8
        bne P2WaitingDone
        dec LIVES2
        lda #P2_SPAWN_X
        sta P2_X
        lda #0
        sta P2_TIMER
        ldx #1
        jsr FireRearm
        lda #1
        sta P2_STATE
P2WaitingDone:
        jmp P2Bullets

P2Alive:
        jsr P2Move
        lda SHIELD+1
        bne P2AliveDone         ; respawn shield: no hits on P2
        lda $0104               ; enemy bullets on even frames, divers on odd:
        lsr a                   ; bullets move 2 px/frame (smallest window 5),
        bcs P2AliveDivers       ; divers 1-3 px/frame (boxes >= 17 px)
        jmp P2VsBullets
P2AliveDivers:
        jmp P2VsDivers
P2AliveDone:
        rts

P2Exploding:
        inc P2_TIMER
        lda P2_TIMER
        cmp #32
        bcc P2ExplodingDone
        lda #0
        sta P2_TIMER
        lda LIVES2
        beq P2ExplodingOut
        lda #3                  ; wait, then respawn
        bne P2ExplodingSet
P2ExplodingOut:
        lda #0                  ; no ships left: P2 is out
P2ExplodingSet:
        sta P2_STATE
P2ExplodingDone:
        jmp P2Bullets

P2Kill:
        ldx #1
        jsr PilotDown
        lda #2
        sta P2_STATE
        lda #0
        sta P2_TIMER
        jmp $FE64               ; explosion sound

; Enemy bullets vs P2: same boxes as E5DF..E61D, centred on P2_X.
P2VsBullets:
        ldx #$18
P2VsBulletsLoop:
        lda EBUL_Y,x
        beq P2VsBulletsNext
        sec
        sbc #$CA
        cmp #$05
        bcc P2VsBulletsTip
        cmp #$11
        bcs P2VsBulletsNext
        lda P2_X
        clc
        adc #$77
        sta T0
        lda #$0B
        bne P2VsBulletsBox
P2VsBulletsTip:
        lda P2_X
        clc
        adc #$7A
        sta T0
        lda #$05
P2VsBulletsBox:
        sta T1
        lda EBUL_X,x
        sec
        sbc T0
        cmp T1
        bcs P2VsBulletsNext
        lda #0
        sta EBUL_Y,x
        jmp P2Kill
P2VsBulletsNext:
        dex
        dex
        dex
        dex
        bpl P2VsBulletsLoop
        rts

; Diving enemies (states 2 and 7, as in EB9C) vs P2: same boxes as EC37..EC93.
; The enemy is destroyed and its points go to P2, like a P1 collision.
P2VsDivers:
        lda DCOUNT              ; no diver in flight (list from BulletHits)
        beq P2VsDiversDone
        ldx #7
P2VsDiversLoop:
        lda DIVER_STATE,x
        cmp #2
        beq P2VsDiversCheck
        cmp #7
        bne P2VsDiversNext
P2VsDiversCheck:
        txa
        asl a
        asl a
        asl a
        asl a
        tay
        lda OAM,y
        sec
        sbc #$40
        cmp #$58
        bcc P2VsDiversNext
        sbc #$87                ; carry is set: A = Y - $C7
        cmp #$05
        bcc P2VsDiversTip
        cmp #$13
        bcs P2VsDiversNext
        lda P2_X
        clc
        adc #$6D
        sta T0
        lda #$17
        bne P2VsDiversBox
P2VsDiversTip:
        lda P2_X
        clc
        adc #$70
        sta T0
        lda #$11
P2VsDiversBox:
        sta T1
        lda OAM+3,y
        sec
        sbc T0
        cmp T1
        bcs P2VsDiversNext
        stx $9E
        sty $9D
        jsr SwapToP2
        ldx $9E
        jsr $F31E               ; destroy the diver and score it
        jsr SwapToP1
        jmp P2Kill
P2VsDiversNext:
        dex
        bpl P2VsDiversLoop
P2VsDiversDone:
        rts

; ---------------------------------------------------------------- OAM clear
ClearOam:
        ldx #0
ClearOamLoop:
        lda #0
        sta OAM,x
        sta OAM+2,x
        sta OAM+3,x
        lda #$10
        sta OAM+1,x
        inx
        inx
        inx
        inx
        cpx #$A0
        bne ClearOamLoop
        rts

; ---------------------------------------------------------------- title
; Rows go through the game's own row writer: $36/$37 = VRAM address of
; column 3, $38/$39 = 26 tile bytes (E4AA writes them in the next NMI).
; Row 29 of $2800 must stay blank: ScrollFix shows its last pixel line.
TitleExtra:
        ldx TITLE_STEP
        cpx #3
        bcs TitleExtraDone
        inc TITLE_STEP
        lda TitleAddrLo,x
        sta $36
        lda TitleAddrHi,x
        sta $37
        lda TitleDataLo,x
        sta $38
        lda TitleDataHi,x
        sta $39
        rts
TitleExtraDone:                 ; original F666: next sub-state, FD = 0
        lda #0
        sta TITLE_STEP
        inc SUBSTATE
        sta $FD
        rts

TitleAddrLo:
        .byte <($2800 + 16 * 32 + 3), <($2800 + 18 * 32 + 3), <($2800 + 28 * 32 + 3)
TitleAddrHi:
        .byte >($2800 + 16 * 32 + 3), >($2800 + 18 * 32 + 3), >($2800 + 28 * 32 + 3)
TitleDataLo:
        .byte <TitleRow16, <TitleRow18, <TitleRow28
TitleDataHi:
        .byte >TitleRow16, >TitleRow18, >TitleRow28
; Tiles: digits $00-$09, A-Z $11-$2A, space $10, "-" $2B, (c) $2D, red "1"/"2" $0A/$0B.
TitleRow16:     ; "1 PILOT" row 16, from col 12
        .byte $10, $10, $10, $10, $10, $10, $10, $10, $10, $0A, $10, $20, $19
        .byte $1C, $1F, $24, $10, $10, $10, $10, $10, $10, $10, $10, $10, $10
TitleRow18:     ; "2 PILOTS CO-OP" row 18, from col 12
        .byte $10, $10, $10, $10, $10, $10, $10, $10, $10, $0B, $10, $20, $19
        .byte $1C, $1F, $24, $23, $10, $13, $1F, $2B, $1F, $20, $10, $10, $10
TitleRow28:     ; "HACK BY ZVGELO ©2026" row 28, from col 6
        .byte $10, $10, $10, $18, $11, $13, $1B, $10, $12, $29, $10, $2A, $26
        .byte $17, $15, $1C, $1F, $10, $2D, $02, $00, $02, $06, $10, $10, $10

; ---------------------------------------------------------------- life sharing
; SELECT (new press only: pressed now, released in the previous frame) gives
; one ship to a partner who is out of the game. Only in normal play (FE=8;
; E913 doesn't run while paused). The donor must be in play and have at
; least one reserve ship, i.e. 2+ lives; the receiver re-enters at once
; (the original game has no post-respawn protection). Scores don't change.
LifeShare:
        lda SUBSTATE
        cmp #8
        bne LifeShareDone
        lda PAD1_PREV
        eor #$FF
        and PAD1
        and #SELECT_BIT
        beq LifeShareP2
        jsr GiveFromP1
LifeShareP2:
        lda PAD2_PREV
        eor #$FF
        and PAD2
        and #SELECT_BIT
        beq LifeShareDone
        jmp GiveFromP2
LifeShareDone:
        rts

GiveFromP1:
        lda P1_OUT
        ora P1_DEAD
        bne LifeShareDone       ; P1 not in play
        lda LIVES1
        beq LifeShareDone       ; last ship
        lda P2_STATE
        bne LifeShareDone       ; P2 still in the game
        dec LIVES1
        lda #0
        sta P2_X
        sta P2_TIMER
        lda #1
        sta P2_STATE            ; LIVES2 stays 0: this ship is the one in play
        lda SHIP_X              ; beside P1: right, or left near the edge
        eor #$80
        cmp #$80 + $6A - REVIVE_GAP + 1
        bcs ReviveP2Left
        lda SHIP_X
        clc
        adc #REVIVE_GAP
        bne ReviveP2Set
ReviveP2Left:
        lda SHIP_X
        sec
        sbc #REVIVE_GAP
ReviveP2Set:
        sta P2_X
        ldx #1
        jsr PilotDown
        jsr FireRearm
        lda #0                  ; donor P1
        beq LifeShareBonus

GiveFromP2:
        lda P2_STATE
        cmp #1
        bne LifeShareDone       ; P2 not in play
        lda LIVES2
        beq LifeShareDone       ; last ship
        lda P1_OUT
        beq LifeShareDone       ; P1 still in the game
        lda P1_DEAD
        bne LifeShareDone       ; game over hand-over already started
        dec LIVES2
        lda #0
        sta P1_OUT              ; LIVES1 stays 0: this ship is the one in play
        lda P2_X                ; beside P2: left, or right near the edge
        eor #$80
        cmp #$80 - $6A + REVIVE_GAP
        bcc ReviveP1Right
        lda P2_X
        sec
        sbc #REVIVE_GAP
        jmp ReviveP1Set
ReviveP1Right:
        lda P2_X
        clc
        adc #REVIVE_GAP
ReviveP1Set:
        sta SHIP_X
        lda #BULLET_TILE        ; bullet tile, as FC7C sets it on a respawn
        sta P1_BUL_Y+1
        lda #1
        sta P1_REDRAW
        ldx #0
        jsr PilotDown
        jsr FireRearm
        lda #1                  ; donor P2
; +200 points for the donor through the normal score path (E841 adds $54-$58
; to the row of pilot $53; AfterScore: boost points, extra lives).
LifeShareBonus:
        sta CUR_PLAYER
        lda #2
        sta $57
        lda #0
        sta $58
        jsr $E841
        jsr AfterScore
        lda #0
        sta CUR_PLAYER
        lda #1                  ; extra-ship jingle (as E888)
        sta $6D
        rts

; Draw P1's background ship (same call as FBEB/FC05 on a respawn) once the
; VRAM queue has room for its two entries.
P1RedrawShip:
        lda P1_REDRAW
        beq P1RedrawShipDone
        lda VQ_COUNT
        cmp #15
        bcs P1RedrawShipDone
        lda #0
        sta P1_REDRAW
        lda #$23
        sta $DB
        lda #$6F
        sta $DA
        lda #$63
        sta $DD
        sta $DF
        jmp $EFFF
P1RedrawShipDone:
        rts

OrientHalf:
        lda $9E                 ; diver slot
        eor $0104
        lsr a
        bcc OrientHalfGo
        rts
OrientHalfGo:
        jmp $E65E

; ---------------------------------------------------------------- sound
; The original driver uses pulse 1 for tunes and the diving siren (rewritten
; every frame), pulse 2 and noise for the shot, explosions and the formation
; hum; the triangle is never used. Overdrive sounds:
; - activation: a rising B-flat arpeggio on the triangle (A#4 D5 F5 A#5 D6
;   F6 A#6, 4 frames each, the last one longer, ~0.6 s). Nothing else uses
;   the triangle, so it can't cut music or effects, nor be cut;
; - each W4 shot: a short laser zap on pulse 2 instead of FEA8's shot
;   (duty 50 %, fast decay, fast downward sweep: ~1.4 kHz falling, ~14
;   frames). Hardware envelope and sweep end it, nothing to update per frame;
;   a new shot restarts it (two pilots in one frame: the same values twice).
SfxOverdrive:
        lda STATE               ; the driver only runs in a game (state 3)
        cmp #3
        bne SfxOverdriveDone
        lda #28
        sta OD_SND
SfxOverdriveDone:
        rts

SfxZap:
        lda STATE
        cmp #3
        bne SfxZapDone
        lda #$82                ; duty 50 %, envelope decay, rate 2
        sta $4004
        lda #$92                ; sweep on, period 1, downward, shift 2
        sta $4005
        lda #$50                ; timer $050: ~1.4 kHz
        sta $4006
        lda #$08                ; length index 1, high timer bits 0; restarts
        sta $4007               ; the envelope (written last)
SfxZapDone:
        rts

SoundTick:
        jsr $FED4               ; the call this replaces (shot sound step)
        lda OD_SND
        beq SoundTickDone
        and #3                  ; a new note every 4 frames
        bne SoundTickNext
        lda OD_SND
        lsr a
        lsr a                   ; 7..1
        tax
        lda OdLinear-1,x
        sta $4008
        lda OdPeriod-1,x
        sta $400A
        lda #$08
        sta $400B
SoundTickNext:
        dec OD_SND
SoundTickDone:
        rts
; last note first (OD_SND counts down): A#6 F6 D6 A#5 F5 D5 A#4
OdPeriod:       .byte $1D, $27, $2F, $3B, $4F, $5E, $77
OdLinear:       .byte $20, $10, $10, $10, $10, $10, $10

; ---------------------------------------------------------------- HUD scores
HudScores:
        lda STATE
        cmp #3
        bne HudScoresFull       ; other states: as the original
        lda SCORE_NEW
        beq HudScoresStream
        dec SCORE_NEW
        cmp #3                  ; 3: the frame the points were scored in (a
        bcs HudScoresStream     ; kill: busy): copy in the next two frames
HudScoresFull:
        jmp $E2FE
HudScoresStream:                ; E2FE's tail: stream the HUD buffer on every
        lda $0104               ; 4th frame in a game (RC4, CPU): the one
        and #3                  ; whose logic had $0104 = 3 mod 4 (E2D7 has
        bne HudScoresDone       ; counted it up since): no stars, no HUD
        jmp $E342               ; update; all 22 cell pairs in 8 frames
HudScoresDone:
        rts

; ---------------------------------------------------------------- NMI guard
NmiGuard:                       ; X = stack pointer after the 3 pushes
        lda $2A
        bne NmiLag              ; previous NMI still running
        lda $0106,x             ; the original test: the interrupted code must
        cmp #$E0                ; be the main loop ($E000+), else reset path
        bcc NmiReset
        jmp $E224               ; the original checks go on
NmiLag:
        inc LAG_TOTAL
        inc LAG_COUNT
        lda LAG_COUNT
        cmp #8
        bcs NmiReset            ; stuck: the original watchdog reset
        bit $2002               ; frame-start scroll, as E53A-E549 + ScrollFix
        lda $F6
        sta $2005
        lda $F7
        cmp #$FF
        bne NmiLagKeep
        lda #$EF
        sta $2005
        lda $FB
        ora #$02
        bne NmiLagCtrl
NmiLagKeep:
        sta $2005
        lda $FB
NmiLagCtrl:
        sta $2000
        pla
        tay
        pla
        tax
        pla
        rti
NmiReset:
        jmp $E22F

; ---------------------------------------------------------------- EE4E
; With both ships alive, consecutive dives alternate between P1 and P2;
; while only one of them is in overdrive, 3 dives out of 4 go for that one.
AimDiver:
        jsr IsCoop
        beq AimP1
        lda P2_STATE
        cmp #1
        bne AimP1
        lda P1_DEAD             ; a shielded P1 is still a target
        ora P1_OUT
        bne AimP2
        inc AIM_TOGGLE
        jsr OdTarget
        beq AimAlternate
        tax                     ; 1 = P1, 2 = P2 in overdrive
        lda AIM_TOGGLE
        and #3
        beq AimOther
        cpx #1
        beq AimP1
        bne AimP2
AimOther:
        cpx #1
        beq AimP2
        bne AimP1
AimAlternate:
        lda AIM_TOGGLE
        and #1
        beq AimP1
AimP2:
        lda SHIP_X
        pha
        lda P2_X
        sta SHIP_X
        ldx $9E
        ldy $9D
        jsr $EE52
        pla
        sta SHIP_X
        jmp AimShots
AimP1:
        ldx $9E
        ldy $9D
        jsr $EE52
; EE52 gave the diver its shots for this aim ($06E8: 2 on stage 1, else 3);
; in overdrive one more (RC6). At most 7 enemy shots at once stays the
; game's limit (E5BA's slots). Keeps X ($9E) and Y ($9D) as EE52 left them.
AimShots:
        jsr OdActive
        beq AimShotsDone
        inc $06E8,x
AimShotsDone:
        rts

; ---------------------------------------------------------------- aggression
; Z=0 while any pilot's overdrive runs (W4_SEC is 0 outside overdrive, after
; a death and in a new game: no flag to clear). Uses A only.
OdActive:
        lda W4_SEC
        ora W4_SEC+1
        rts

; A = pilot in overdrive alone: 1 P1, 2 P2; 0 none or both. Uses A only.
OdTarget:
        lda W4_SEC+1
        beq OdTargetP1
        lda W4_SEC
        bne OdTargetNone
        lda #2
        rts
OdTargetP1:
        lda W4_SEC
        beq OdTargetDone
        lda #1
        rts
OdTargetNone:
        lda #0
OdTargetDone:
        rts

AtkGate:                        ; F45F
        lda $ED
        and #3
        bne AtkGateExtra
        jmp $F465               ; the normal step: flagship timer and counters
AtkGateExtra:
        jsr OdActive
        beq AtkGateDone
        lda $ED
        and #7
        cmp #2
        bne AtkGateDone
        jmp $F468               ; the extra steps: counters only
AtkGateDone:
        rts                     ; as F40C: returns from F415

; Y = attack level for the solo-slot limit, C = stage 2 or later ($59 >= 1),
; as F10E-F113 left them; A is free (F114 on reloads it).
SoloLimit:
        ldy $65
        jsr OdActive
        beq SoloLimitStage
        cpy #7
        bcs SoloLimitStage
        iny
SoloLimitStage:
        lda $59
        cmp #1
        rts

; Dives (states 2/7, EB9C: y + 1 per frame) ~23 % faster in overdrive
; (RC4: ~14 %): every diving slot, after the divers moved, + 1 more when its
; y mod 16 is 3, 8 or 13 (16 px in 13 frames). Never from y = 15 mod 16
; (the next value is a fire row, tested after EB9C's step) and at most 1
; extra px per diver and frame: the ship hit bands (5 and 14 px, P2 5 px)
; can't be skipped; x, the launch arc and the return to the formation
; (exact frame counts) are unchanged. Nothing to do without an overdrive.
DiveBoost:
        jsr OdActive
        beq DiveBoostDone
        ldx #6
DiveBoostLoop:
        lda DIVER_STATE,x
        cmp #2
        beq DiveBoostDiver
        cmp #7
        bne DiveBoostNext
DiveBoostDiver:
        ldy DiverOamY,x
        lda OAM,y
        and #$0F
        tay
        lda DiveBoostRow,y
        beq DiveBoostNext
        ldy DiverOamY,x
        lda OAM,y
        clc
        adc #1
        sta OAM,y
DiveBoostNext:
        dex
        bpl DiveBoostLoop
DiveBoostDone:
        rts
DiveBoostRow:   .byte 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0
DiverOamY:      .byte $00, $10, $20, $30, $40, $50, $60

; Co-op: P2 alone in overdrive: 7 shots of 8 aimed at P2 (RC4: 3 of 4);
; both in overdrive: every other frame P1 / P2; else at P1 (the original).
BulletAimX:                     ; EE23: A = x to aim at, C = 0; keeps X, Y
        jsr IsCoop
        beq BulletAimP1
        lda P2_STATE
        cmp #1
        bne BulletAimP1
        jsr OdActive
        beq BulletAimP1
        jsr OdTarget
        cmp #1
        beq BulletAimP1
        cmp #2
        beq BulletAimP2Alone
        lda $ED                 ; both: alternate
        and #1
        beq BulletAimP1
        bne BulletAimP2
BulletAimP2Alone:
        lda $ED
        and #7
        beq BulletAimP1
BulletAimP2:
        lda P2_X
        clc
        rts
BulletAimP1:
        lda SHIP_X
        clc
        rts

; ---------------------------------------------------------------- NMI tail
CoopPost:
        jsr P1Blink             ; first: right after the ship split
        lda #0                  ; this NMI finished in time
        sta LAG_COUNT
        jsr $E373
        jsr P2Draw
        lda HIT_DONE            ; a hit this frame (the costly kind of frame):
        bne CoopPostNoReady     ; the ready bullets stay as drawn last frame
        jsr BulletsDraw
CoopPostNoReady:
        jsr TitleBadge
        jsr BannerUpdate
        lda OD_NOW              ; an overdrive just started: its countdown now
        bne CoopPostStatus
        lda $0104               ; status row on frames 2 mod 4 (no HUD work)
        and #3
        cmp #2
        bne CoopPostStatusDone
CoopPostStatus:
        jsr StatusRow
CoopPostStatusDone:
        lda STATE
        cmp #3
        bne CoopPostDone
        lda $0104               ; spread over frames: stars (F038) run on
        and #3                  ; even frames; HUD and P2's hi score on
        cmp #1                  ; frames 1 mod 4, the status row on 2, the
        bne CoopPostDone        ; HUD stream on 3 (HudScores). The HUD data
        jsr HudP1Lives          ; changes rarely.
        lda COOP
        beq CoopPostDone        ; 1P: rows 3-4 cols 20-31 hold the original flags
        jsr P1RedrawShip
        jsr CoopHud
        jmp CoopHiScore
CoopPostDone:
        rts

; ---------------------------------------------------------------- banner
; Messages on HUD row 1 (cols 3-28), written through the game's 26-byte
; row writer (E4AA), only while it is idle (pointer back on the blank row
; $E1F2 for $2003) so game messages are never overwritten, and only when the
; wanted message changes. Row 2 is the status row (StatusRow); the banner
; blanks it only at the start of a game (BANNER_CUR unknown), so that what
; an earlier game left there goes away.
BANNER_UNKNOWN = $FF
BannerUpdate:
        lda STATE
        cmp #3
        beq BannerUpdateGo
        cmp #4                  ; game over screen: clear
        bne BannerUpdateDone
BannerUpdateGo:
        jsr BannerWanted
        cmp BANNER_CUR
        beq BannerUpdateWrite
        ldx BANNER_CUR
        sta BANNER_CUR
        lda #1                  ; row 1
        cpx #BANNER_UNKNOWN
        bne BannerUpdateRows
        lda #2                  ; row 2 (blank), then row 1
BannerUpdateRows:
        sta BANNER_ROW
BannerUpdateWrite:
        lda BANNER_ROW
        beq BannerUpdateDone
        lda $38                 ; row writer idle?
        cmp #$F2
        bne BannerUpdateDone
        lda $39
        cmp #$E1
        bne BannerUpdateDone
        lda #$20
        sta $37
        lda BANNER_ROW
        cmp #2
        bne BannerUpdateRow1
        lda #$43                ; row 2, col 3: blank (the original's blank row)
        sta $36
        lda #<BLANK_ROW
        sta $38
        lda #>BLANK_ROW
        sta $39
        lda #STATUS_UNKNOWN     ; status row: everything to be drawn again
        sta STG_SHOWN
        sta TMR_SHOWN
        sta TMR_SHOWN+1
        dec BANNER_ROW
        rts
BannerUpdateRow1:
        ldy BANNER_CUR
        lda #$23                ; row 1, col 3
        sta $36
        lda BannerRow1Lo,y
        sta $38
        lda BannerRow1Hi,y
        sta $39
        dec BANNER_ROW
BannerUpdateDone:
        rts

; ---------------------------------------------------------------- status row
; HUD row 2 (lines 17-24, never written by the original in play):
;   cols 2-7   "W4 12s" P1's overdrive seconds left (above P1's "W4"), or
;              "W4 RDY" while P1's overdrive waits for the next stage
;   cols 13-18 "STG 01" stage number, 1P and co-op (1P also keeps the
;              original stage flags of E8B2 in rows 3-4, cols 25-29)
;   cols 22-27 the same for P2, above P2's "2UP" (cols
;              28-29 of rows 2-3 have palette 1 for P2's ship icon: blue digits)
; Each field is queued (VRAM queue, 3 entries of 2 cells) only when the value
; it shows changes, and only while the row writer is idle and the banner
; has nothing pending (the banner blanks the row at the start of a game).
STATUS_UNKNOWN = $FF            ; field state unknown: draw it
STATUS_BLANK   = $FE            ; field blank
STATUS_READY   = $FD            ; "W4 RDY"
StatusRow:
        lda BANNER_ROW
        bne StatusRowDone
        lda $38                 ; row writer idle?
        cmp #$F2
        bne StatusRowDone
        lda $39
        cmp #$E1
        bne StatusRowDone
        lda #0                  ; the row is being brought up to date
        sta OD_NOW
        jsr StageWanted
        cmp STG_SHOWN
        beq StatusRowTimers
        ldx VQ_COUNT
        cpx #14
        bcs StatusRowDone
        sta STG_SHOWN
        ldy #<($2040 + 13)
        jsr StatusField
StatusRowTimers:
        ldx #0
        jsr StatusTimer
        ldx #1
StatusTimer:                    ; X = pilot
        lda #STATUS_BLANK
        ldy STATE
        cpy #3
        bne StatusTimerSet
        ldy W4_SEC,x            ; non-zero only while overdrive runs
        beq StatusTimerReady
        tya
        ora #$80                ; seconds + $80: "W4 nnS"
        bne StatusTimerSet
StatusTimerReady:
        ldy OD_PEND,x
        beq StatusTimerSet
        lda #STATUS_READY
StatusTimerSet:
        cmp TMR_SHOWN,x
        beq StatusRowDone
        ldy VQ_COUNT
        cpy #14
        bcs StatusRowDone
        sta TMR_SHOWN,x
        ldy StatusTimerCol,x
        jmp StatusField
StatusRowDone:
        rts
StatusTimerCol: .byte <($2040 + 2), <($2040 + 22)

; A = stage number to show (1-99, the game's $59 + 1; $59 goes back to 0
; after stage 99, FC3B) or STATUS_BLANK.
StageWanted:
        lda STATE
        cmp #3
        bne StageWantedBlank
        lda $59
        clc
        adc #1
        rts
StageWantedBlank:
        lda #STATUS_BLANK
        rts

; Queue the 6 cells of a field at $20xx (Y = low address of its first cell):
; A = STATUS_BLANK: blanks; A < $80: "STG nn"; A >= $80: "W4 nnS", nn = A & $7F.
StatusField:
        sty T2
        cmp #STATUS_BLANK
        beq StatusFieldBlank
        cmp #STATUS_READY
        beq StatusFieldReady
        tax
        and #$7F
        ldy #$FF                ; tens / units (0-99)
        sec
StatusFieldTens:
        iny
        sbc #10
        bcs StatusFieldTens
        adc #10
        sta DI                  ; units
        txa
        bmi StatusFieldTimer
        lda #$23                ; "ST" "G " tens units
        sta T0
        lda #$24
        sta T1
        jsr StatusPair
        lda #$17
        sta T0
        lda #$10
        bne StatusFieldDigits
StatusFieldTimer:               ; "W4" " " tens units "S"
        lda #W_TILE
        sta T0
        lda #$0C                ; red "4", as the HUD's W4
        sta T1
        jsr StatusPair
        lda #$10
        sta T0
        sty T1
        jsr StatusPair
        lda DI
        sta T0
        lda #SECONDS_TILE
        sta T1
        jmp StatusPair
StatusFieldReady:               ; "W4" " R" "DY"
        lda #W_TILE
        sta T0
        lda #$0C
        sta T1
        jsr StatusPair
        lda #$10
        sta T0
        lda #$22
        sta T1
        jsr StatusPair
        lda #$14
        sta T0
        lda #$29
        sta T1
        jmp StatusPair
StatusFieldDigits:
        sta T1
        jsr StatusPair
        sty T0
        lda DI
        sta T1
        jmp StatusPair
StatusFieldBlank:
        lda #$10
        sta T0
        sta T1
        jsr StatusPair
        jsr StatusPair
; One VRAM queue entry: cells T0, T1 at $20(T2); T2 += 2. Keeps Y.
StatusPair:
        ldx VQ_COUNT
        lda T2
        sta VQ_ADDR_LO,x
        lda #$20
        sta VQ_ADDR_HI,x
        lda T0
        sta VQ_LO1,x
        lda T1
        sta VQ_LO2,x
        inc VQ_COUNT
        inc T2
        inc T2
        rts

; A = wanted message: the overdrive message (timed: READY 5-8, started
; 9-12; P1, P2, both, 1P) first, then the revive prompt (1-4).
BannerWanted:
        lda W4_TIMER
        beq BannerWantedCoop
        dec W4_TIMER
        jsr IsCoop
        beq BannerWantedSolo
        lda W4_WHO
        and #3                  ; 1 P1, 2 P2, 3 both -> 5, 6, 7
        clc
        adc #4
        bne BannerWantedKind
BannerWantedSolo:
        lda #8
BannerWantedKind:
        ldy OD_MSG
        cpy #OD_MSG_GO
        bne BannerWantedDone
        clc
        adc #4
BannerWantedDone:
        rts
BannerWantedCoop:
        sta W4_WHO              ; A = 0: message shown
        lda STATE
        cmp #3
        bne BannerWantedNone
        jsr IsCoop
        beq BannerWantedNone
        lda P1_OUT
        beq BannerWantedP2
        lda P2_STATE
        beq BannerWantedNone
        jsr P2TotalLives
        cmp #2
        bcc BannerWantedOut1
        lda #1                  ; P2 SELECT TO REVIVE P1
        rts
BannerWantedOut1:
        lda #3                  ; P1 OUT
        rts
BannerWantedP2:
        lda P2_STATE
        bne BannerWantedNone
        jsr P1TotalLives
        cmp #2
        bcc BannerWantedOut2
        lda #2                  ; P1 SELECT TO REVIVE P2
        rts
BannerWantedOut2:
        lda #4                  ; P2 OUT
        rts
BannerWantedNone:
        lda #0
        rts

BLANK_ROW = $E1F2               ; 26 x $10 in the original ROM
BannerRow1Lo:   .byte <BLANK_ROW, <BanReviveP1, <BanReviveP2, <BanOutP1, <BanOutP2, <BanReadyP1, <BanReadyP2, <BanReadyBoth, <BanReady, <BanGoP1, <BanGoP2, <BanGoBoth, <BanGo
BannerRow1Hi:   .byte >BLANK_ROW, >BanReviveP1, >BanReviveP2, >BanOutP1, >BanOutP2, >BanReadyP1, >BanReadyP2, >BanReadyBoth, >BanReady, >BanGoP1, >BanGoP2, >BanGoBoth, >BanGo
; red letters and red digits ($0A "1", $0B "2", $0C "4")
BanReviveP1:    ; "P2 SELECT TO REVIVE P1"
        .byte $10, $10, $20, $0B, $10, $23, $15, $1C, $15, $13, $24, $10, $24
        .byte $1F, $10, $22, $15, $26, $19, $26, $15, $10, $20, $0A, $10, $10
BanReviveP2:    ; "P1 SELECT TO REVIVE P2"
        .byte $10, $10, $20, $0A, $10, $23, $15, $1C, $15, $13, $24, $10, $24
        .byte $1F, $10, $22, $15, $26, $19, $26, $15, $10, $20, $0B, $10, $10
BanOutP1:       ; "P1 OUT"
        .byte $10, $10, $10, $10, $10, $10, $10, $10, $10, $10, $20, $0A, $10
        .byte $1F, $25, $24, $10, $10, $10, $10, $10, $10, $10, $10, $10, $10
BanOutP2:       ; "P2 OUT"
        .byte $10, $10, $10, $10, $10, $10, $10, $10, $10, $10, $20, $0B, $10
        .byte $1F, $25, $24, $10, $10, $10, $10, $10, $10, $10, $10, $10, $10
BanReadyP1:    ; "P1 W4 READY NEXT STAGE"
        .byte $10, $10, $20, $0A, $10, $27, $04, $10, $22, $15, $11, $14, $29
        .byte $10, $1E, $15, $28, $24, $10, $23, $24, $11, $17, $15, $10, $10
BanReadyP2:    ; "P2 W4 READY NEXT STAGE"
        .byte $10, $10, $20, $0B, $10, $27, $04, $10, $22, $15, $11, $14, $29
        .byte $10, $1E, $15, $28, $24, $10, $23, $24, $11, $17, $15, $10, $10
BanReadyBoth:  ; "P1 P2 W4 READY NEXT STAGE"
        .byte $20, $0A, $10, $20, $0B, $10, $27, $04, $10, $22, $15, $11, $14
        .byte $29, $10, $1E, $15, $28, $24, $10, $23, $24, $11, $17, $15, $10
BanReady:      ; "OVERDRIVE READY NEXT STAGE"
        .byte $1F, $26, $15, $22, $14, $22, $19, $26, $15, $10, $22, $15, $11
        .byte $14, $29, $10, $1E, $15, $28, $24, $10, $23, $24, $11, $17, $15
BanGoP1:       ; "P1 OVERDRIVE!"
        .byte $10, $10, $10, $10, $10, $10, $20, $0A, $10, $1F, $26, $15, $22
        .byte $14, $22, $19, $26, $15, $34, $10, $10, $10, $10, $10, $10, $10
BanGoP2:       ; "P2 OVERDRIVE!"
        .byte $10, $10, $10, $10, $10, $10, $20, $0B, $10, $1F, $26, $15, $22
        .byte $14, $22, $19, $26, $15, $34, $10, $10, $10, $10, $10, $10, $10
BanGoBoth:     ; "P1 P2 OVERDRIVE!"
        .byte $10, $10, $10, $10, $10, $20, $0A, $10, $20, $0B, $10, $1F, $26
        .byte $15, $22, $14, $22, $19, $26, $15, $34, $10, $10, $10, $10, $10
BanGo:         ; "OVERDRIVE!"
        .byte $10, $10, $10, $10, $10, $10, $10, $10, $1F, $26, $15, $22, $14
        .byte $22, $19, $26, $15, $34, $10, $10, $10, $10, $10, $10, $10, $10

; ---------------------------------------------------------------- title badge
; "CO-OP" as 5 sprites rising 2 px per letter over the logo's bottom-right
; corner, once the title has settled (menu). Red, with a short white glint
; every 64 frames (sprite palette 1 / 0; sprite tiles from $1000 on the title).
BADGE_X = 168
BADGE_Y = 99                    ; OAM Y of the first letter (line 100)
TitleBadge:
        lda STATE
        cmp #1
        bne TitleBadgeDone
        lda SUBSTATE
        cmp #2
        bne TitleBadgeDone
        lda $F7
        cmp #$EF
        bne TitleBadgeDone
        lda $0104
        and #$3F
        cmp #8
        lda #1                  ; red
        bcs TitleBadgeAttr
        lda #0                  ; glint: white
TitleBadgeAttr:
        sta T0
        ldx #0
        ldy #0
TitleBadgeLoop:
        lda BadgeY,x
        sta P2_OAM,y
        lda BadgeTile,x
        sta P2_OAM+1,y
        lda T0
        sta P2_OAM+2,y
        lda BadgeX,x
        sta P2_OAM+3,y
        iny
        iny
        iny
        iny
        inx
        cpx #5
        bcc TitleBadgeLoop
TitleBadgeDone:
        rts
BadgeTile:      .byte $13, $1F, $2B, $1F, $20      ; C O - O P
BadgeX:         .byte BADGE_X, BADGE_X + 8, BADGE_X + 16, BADGE_X + 24, BADGE_X + 32
BadgeY:         .byte BADGE_Y, BADGE_Y - 2, BADGE_Y - 4, BADGE_Y - 6, BADGE_Y - 8

; ---------------------------------------------------------------- HUD
; The HUD buffer $0690-$06BB is streamed by E342 to VRAM $2074-$209F
; (row 3 col 20 .. row 4 col 31). E2FE fills $06A0-$06AE (P1 score, hi
; score) after this runs. Co-op layout (rows 3 / 4):
;   col 1 ship icon, cols 2-3 "X" + lives   cols 5-7 "1UP", 4-9 P1 score
;   cols 12-19 "HI-SCORE", 13-18 hi score
;   cols 23-25 "2UP", 21-26 P2 score        col 28 ship icon, 29-30 "X" + lives
; Lives = all ships left including the one in play. The P2 icon uses
; palette 1 (blue wings, like the P2 ship): attribute bytes $23C7/$23CF.
; The stage flags (E8B2, cols 25-29) don't fit and are not shown in co-op.
LIFE_TOP    = $6E
LIFE_BOT    = $6F
X_TILE      = $28       ; letter X
SECONDS_TILE = $36      ; "s" after the overdrive seconds (CHR, build.py)
EXCL_TILE   = $34       ; "!" of "OVERDRIVE!" (CHR, build.py)
W_TILE      = $27       ; letter W
VQ_LO2      = $0748     ; VRAM queue (E4EF): second byte, first byte,
VQ_LO1      = $0758     ; address low, address high; count in $E1 (max 16)
VQ_ADDR_LO  = $0768
VQ_ADDR_HI  = $0778
VQ_COUNT    = $E1

CoopHud:
        ldx #11
        lda #$10
CoopHudClear:
        sta $0690,x
        sta $06B0,x
        dex
        bpl CoopHudClear
        lda #$0B                ; "2UP"
        sta $0693
        lda #$25
        sta $0694
        lda #$20
        sta $0695
        ldx #5
CoopHudScore:
        lda $0129,x
        sta $06B1,x             ; row 4 cols 21-26 (col 27 left blank)
        dex
        bpl CoopHudScore
        lda #LIFE_BOT           ; P2: icon rows 3-4 col 28, row 4 cols 29-30
        sta $06B8
        lda #LIFE_TOP
        sta $0698
        lda #X_TILE
        sta $06B9
        jsr P2TotalLives
        sta $06BA
        lda #W_TILE             ; weapon level: row 3 cols 29-30
        sta $0699
        ldy WLEVEL+1
        lda WLevelTile,y
        sta $069A
        ldx VQ_COUNT            ; P2 icon palette: two attribute bytes
        cpx #15
        bcs CoopHudDone
        lda #$10                ; $23C7 = %00010000: rows 2-3, cols 28-29 -> palette 1
        ldy #$01                ; $23CF = %00000001: rows 4-5, cols 28-29 -> palette 1
        jsr HudAttrQueue
CoopHudDone:
        rts

; New game (both modes): rows 3-4 cols 20-31 of the HUD buffer blank. In
; co-op CoopHud fills them; in 1 PILOT only the original stage flags go
; there (E8B2 runs right after, FA41). RC1-RC5 left a co-op game's P2
; fields ("U" of 2UP, a score digit, W and X digits: cols 24 and 30) in a
; following 1 PILOT game.
HudRightClear:
        ldx #11
        lda #$10
HudRightClearLoop:
        sta $0690,x
        sta $06B0,x
        dex
        bpl HudRightClearLoop
        rts

; E8B2's first instruction: in co-op return from E8B2 (no flags in P2's
; area); else E88D, its own check (it returns from E8B2 outside a game).
StageFlags:
        jsr IsCoop
        bne StageFlagsCoop
        jmp $E88D
StageFlagsCoop:
        pla
        pla
        rts

; P1 lives (both modes): icon rows 3-4 col 1, "X" + lives row 4 cols 2-3.
HudP1Lives:
        lda #$10
        sta $069C
        lda #LIFE_BOT
        sta $069D
        lda #X_TILE
        sta $069E
        jsr P1TotalLives
        sta $069F
        ldx VQ_COUNT            ; row 3 cols 1-4 is outside the buffer:
        cpx #15                 ; icon top, "W", weapon level, blank
        bcs HudP1LivesDone
        lda #$20
        sta VQ_ADDR_HI,x
        sta VQ_ADDR_HI+1,x
        lda #$61
        sta VQ_ADDR_LO,x
        lda #$63
        sta VQ_ADDR_LO+1,x
        lda #LIFE_TOP
        sta VQ_LO1,x
        lda #W_TILE
        sta VQ_LO2,x
        ldy WLEVEL
        lda WLevelTile,y
        sta VQ_LO1+1,x
        lda #$10
        sta VQ_LO2+1,x
        inx
        inx
        stx VQ_COUNT
HudP1LivesDone:
        rts

WLevelTile:     .byte $01, $02, $03, $0C   ; W1-W3 white digits, W4 red "4"

; 1P game: put the two attribute bytes back to the original 0.
HudAttrReset:
        ldx VQ_COUNT
        cpx #15
        bcs CoopHudDone
        lda #0
        tay
; X = queue slot, A -> $23C7, Y -> $23CF ($23C6 / $23CE stay 0, as in the game)
HudAttrQueue:
        sta VQ_LO2,x
        tya
        sta VQ_LO2+1,x
        lda #$23
        sta VQ_ADDR_HI,x
        sta VQ_ADDR_HI+1,x
        lda #$C6
        sta VQ_ADDR_LO,x
        lda #$CE
        sta VQ_ADDR_LO+1,x
        lda #0
        sta VQ_LO1,x
        sta VQ_LO1+1,x
        inx
        inx
        stx VQ_COUNT
        rts

; All ships P1 has left, including the one in play or about to respawn.
P1TotalLives:
        lda P1_OUT
        bne LivesZero
        lda P1_DEAD
        beq LivesPlusOne1
        lda P1_GRANTED
        bne LivesPlusOne1
        lda LIVES1
        jmp LivesDigit
LivesPlusOne1:
        lda LIVES1
        clc
        adc #1
        jmp LivesDigit

P2TotalLives:
        lda P2_STATE
        cmp #1
        beq P2LivesInPlay
        lda LIVES2              ; out / exploding / waiting: no ship in play
        jmp LivesDigit
P2LivesInPlay:
        lda LIVES2
        clc
        adc #1
LivesDigit:                     ; digit tiles $00-$09
        cmp #10
        bcc LivesDigitDone
        lda #9
LivesDigitDone:
        rts
LivesZero:
        lda #0
        rts

; E321 only compares the current player's score with the hi score; do the
; same for P2 (digits 0-9, $10 = blank, most significant first).
CoopHiScore:
        ldx #5
        sec
CoopHiScoreCmp:
        lda $0129,x
        and #$0F
        sta T0
        lda $0120,x
        and #$0F
        sbc T0
        dex
        bpl CoopHiScoreCmp
        bcs CoopHiScoreDone
        ldx #5
CoopHiScoreCopy:
        lda $0129,x
        sta $0120,x
        dex
        bpl CoopHiScoreCopy
        lda #1                  ; HudScores: show the new hi score
        sta SCORE_NEW
CoopHiScoreDone:
        rts

; Same rules as the P1 routine at EEC0: 1 px/frame, clamp $96..$6A.
P2Move:
        lda PAD2
        and #$02                ; Left
        beq P2MoveRight
        lda P2_X
        cmp #$96
        beq P2MoveRight
        dec P2_X
P2MoveRight:
        lda PAD2
        and #$01                ; Right
        beq P2MoveDone
        lda P2_X
        cmp #$6A
        beq P2MoveDone
        inc P2_X
P2MoveDone:
        rts

; The ship graphic is symmetric about its centre column, so one tile per
; half is drawn twice: left copy at x0+1, H-flipped copy at x0+8.
P2Draw:
        jsr IsCoop
        beq P2DrawOff
        lda SUBSTATE
        cmp #3                  ; 0-2: screen setup / wipe
        bcs P2DrawOn
P2DrawOff:
        jmp P2Hide
P2DrawOn:
        lda P2_STATE
        cmp #2
        beq P2DrawExplosion
        cmp #1
        beq P2DrawShip
        jmp P2HideShip
P2DrawShip:
        lda SHIELD+1            ; respawn shield: blink
        beq P2DrawShipOn
        jsr ShieldHidden
        beq P2DrawShipOn
        jmp P2HideShip
P2DrawShipOn:
        lda #SHIP_OAM_Y
        sta P2_OAM+0
        sta P2_OAM+4
        lda #SHIP_OAM_Y+8
        sta P2_OAM+8
        sta P2_OAM+12
        lda #P2_TILE_TOP
        sta P2_OAM+1
        sta P2_OAM+5
        lda #P2_TILE_BOT
        sta P2_OAM+9
        sta P2_OAM+13
        lda #P2_ATTR
        sta P2_OAM+2
        sta P2_OAM+10
        lda #P2_ATTR+$40
        sta P2_OAM+6
        sta P2_OAM+14
        lda P2_X
        clc
        adc #$79
        sta P2_OAM+3
        sta P2_OAM+11
        clc
        adc #7
        sta P2_OAM+7
        sta P2_OAM+15
        rts

; 4 frames of the enemy explosion, 8 NMIs each, in the tile order ED8A uses:
; TL = base+2, TR = base, BL = base+3, BR = base+1, palette 1.
P2DrawExplosion:
        lda P2_TIMER
        and #$18
        lsr a
        clc
        adc #EXPL_TILE
        sta P2_OAM+5
        tax
        inx
        stx P2_OAM+13
        inx
        stx P2_OAM+1
        inx
        stx P2_OAM+9
        lda #SHIP_OAM_Y
        sta P2_OAM+0
        sta P2_OAM+4
        lda #SHIP_OAM_Y+8
        sta P2_OAM+8
        sta P2_OAM+12
        lda #1
        sta P2_OAM+2
        sta P2_OAM+6
        sta P2_OAM+10
        sta P2_OAM+14
        lda P2_X
        clc
        adc #$78
        sta P2_OAM+3
        sta P2_OAM+11
        clc
        adc #8
        sta P2_OAM+7
        sta P2_OAM+15
        rts

P2Hide:
P2HideShip:
        lda #$F8
        sta P2_OAM+0
        sta P2_OAM+4
        sta P2_OAM+8
        sta P2_OAM+12
        rts
