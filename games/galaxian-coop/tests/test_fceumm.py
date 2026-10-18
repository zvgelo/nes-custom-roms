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
BUL_Y, BUL_X, WLEVEL, SHIELD = 0x16, 0x0E, 0x45, 0x126
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
        for k in range(7):
            self[0x284 + 4 * k] = 0
        for k in range(8):
            self[0x738 + k] = 0

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

    def test_p1_death_no_ghost_shots(self):
        self.ghost_free_absence(0)

    def test_p2_death_no_ghost_shots(self):
        self.ghost_free_absence(1)


if __name__ == '__main__':
    unittest.main()
