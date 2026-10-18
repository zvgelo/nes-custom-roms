"""Emulator tests for the Two Players Hack ROM built by build.py (FCEUmm core via stable-retro).

    pip install stable-retro numpy
    python3 games/super-mario-coop/tests/test_emulator.py -v

The RAM addresses below were found by comparing runs (pad 1 vs pad 2 held
RIGHT from the same save state); they are observations, not documentation
of the hack.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parents[1] / "tools"), str(GAME / "src")]
import build  # noqa: E402

ORIGINAL = Path(os.environ.get("SMB_ORIGINAL", build.DEFAULT_ROM))
try:
    import stable_retro as retro
except ImportError:
    retro = None

BTN = {"B": 0, "SELECT": 2, "START": 3, "UP": 4, "DOWN": 5, "LEFT": 6, "RIGHT": 7, "A": 8}
P1_X, P2_X = 0x8B, 0x8C          # horizontal position of the two player objects
CREDIT_ROWS = slice(120, 128)    # screen rows of the hack's "©2018 CORPSE GRINDER & TI" line (224-line frame)


class Emu:
    """One stable-retro emulator at a time (the library allows one per process)."""

    def __init__(self, path):
        self.em = retro.RetroEmulator(str(path))
        self.data = retro.data.GameData()
        self.em.configure_data(self.data)

    def press(self, p1=(), p2=(), frames=1):
        for _ in range(frames):
            for player, buttons in ((0, p1), (1, p2)):
                mask = np.zeros(9, np.uint8)
                for b in buttons:
                    mask[BTN[b]] = 1
                self.em.set_button_mask(mask, player)
            self.em.step()

    def ram(self):
        self.data.update_ram()
        b = self.data.memory.blocks
        return np.frombuffer(b[0] + b[1024], np.uint8).copy()

    def screen(self):
        return self.em.get_screen().copy()

    def close(self):
        del self.em


def title_screen(path):
    e = Emu(path)
    e.press(frames=120)
    s = e.screen()
    e.close()
    return s


@unittest.skipUnless(retro is not None and ORIGINAL.exists() and build.DEFAULT_PATCH.exists(),
                     "needs stable-retro, private/original.nes and the hack's patch in private/")
class TestEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.final = Path(cls.tmp.name) / build.DEFAULT_OUT.name
        build.build(ORIGINAL, cls.final)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_title_shows_the_hack_authors(self):
        built, original = title_screen(self.final), title_screen(ORIGINAL)
        changed = (built != original).any(axis=2)
        self.assertGreater(changed[CREDIT_ROWS].sum(), 200, "the hack's credit line is not drawn")
        rows = set(np.nonzero(changed.any(axis=1))[0])
        # besides the credit line the hack changes only the HUD (Luigi's score line) and the 2-player menu text
        self.assertLessEqual(rows - set(range(CREDIT_ROWS.start, CREDIT_ROWS.stop)), set(range(8, 23)) | set(range(152, 159)))

    def test_two_controllers_move_two_players(self):
        e = Emu(self.final)
        try:
            e.press(frames=90)
            e.press(p1=("SELECT",), frames=4)     # "2 PLAYERS GAME"
            e.press(frames=10)
            e.press(p1=("START",), frames=4)
            e.press(frames=240)
            start = e.em.get_state()
            runs = {}
            for name, (p1, p2) in {"idle": ((), ()), "p1": (("RIGHT",), ()), "p2": ((), ("RIGHT",)),
                                   "both": (("RIGHT",), ("RIGHT",))}.items():
                e.em.set_state(start)
                e.press(p1=p1, p2=p2, frames=60)
                runs[name] = e.ram()
        finally:
            e.close()
        idle = runs["idle"]
        self.assertGreater(int(runs["p1"][P1_X]), int(idle[P1_X]) + 30)
        self.assertEqual(runs["p1"][P2_X], idle[P2_X], "pad 1 moved player 2")
        self.assertGreater(int(runs["p2"][P2_X]), int(idle[P2_X]) + 30)
        self.assertEqual(runs["p2"][P1_X], idle[P1_X], "pad 2 moved player 1")
        self.assertGreater(int(runs["both"][P1_X]), int(idle[P1_X]) + 30)
        self.assertGreater(int(runs["both"][P2_X]), int(idle[P2_X]) + 30)


if __name__ == "__main__":
    unittest.main(verbosity=2 if "-v" in sys.argv else 1, argv=[sys.argv[0]])
