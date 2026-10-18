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
P2_FIRE     = $0B       ; fire-button counter, same rule as $44 for P1
P2_BY       = $0C       ; P2 bullet Y: $C8 ready on the ship, 0 = consumed
P2_BX       = $0D       ; P2 bullet X
SAVE_BY     = $0E       ; P1 bullet saved while the P2 bullet borrows its slot
SAVE_BX     = $0F
T0          = $10
T1          = $11
AIM_TOGGLE  = $12       ; alternates the dive target between the players

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
; Stars used $02A0-$02FF (24 sprites); they now start at $02B4 (19 sprites).
P2_OAM      = $02A0     ; 4 sprites: TL, TR, BL, BR
P2_BUL_OAM  = $02B0     ; 1 sprite
BULLET_TILE = $30
EXPL_TILE   = $70       ; enemy explosion frames $70/$74/$78/$7C (2x2 each)
P2_TILE_TOP = $E1       ; sprite table tiles freed from the title logo
P2_TILE_BOT = $EA
P2_ATTR     = $00       ; sprite palette 0: orange tip, blue wings, white core
SHIP_OAM_Y  = $D0       ; BG ship's top row is scanline 209
RESPAWN_DELAY = 120     ; frames between P2's explosion and respawn

; ================================================================ hooks
; E913 is the gameplay frame (called in play, respawn and demo states).
; First call: P1 bullet vs enemies. CoopPre refreshes P1_BLOCK, runs it, then
; runs the same routine for the P2 bullet.
.patch $E913, "20 B3 F2"            ; JSR $F2B3
        jsr CoopPre
; Last relevant call is the diving-enemy update; P2 runs right after.
.patch $E91F, "20 B1 E9"            ; JSR $E9B1
        jsr CoopMid

; P1 checks that must ignore a P1 who is out of the game: read P1_BLOCK
; instead of $4F. In 1P / demo P1_BLOCK == $4F, so behaviour is unchanged.
.patch $EEC0, "A5 4F"               ; movement
        lda P1_BLOCK
.patch $E640, "A5 4F"               ; firing / bullet shown on the ship
        lda P1_BLOCK
.patch $E5DF, "E6 4F C6 4F"         ; enemy bullet vs P1
        inc P1_BLOCK
        dec P1_BLOCK
.patch $EC59, "E6 4F C6 4F"         ; diving enemy vs P1
        inc P1_BLOCK
        dec P1_BLOCK
; The two "P1 is hit" stores also set P1_BLOCK, so P1 can't be hit twice
; in one frame (as in the original, which re-read $4F).
.patch $E611, "A9 01 85 4F"
        jsr SetP1Dead
        nop
.patch $EC8F, "A9 01 85 4F"
        jsr SetP1Dead
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

; Dive target (EE4E computes the x a diver heads for from SHIP_X).
.patch $EE4E, "A6 9E A4 9D"         ; LDX $9E / LDY $9D
        jmp AimDiver
        nop

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
        ldx #$48
.patch $F041, "FE A0 02"
        inc $02B4,x
.patch $F044, "BD A0 02"
        lda $02B4,x
.patch $F04B, "DE A3 02"
        dec $02B7,x
.patch $F051, "9D A0 02"
        sta $02B4,x
.patch $F05B, "BD A3 02"
        lda $02B7,x
.patch $F061, "9D A3 02"
        sta $02B7,x
.patch $FC9B, "A0 5C A2 17"
        ldy #$48
        ldx #$12
.patch $FCA6, "99 A3 02"
        sta $02B7,y
.patch $FCAB, "99 A1 02"
        sta $02B5,y
.patch $FCB5, "99 A2 02"
        sta $02B6,y
.patch $FCBA, "99 A0 02"
        sta $02B4,y

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
        lda #3
        sta P2_FIRE
        lda #$C8
        sta P2_BY
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
        jsr IsCoop
        beq P1ShipRedrawGo
        lda P1_OUT
        bne P1ShipRedrawSkip
P1ShipRedrawGo:
        jmp $EFFF
P1ShipRedrawSkip:
        rts

; Replaces "LDA #1 / STA $4F" where P1 gets hit. Keeps A = 1.
SetP1Dead:
        lda #1
        sta P1_DEAD
        sta P1_BLOCK
        rts

