"""RC3 checks repeated in a second emulator: the FCEUmm core (as used by
RetroArch) through stable-retro. Optional:

    pip install stable-retro numpy
    python3 games/galaxian-coop/tests/test_fceumm.py -v

Same RAM addresses as test_coop.py. Passing here is still not a test on
RetroArch itself or on hardware.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parents[1] / 'tools'), str(GAME / 'src')]
import build  # noqa: E402

ORIG = Path(os.environ.get('GALAXIAN_ROM', build.DEFAULT_ROM))
try:
    import stable_retro as retro
except ImportError:
    retro = None

BTN = {'B': 0, 'SELECT': 2, 'START': 3, 'LEFT': 6, 'RIGHT': 7, 'A': 8}
STATE, SUBSTATE, SHIP_X, P1_DEAD, LIVES1, LIVES2 = 0xFF, 0xFE, 0xE4, 0x4F, 0x42, 0x43
COOP, P1_OUT, P2_STATE, P2_X = 0x05, 0x06, 0x08, 0x09


def _symbols():
    from asm6502 import Assembler
    asm = Assembler()
    build.assemble(asm)
    return asm.symbols


SYM = _symbols()        # addresses of the mod's variables, from coop.asm
BUL_Y, BUL_X, WLEVEL, SHIELD = SYM['BUL_Y'], SYM['BUL_X'], SYM['WLEVEL'], SYM['SHIELD']
SHOT_OAM = (0x280, 0x2BC, 0x2C0, 0x2C4, 0x2B0, 0x2B4, 0x2B8, 0x2C8)


class Emu:
    """One stable-retro emulator per process at a time."""

    def __init__(self, path):
        self.em = retro.RetroEmulator(str(path))
        self.data = retro.data.GameData()
        self.em.configure_data(self.data)

    def __getitem__(self, addr):
        return int(self.data.memory.extract(addr, '|u1'))

    def __setitem__(self, addr, value):
        self.data.memory.assign(addr, '|u1', value)

    def step(self, p1=(), p2=(), frames=1):
        for _ in range(frames):
            for player, buttons in ((0, p1), (1, p2)):
                mask = np.zeros(9, np.uint8)
                for b in buttons:
                    mask[BTN[b]] = 1
                self.em.set_button_mask(mask, player)
            self.em.step()
            self.data.update_ram()

    def calm(self):
        """No enemy bullets, no divers (their sprites hidden too: a stopped
        diver's sprites would stay on screen and fill scanlines)."""
        for k in range(7):
            self[0x284 + 4 * k] = 0
        for k in range(8):
            self[0x738 + k] = 0
        for a in range(0x200, 0x280, 4):
            self[a] = 0xF8

    def alive(self, pilot):
        return (self[P1_DEAD] == 0 and not self[P1_OUT]) if pilot == 0 else self[P2_STATE] == 1

    def flying(self, pilot):
        return sum(1 for k in range(4) if self[BUL_Y + 4 * pilot + k])

    def close(self):
        del self.em


@unittest.skipUnless(retro is not None and ORIG.exists(), 'needs stable-retro and the original ROM')
class TestFceumm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.rom = Path(cls.tmp.name) / 'coop.nes'
        build.build(ORIG, cls.rom)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        e = self.e = Emu(self.rom)
        e.step(frames=150)
        for _ in range(40):
            if e[0x31] & 1:
                break
            e.step(('SELECT',), frames=6)
            e.step(frames=6)
        for _ in range(60):
            if e[STATE] == 3:
                break
            e.step(('START',), frames=6)
            e.step(frames=6)
        for _ in range(1200):
            if e[STATE] == 3 and e[SUBSTATE] == 8 and e[P1_DEAD] == 0 and e[P2_STATE] == 1:
                break
            e.step()
        for _ in range(130):                             # P1 far left, P2 far right
            e.calm()
            e.step(('LEFT',), ('RIGHT',))
        for _ in range(60):
            e.calm()
            e.step()
        e[LIVES1] = e[LIVES2] = 5

    def tearDown(self):
        self.e.close()

    def shot(self, pilot, level):
        """One press: frames to the shot, its Y per frame, X unchanged."""
        e = self.e
        e[WLEVEL], e[WLEVEL + 1] = level, level
        for k in range(8):
            e[BUL_Y + k] = 0
        e.step()
        lat, ys, xs = None, [], set()
        for f in range(80):
            e.calm()
            fire = ('B',) if f < 6 else ()
            e.step(fire if pilot == 0 else (), fire if pilot == 1 else ())
            y = e[BUL_Y + 4 * pilot]
            if y and lat is None:
                lat = f + 1
            if lat is not None:
                if y == 0:
                    break
                ys.append(y)
                xs.add(e[BUL_X + 4 * pilot])
        return lat, ys, len(xs)

    def test_weapon_parity_and_fire(self):
        e = self.e
        for level, flight in ((0, 50), (1, 46), (2, 42), (3, 32)):
            p1, p2 = self.shot(0, level), self.shot(1, level)
            self.assertEqual(p1, p2, f'W{level + 1}: P1 and P2 identical')
            self.assertEqual((p1[0], len(p1[1]), p1[2]), (2, flight, 1), f'W{level + 1}')
            new = [0, 0]                                 # FIRE held 120 frames: one shot each
            prev = [e[BUL_Y + k] for k in range(8)]
            for _ in range(120):
                e.calm()
                e.step(('B',), ('B',))
                cur = [e[BUL_Y + k] for k in range(8)]
                for k in range(8):
                    new[k // 4] += cur[k] > prev[k]
                prev = cur
            self.assertEqual(new, [1, 1], f'W{level + 1}: no auto fire')
            e.step(frames=60)
            for k in range(8):                           # quick presses fill the pool,
                e[BUL_Y + k] = 0                         # every shot from the ship's X
            for i in range(4 * (level + 2)):
                e.calm()
                fire = ('B',) if (i // 2) % 2 == 0 else ()
                e.step(fire, fire)
            for pilot in (0, 1):
                xs = {e[BUL_X + 4 * pilot + k] for k in range(4) if e[BUL_Y + 4 * pilot + k]}
                self.assertEqual((e.flying(pilot), len(xs)), (level + 1, 1), f'P{pilot + 1} W{level + 1} pool')
            e.step(frames=60)

    def ghost_free_absence(self, pilot):
        e = self.e
        e[WLEVEL + pilot] = 3
        for i in range(16):
            fire = ('B',) if (i // 2) % 2 == 0 else ()
            e.calm()
            e.step(fire if pilot == 0 else (), fire if pilot == 1 else ())
        self.assertEqual(e.flying(pilot), 4)
        x = e[SHIP_X] if pilot == 0 else e[P2_X]
        e[0x284], e[0x287] = 0xC4, (x + 0x7C) & 0xFF
        for _ in range(12):
            e.step()
            if not e.alive(pilot):
                break
        self.assertFalse(e.alive(pilot), 'hit')
        self.assertEqual(e.flying(pilot), 0, 'shots removed')
        sprites = [a for a in SHOT_OAM[4 * pilot:4 * pilot + 4] if e[a] < 0xEF and e[a + 1] in (0x30, 0x60)]
        self.assertEqual(sprites, [], 'shot sprites hidden at the hit')
        for i in range(900):
            fire = ('B',) if (i // 3) % 2 == 0 else ()
            e[WLEVEL + 1 - pilot] = 3
            e.step(fire, fire)
            if e.alive(pilot) and e[SUBSTATE] == 8:
                break
            self.assertEqual(e.flying(pilot), 0, f'frame {i}: shot in RAM')
            sprites = [a for a in SHOT_OAM[4 * pilot:4 * pilot + 4] if e[a] < 0xEF and e[a + 1] in (0x30, 0x60)]
            self.assertEqual(sprites, [], f'frame {i}: shot sprite')
        self.assertTrue(e.alive(pilot), 'back')
        self.assertEqual(e[WLEVEL + pilot], 0, 'W1')
        self.assertGreater(e[SHIELD + pilot], 200, 'shield')
        for _ in range(5):                               # shielded: enemy bullets pass
            x = e[SHIP_X] if pilot == 0 else e[P2_X]
            e[0x284], e[0x287] = 0xC4, (x + 0x7C) & 0xFF
            e.step(frames=6)
            self.assertTrue(e.alive(pilot), 'shield holds')

    def test_shot_origins_every_slot(self):
        """RC4: ships moving left and right, both pilots firing on W1-W4: every
        new shot of every slot starts at its ship (x = ship x + $7C, the x the
        ship is drawn at in that frame), keeps that x in RAM and OAM for its
        whole flight, and is drawn there (pixels: column x+4, the pilot's
        colour, symmetric: 1 px bullet, 3 px laser), P1 palette 2, P2 palette 0."""
        import random
        e = self.e
        rnd = random.Random(4)
        fired = [0] * 8
        checked = [0] * 8
        dropped = [0, 0]
        colours = ({}, {})
        for level in (0, 1, 2, 3):
            e[WLEVEL], e[WLEVEL + 1] = level, level
            e[SYM['W4_SEC']], e[SYM['W4_SEC'] + 1] = (30, 30) if level == 3 else (0, 0)
            track = {}
            hold = ['', '']
            for f in range(900):
                e.calm()
                e[LIVES1] = e[LIVES2] = 5
                if f % 25 == 0:
                    hold = [rnd.choice(['', 'LEFT', 'RIGHT']), rnd.choice(['', 'LEFT', 'RIGHT'])]
                b1 = tuple(x for x in (hold[0], 'B' if f % 4 < 2 else '') if x)
                b2 = tuple(x for x in (hold[1], 'B' if (f + 1) % 4 < 2 else '') if x)
                before = [e[BUL_Y + k] for k in range(8)]
                oam = [(e[a], e[a + 1], e[a + 2], e[a + 3]) for a in SHOT_OAM]
                ys = [e[a] for a in range(0x200, 0x300, 4)]       # the OAM this frame shows
                e.step(b1, b2)
                screen = e.em.get_screen()
                ships = (e[SHIP_X], e[P2_X])
                for k in range(8):
                    y, x = e[BUL_Y + k], e[BUL_X + k]
                    if y and (before[k] == 0 or y > before[k]):          # fired this frame
                        if e[SUBSTATE] == 8:                # (at a stage end the ships go to their start)
                            fired[k] += 1
                            self.assertEqual(x, (ships[k // 4] + 0x7C) & 0xFF,
                                             f'slot {k} W{level + 1} starts at the ship (frame {f})')
                        track[k] = x
                    elif y:
                        self.assertEqual(x, track.get(k, x), f'slot {k} x changed in flight')
                    else:
                        track.pop(k, None)
                for k, (oy, tile, attr, ox) in enumerate(oam):     # the picture of this frame
                    if not (0x30 <= oy < 0xC0) or tile not in (0x30, 0x60):
                        continue
                    self.assertEqual(attr & 3, 2 if k < 4 else 0, f'slot {k} palette')
                    py, px = oy + 6 - 8, ox + 4 - 8                  # the core shows 224 x 240 (8 px cropped)
                    if not 3 <= px < 240 - 3:
                        continue
                    line = oy + 6
                    on_line = sum(1 for y0 in ys if y0 < 0xEF and y0 < line <= y0 + 8)
                    mid = tuple(int(v) for v in screen[py, px])
                    if on_line > 8 and mid == (0, 0, 0):
                        dropped[k // 4] += 1                        # 8-sprites-per-line limit
                        continue
                    self.assertNotEqual(mid, (0, 0, 0), f'slot {k} drawn at x+4 ({on_line} sprites on the line)')
                    if screen[py, px - 3].any() or screen[py, px + 3].any():
                        continue                                    # over an enemy or a star
                    lit = [tuple(int(v) for v in screen[py, px + d]) == mid for d in range(-3, 4)]
                    if sum(lit) != (3 if tile == 0x60 else 1):
                        continue                                    # another sprite touches it
                    self.assertEqual(lit, lit[::-1], f'slot {k} W{level + 1} x {ox:02X} frame {f}: centred on x+4')
                    colours[k // 4][mid] = colours[k // 4].get(mid, 0) + 1
                    checked[k] += 1
        self.assertTrue(all(fired), f'every slot fired: {fired}')
        self.assertTrue(all(c >= 20 for c in checked), f'pictures checked per slot: {checked}')
        print(f'\n  shots hidden by the sprite limit: P1 {dropped[0]}, P2 {dropped[1]}', file=sys.stderr)
        self.assertEqual(len(colours[0]), 1, colours[0])
        self.assertEqual(len(colours[1]), 1, colours[1])
        self.assertNotEqual(colours[0], colours[1], 'P1 and P2 shots in different colours')
        (g1,), (o2,) = colours[0], colours[1]               # RC5: P1 green, P2 orange
        self.assertTrue(g1[1] > g1[0] + 80 and g1[1] > g1[2] + 80, f'P1 green {g1}')
        self.assertTrue(o2[0] > o2[1] > o2[2] + 40, f'P2 orange {o2}')

    def test_ship_silhouettes(self):
        """RC5: P1 the original ship, P2 its own (build.P2_PIXELS): both
        pictures matched pixel mask by pixel mask while the ships move, with
        P1 and P2 each in exactly 3 colours, and no colour shared between the
        ships but white."""
        e = self.e
        p1 = [[v != 0 for v in r] for r in build.p1_ship(self.rom.read_bytes()[-0x2000:])]
        p2 = [[c != '.' for c in r] for r in build.P2_PIXELS]
        self.assertNotEqual(p1, p2)
        matched = [0, 0]
        cols = (set(), set())
        for i in range(200):
            e.calm()
            m1 = 'RIGHT' if (i // 50) % 2 == 0 else 'LEFT'
            oam = [e[0x2A0 + k] for k in range(4)]
            x1 = e[SHIP_X]
            e.step((m1,), ('LEFT' if m1 == 'RIGHT' else 'RIGHT',))
            screen = e.em.get_screen()
            places = ((209 - 8, 120 + ((x1 + 128) & 0xFF) - 128 - 8), (oam[0] + 1 - 8, oam[3] - 1 - 8))
            for k, (mask, (top, left)) in enumerate(zip((p1, p2), places)):
                for dx in (0, -1, 1, -2, 2):
                    x = left + dx
                    if x < 0 or x + 16 > screen.shape[1]:
                        continue
                    box = screen[top:top + 16, x:x + 16]
                    lit = box.any(2)
                    want = np.array(mask)
                    if (lit[want]).all() and int((lit & ~want).sum()) <= 2:
                        matched[k] += 1
                        cols[k].update(tuple(int(v) for v in box[r, c]) for r, c in zip(*np.nonzero(want)))
                        break
        self.assertGreaterEqual(min(matched), 190, matched)      # (a ship at a cropped edge may not fit)
        self.assertEqual([len(c) for c in cols], [3, 3], cols)
        self.assertEqual(len(cols[0] & cols[1]), 1, 'only white in common')

    def test_p1_death_no_ghost_shots(self):
        self.ghost_free_absence(0)

    def test_p2_death_no_ghost_shots(self):
        self.ghost_free_absence(1)


    def next_stage(self, e):
        """Clear the stage; stop right before F0, the first frame of the next
        stage with its formation drawn (the frame the game clears OD_ARM)."""
        stage = e[0x59]
        for k in range(10):
            e[0xC3 + k] = 0
        for _ in range(900):
            e[LIVES1] = e[LIVES2] = 5
            for k in range(8):
                e[0x738 + k] = 0
            e.step()
            if e[0x59] != stage and e[SUBSTATE] == 8:
                break
        for _ in range(60):
            st = e.em.get_state()
            e.step()
            if not e[SYM['OD_ARM']]:
                e.em.set_state(st)
                e.data.update_ram()
                return
        self.fail('no F0')

    def test_overdrive_starts_with_next_stage(self):
        """RC6: READY (W3 + 8000 no-death points by a real kill) keeps W3;
        F0 of the next stage: W4 for 12 s and 3 aliens leave the formation
        (diver state 1); F1-F3 they move."""
        e = self.e
        e[WLEVEL] = 2
        e[SYM['NODEATH_LO']], e[SYM['NODEATH_HI']] = 799 & 0xFF, 799 >> 8
        e[SHIP_X] = 0xE0
        for i in range(1500):
            e.calm()
            e.step(('B',) if i % 4 < 2 else ())
            if e[SYM['OD_PEND']]:
                break
        self.assertEqual((e[WLEVEL], e[SYM['OD_PEND']], e[SYM['W4_SEC']]), (2, 1, 0), 'READY, still W3')
        self.next_stage(e)
        self.assertEqual([e[0x738 + k] for k in range(8)], [0] * 8)
        e.step()
        self.assertEqual((e[WLEVEL], e[SYM['W4_SEC']], e[SYM['W4_FRM']]), (3, 12, 59))
        launched = [k for k in range(7) if e[0x738 + k] == 1]
        self.assertEqual(len(launched), 3)
        pos = {k: (e[0x200 + 16 * k], e[0x203 + 16 * k]) for k in launched}
        for f in range(3):
            e.step()
            for k in launched:
                now = (e[0x200 + 16 * k], e[0x203 + 16 * k])
                self.assertNotEqual(now, pos[k], f'F{f + 1} diver {k}')
                pos[k] = now

    def test_single_player_rules(self):
        """RC6 in 1 PILOT: the free W2 for stage 1 and the 4-s shield."""
        self.e.close()
        e = self.e = Emu(self.rom)
        e.step(frames=150)
        for _ in range(60):
            if e[STATE] == 3:
                break
            e.step(('START',), frames=6)
            e.step(frames=6)
        for _ in range(1200):
            if e[STATE] == 3 and e[SUBSTATE] == 8 and e[P1_DEAD] == 0:
                break
            e.step()
        self.assertEqual(e[COOP], 0)
        self.next_stage(e)
        e.step()
        self.assertEqual((e[WLEVEL], e[SYM['W2_OWNED']]), (1, 1), 'free W2 in 1P')
        for _ in range(130):
            e.calm()
            e.step(('LEFT',))
        x = e[SHIP_X]
        e[0x284], e[0x287] = 0xC4, (x + 0x7C) & 0xFF
        for _ in range(12):
            e.step()
            if not e.alive(0):
                break
        self.assertFalse(e.alive(0))
        self.assertEqual(e[SHIELD], 240)
        for _ in range(900):
            e.calm()
            e.step()
            if e.alive(0) and e[SUBSTATE] == 8:
                break
        self.assertEqual(e[WLEVEL], 1, 'back on W2')
        self.assertGreater(e[SHIELD], 200)
        for _ in range(5):
            x = e[SHIP_X]
            e[0x284], e[0x287] = 0xC4, (x + 0x7C) & 0xFF
            e.step(frames=6)
            self.assertTrue(e.alive(0), 'shield holds')


    def test_mode_switch_hud(self):
        """RC6, manual test report: a co-op game (P2 scores) to GAME OVER, then 1
        PILOT without restarting the core: the cells where co-op shows P2's
        fields (rows 3-4, cols 20-24 and 30-31) are blank in the picture in
        most frames (a star may cross a cell); the stage flag (col 25) is
        drawn. RC1-RC5 kept the "U" of 2UP, a score digit and P2's W and X
        digits there."""
        e = self.e
        for i in range(600):
            e[LIVES1] = e[LIVES2] = 3
            e.step(('B',) if i % 6 < 2 else (), ('B',) if i % 6 < 3 else ())
        for _ in range(60 * 60):                           # game over
            if e[STATE] != 3:
                break
            e[LIVES1] = e[LIVES2] = 0
            e[SHIELD] = e[SHIELD + 1] = 0
            for pilot, k in ((0, 0), (1, 1)):
                if e.alive(pilot) and not e[0x284 + 4 * k]:
                    x = e[SHIP_X] if pilot == 0 else e[P2_X]
                    e[0x284 + 4 * k], e[0x287 + 4 * k] = 0xC4, (x + 0x7C) & 0xFF
            e.step()
        for _ in range(60 * 60):
            if e[STATE] == 1:
                break
            e.step()
        self.assertEqual(e[STATE], 1, 'title')
        e.step(frames=60)
        for _ in range(40):
            if not e[0x31] & 1:
                break
            e.step(('SELECT',), frames=6)
            e.step(frames=6)
        for _ in range(60):
            if e[STATE] == 3:
                break
            e.step(('START',), frames=6)
            e.step(frames=6)
        for _ in range(1200):
            if e[STATE] == 3 and e[SUBSTATE] == 8 and e[P1_DEAD] == 0:
                break
            e.step()
        self.assertEqual(e[COOP], 0, '1 PILOT')
        lit = {}
        frames = 40
        for _ in range(frames):
            e.calm()
            e.step()
            img = e.em.get_screen()                        # 224 x 240: 8 px cropped top/bottom... per side
            for row in (3, 4):
                for col in (20, 21, 22, 23, 24, 25, 30, 31):
                    y, x = 8 * row + 1 - 8, 8 * col - 8
                    cell = img[y:y + 8, x:x + 8]
                    lit[(row, col)] = lit.get((row, col), 0) + int(cell.any())
        for (row, col), n in lit.items():
            if col == 25:
                self.assertEqual(n, frames, 'stage flag drawn')
            else:
                self.assertLess(n, frames // 2, f'row {row} col {col}: something drawn in {n} of {frames} frames')


if __name__ == '__main__':
    unittest.main()