; ---------------------------------------------------------------- E913 start
CoopPre:
        jsr IsCoop
        bne CoopPreCoop
        lda P1_DEAD
        sta P1_BLOCK
        jmp $F2B3
CoopPreCoop:
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
        sta P1_BLOCK
        jsr $F2B3
        jmp P2BulletHits

; Swap in the per-player variables used by the scoring code (E833 adds to
; the score row picked by $53 and gives the extra ship via $3D/$42).
SwapToP2:
        lda #1
        sta CUR_PLAYER
        bne SwapLives
SwapToP1:
        lda #0
        sta CUR_PLAYER
SwapLives:
        ldx LIVES1
        ldy LIVES2
        stx LIVES2
        sty LIVES1
        ldx BONUS1
        ldy BONUS2
        stx BONUS2
        sty BONUS1
        rts

; P2 bullet vs formation and divers: the original routines read the P1
; bullet slot, so the P2 bullet borrows it for the call.
P2BulletHits:
        lda P2_BY
        beq P2BulletHitsDone
        cmp #$C8
        beq P2BulletHitsDone
        lda P1_BUL_Y
        sta SAVE_BY
        lda P1_BUL_X
        sta SAVE_BX
        lda P2_BY
        sta P1_BUL_Y
        lda P2_BX
        sta P1_BUL_X
        jsr SwapToP2
        lda #0
        sta HIT_FLAG
        jsr $F381               ; formation (background) enemies
        jsr $F2D1               ; diving enemies
        jsr SwapToP1
        lda HIT_FLAG
        beq P2BulletRestore
        lda #0
        sta P2_BY
P2BulletRestore:
        lda SAVE_BY
        sta P1_BUL_Y
        lda SAVE_BX
        sta P1_BUL_X
P2BulletHitsDone:
        rts

; ---------------------------------------------------------------- after E9B1
CoopMid:
        jsr $E9B1
        jsr IsCoop
        beq CoopMidDone
        lda P2_STATE
        cmp #1
        beq P2Alive
        cmp #2
        beq P2Exploding
        cmp #3
        beq P2Waiting
        jmp P2Bullet            ; out: a shot in flight keeps going
CoopMidDone:
        rts

; Respawn after RESPAWN_DELAY frames, only during normal play (not while
; the original P1 respawn / wave sequence runs). LIVES2 counts reserve
; ships exactly like LIVES1: the ship entering play is taken from it.
P2Waiting:
        lda P2_TIMER
        cmp #RESPAWN_DELAY
        bcs P2WaitingReady
        inc P2_TIMER
        jmp P2Bullet
P2WaitingReady:
        lda SUBSTATE
        cmp #8
        bne P2WaitingDone
        dec LIVES2
        lda #0
        sta P2_X
        sta P2_TIMER
        lda #3
        sta P2_FIRE
        lda #1
        sta P2_STATE
P2WaitingDone:
        jmp P2Bullet

P2Alive:
        jsr P2Move
        jsr P2Bullet
        jsr P2VsBullets
        jmp P2VsDivers

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
        jmp P2Bullet

P2Kill:
        lda #2
        sta P2_STATE
        lda #0
        sta P2_TIMER
        jmp $FE64               ; explosion sound

; Same rules as E627: Y=$C8 is "ready on the ship", 4 px/frame, A or B fires
; once the counter (reset to 3 while released) runs out.
P2Bullet:
        lda P2_BY
        beq P2BulletReady
        cmp #$C8
        beq P2BulletAim
        sec
        sbc #4
        sta P2_BY
        bcs P2BulletDone
P2BulletReady:
        lda #$C8
        sta P2_BY
P2BulletAim:
        lda P2_STATE
        cmp #1
        bne P2BulletDone
        lda P2_X
        clc
        adc #$7C
        sta P2_BX
        lda PAD2
        and #$C0
        bne P2BulletHeld
        lda #3
        sta P2_FIRE
P2BulletHeld:
        dec P2_FIRE
        bne P2BulletDone
        jsr $FEA8               ; shot sound
        lda P2_BY
        sec
        sbc #4
        sta P2_BY
P2BulletDone:
        rts

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
        rts

; ---------------------------------------------------------------- EE4E
; With both ships alive, consecutive dives alternate between P1 and P2.
AimDiver:
        jsr IsCoop
        beq AimP1
        lda P2_STATE
        cmp #1
        bne AimP1
        lda P1_BLOCK
        bne AimP2
        inc AIM_TOGGLE
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
        rts
AimP1:
        ldx $9E
        ldy $9D
        jmp $EE52

; ---------------------------------------------------------------- NMI tail
CoopPost:
        jsr $E373
        jsr P2Draw
        jsr IsCoop
        beq CoopPostDone
        jsr CoopHud
        jmp CoopHiScore
CoopPostDone:
        rts

; ---------------------------------------------------------------- HUD
; The HUD buffer $0690-$06BB is streamed by E342 to VRAM $2074-$209F
; (row 3 col 20 .. row 4 col 31). E2FE fills $06A0-$06AE (P1 score, hi
; score) after this runs. Co-op layout, rows 3/4:
;   cols 1-3  P1 reserve ships   cols 5-7 "1UP", 4-9 P1 score
;   cols 12-19 "HI-SCORE", 13-18 hi score
;   cols 23-25 "2UP", 22-27 P2 score   cols 28-30 P2 reserve ships
; The stage flags (E8B2, cols 25-29) don't fit and are not shown in co-op.
LIFE_TOP    = $6E
LIFE_BOT    = $6F
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
        sta $06B2,x
        dex
        bpl CoopHudScore
        ldx #2
CoopHudLives2:
        cpx LIVES2
        bcs CoopHudLives2Next
        lda #LIFE_TOP
        sta $0698,x
        lda #LIFE_BOT
        sta $06B8,x
CoopHudLives2Next:
        dex
        bpl CoopHudLives2
        ldx #2
CoopHudLives1:
        lda #$10
        cpx LIVES1
        bcs CoopHudLives1Set
        lda #LIFE_BOT
CoopHudLives1Set:
        sta $069D,x             ; row 4 cols 1-3
        dex
        bpl CoopHudLives1
        ldx VQ_COUNT            ; row 3 cols 1-4 is outside the buffer:
        cpx #15                 ; queue two 2-byte writes
        bcs CoopHudDone
        lda #$20
        sta VQ_ADDR_HI,x
        sta VQ_ADDR_HI+1,x
        lda #$61
        sta VQ_ADDR_LO,x
        lda #$63
        sta VQ_ADDR_LO+1,x
        lda $069D
        jsr LifeTopTile
        sta VQ_LO1,x
        lda $069E
        jsr LifeTopTile
        sta VQ_LO2,x
        lda $069F
        jsr LifeTopTile
        sta VQ_LO1+1,x
        lda #$10
        sta VQ_LO2+1,x
        inx
        inx
        stx VQ_COUNT
CoopHudDone:
        rts

LifeTopTile:
        cmp #LIFE_BOT
        bne LifeTopTileBlank
        lda #LIFE_TOP
        rts
LifeTopTileBlank:
        lda #$10
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
        jsr P2DrawBullet
        lda P2_STATE
        cmp #2
        beq P2DrawExplosion
        cmp #1
        beq P2DrawShip
        jmp P2HideShip
P2DrawShip:
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

; Bullet: in flight -> shown; parked on the ship ($C8) -> shown only while
; P2 is alive (as E640 does for P1).
P2DrawBullet:
        lda P2_BY
        beq P2HideBullet
        cmp #$C8
        bne P2ShowBullet
        ldx P2_STATE
        cpx #1
        bne P2HideBullet
P2ShowBullet:
        sta P2_BUL_OAM+0
        lda #BULLET_TILE
        sta P2_BUL_OAM+1
        lda #0
        sta P2_BUL_OAM+2
        lda P2_BX
        sta P2_BUL_OAM+3
        rts

P2Hide:
        jsr P2HideBullet
P2HideShip:
        lda #$F8
        sta P2_OAM+0
        sta P2_OAM+4
        sta P2_OAM+8
        sta P2_OAM+12
        rts
P2HideBullet:
        lda #$F8
        sta P2_BUL_OAM+0
        rts
