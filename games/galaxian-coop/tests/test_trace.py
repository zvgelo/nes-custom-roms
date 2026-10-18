#!/usr/bin/env python3
"""Checks that need every CPU write: APU registers (sound) and who touches
what, run in tools/trace6502.py (a 6502 core with an NROM/PPU stub; no
picture, no audio output, approximate timing). Needs only the original ROM.

    python3 games/galaxian-coop/tests/test_trace.py [-v]

The tracer is not an emulator test of the game's look or timing: those are
in test_coop.py (cynes) and test_fceumm.py (FCEUmm).
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parents[1] / 'tools'), str(GAME / 'src')]
import build  # noqa: E402
from nestest import ines_compatible  # noqa: E402
from trace6502 import CPU  # noqa: E402

ORIG = Path(os.environ.get('GALAXIAN_ROM', build.DEFAULT_ROM))
B, SEL, START, LEFT, RIGHT = 0x40, 0x20, 0x10, 0x02, 0x01
STATE, SUBSTATE, P1_DEAD, P2_STATE, WLEVEL, NODEATH_LO, NODEATH_HI = 0xFF, 0xFE, 0x4F, 0x08, 0x45, 0x47, 0x49
ZAP = [0x82, 0x92, 0x50, 0x08]                  # $4004-$4007 of the overdrive shot
SHOT = [0x05, 0x84, 0x16, 0x08]                 # $4004-$4007 of FEA8 (the original shot)
ARPEGGIO = [0x77, 0x5E, 0x4F, 0x3B, 0x2F, 0x27, 0x1D]   # triangle periods, A#4 .. A#6


def symbols():
    from asm6502 import Assembler
    asm = Assembler()
    build.assemble(asm)
    return asm.symbols


def start_game(c, two, frames=3000):
    """Title -> menu choice -> game in normal play with P1 (and P2) in play."""
    for _ in range(150):
        c.run_frame()
    for _ in range(40):
        if (c.ram[0x31] & 1) == two:
            break
        c.pads = [SEL, 0]
        for _ in range(6):
            c.run_frame()
        c.pads = [0, 0]
        for _ in range(6):
            c.run_frame()
    for _ in range(60):
        if c.ram[STATE] == 3:
            break
        c.pads = [START, 0]
        for _ in range(6):
            c.run_frame()
        c.pads = [0, 0]
        for _ in range(6):
            c.run_frame()
    for _ in range(frames):
        if c.ram[STATE] == 3 and c.ram[SUBSTATE] == 8 and c.ram[P1_DEAD] == 0 and (not two or c.ram[P2_STATE] == 1):
            return
        c.run_frame()
    raise AssertionError('game did not start')


def writes(c, frame, regs):
    return [(r, v) for f, r, v, pc in c.apu if f == frame and r in regs]


@unittest.skipUnless(ORIG.exists(), f'original ROM not found: {ORIG}')
class TestTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        path = Path(cls.tmp.name) / 'coop.nes'
        build.build(ORIG, path)
        cls.rom = path.read_bytes()
        cls.orig = Path(ines_compatible(ORIG)).read_bytes()
        cls.sym = symbols()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def game(self, two=True):
        c = CPU(self.rom)
        c.log = False
        start_game(c, two)
        c.apu_log = True
        return c

    def keep_alive(self, c):
        """No enemy bullets, no divers, lives kept up (as test_coop.calm)."""
        for k in range(7):
            c.ram[0x284 + 4 * k] = 0
        for k in range(8):
            c.ram[0x738 + k] = 0
        c.ram[0x42], c.ram[0x43] = max(c.ram[0x42], 3), max(c.ram[0x43], 3)

    def fire_until_score(self, c, pilot, frames=1500):
        row = 0x117 if pilot == 0 else 0x129
        before = bytes(c.ram[row:row + 6])
        for i in range(frames):
            btn = B if i % 4 < 2 else 0
            c.pads = [btn, 0] if pilot == 0 else [0, btn]
            c.run_frame()
            if bytes(c.ram[row:row + 6]) != before:
                c.pads = [0, 0]
                return
        self.fail('no points')

    def test_overdrive_jingle_once(self):
        """The triangle (unused by the game) plays the 7-note arpeggio once, in
        the frames right after W4 starts; never before, not again while W4 lasts."""
        c = self.game()
        c.ram[WLEVEL] = 2
        c.ram[NODEATH_LO], c.ram[NODEATH_HI] = 799 & 0xFF, 799 >> 8
        start = c.frame
        self.fire_until_score(c, 0)
        self.assertEqual(c.ram[WLEVEL], 3)
        on = c.frame
        for _ in range(60):
            c.run_frame()
        tri = [(f, v) for f, r, v, pc in c.apu if r == 0x400A]
        self.assertEqual([v for f, v in tri], ARPEGGIO)
        self.assertTrue(all(on - 1 <= f <= on + 30 for f, v in tri), (on, tri))
        self.assertTrue(all(f >= start for f, v in tri))
        for i in range(1200):                            # more kills during W4: no second jingle
            self.keep_alive(c)
            c.pads = [B if i % 4 < 2 else 0, 0]
            c.run_frame()
        self.assertEqual(len([1 for f, r, v, pc in c.apu if r == 0x400A]), 7)
        self.assertEqual({hex(pc) for f, r, v, pc in c.apu if r in (0x4008, 0x400A, 0x400B) and pc < 0x8000}, set())

    def test_overdrive_shot_sound(self):
        """A W4 shot writes the laser zap to pulse 2, a W1-W3 shot the
        original FEA8 shot (pulse 2 + noise); one sound per new press; P1 and
        P2 firing in the same frame write the same zap (no other conflict);
        no new code writes pulse 1 (tunes / siren)."""
        c = self.game()
        for level, want in ((0, SHOT), (2, SHOT), (3, ZAP)):
            c.ram[WLEVEL], c.ram[WLEVEL + 1] = level, level
            c.ram[self.sym['W4_SEC']], c.ram[self.sym['W4_SEC'] + 1] = (30, 30) if level == 3 else (0, 0)
            for k in range(8):
                c.ram[0x16 + k] = 0
            c.apu.clear()
            fired = []
            for i in range(24):                          # 3 presses of 4 frames
                self.keep_alive(c)
                if i % 8 == 0:
                    for k in range(8):                   # a free slot for every press
                        c.ram[0x16 + k] = 0
                c.pads = [B if i % 8 < 4 else 0, 0]
                was = [c.ram[0x16 + k] for k in range(4)]
                c.run_frame()
                if any(c.ram[0x16 + k] > was[k] for k in range(4)):
                    fired.append(c.frame - 1)            # the frame the shot was fired in
            c.pads = [0, 0]
            self.assertEqual(len(fired), 3, 'one shot per press')
            sound = lambda pc: 0x8000 <= pc < 0xE000 or 0xFEA8 <= pc < 0xFED4    # SfxZap / FEA8
            for f0 in fired:
                got = [v for f, r, v, pc in c.apu if f == f0 and 0x4004 <= r <= 0x4007 and sound(pc)]
                self.assertEqual(got, want, f'W{level + 1} shot sound in frame {f0}')
                noise = [v for f, r, v, pc in c.apu if f == f0 and r == 0x400C and sound(pc)]
                self.assertEqual(bool(noise), level < 3, 'FEA8 has a noise part, the zap none')
            self.assertEqual(len({f for f, r, v, pc in c.apu if r == 0x4007 and sound(pc)}), 3)
        c.ram[WLEVEL], c.ram[WLEVEL + 1] = 3, 3          # both pilots, same frame
        for k in range(8):
            c.ram[0x16 + k] = 0
        c.apu.clear()
        for i in range(30):
            self.keep_alive(c)
            c.pads = [B if i % 8 < 4 else 0, B if i % 8 < 4 else 0]
            c.run_frame()
        c.pads = [0, 0]
        by_frame = {}
        for f, r, v, pc in c.apu:
            if 0x4004 <= r <= 0x4007 and pc >= 0x8000:
                by_frame.setdefault(f, []).append(v)
        both = [vs for vs in by_frame.values() if len(vs) == 8]
        self.assertTrue(both, 'a frame with both pilots firing')
        self.assertTrue(all(vs == ZAP + ZAP for vs in both))
        self.assertEqual([1 for f, r, v, pc in c.apu if r <= 0x4003 and 0x8000 <= pc < 0xE000], [])

    def test_tunes_unchanged(self):
        """The music (pulse 1: tunes and siren) in the first 6 s of a 1P game is
        written exactly as by the original (same input): RAM holding the tunes
        ($014E-$01FF) is not disturbed."""
        streams = []
        for rom in (self.orig, self.rom):
            c = CPU(rom)
            c.log = False
            c.apu_log = True
            start_game(c, two=False)
            for _ in range(360):
                c.run_frame()
            streams.append([(f, r, v) for f, r, v, pc in c.apu if r <= 0x4003])
        self.assertGreater(len(streams[0]), 200)
        self.assertEqual(streams[1], streams[0])

    def test_tune_ram_intact_in_play(self):
        """$014E-$01FF (tune pointers and three tunes copied from CHR) keep
        their reset contents through a co-op game with overdrive."""
        c = CPU(self.rom)
        c.log = False
        for _ in range(150):
            c.run_frame()
        ref = bytes(c.ram[0x150:0x200])                  # $014E/$014F: slot-0 pointer, rewritten by FD8E
        start_game(c, two=True)
        c.ram[WLEVEL] = 2
        c.ram[NODEATH_LO], c.ram[NODEATH_HI] = 799 & 0xFF, 799 >> 8
        for i in range(3000):
            self.keep_alive(c)
            c.pads = [B if i % 4 < 2 else 0, B if (i + 1) % 4 < 2 else 0]
            c.run_frame()
        self.assertEqual(bytes(c.ram[0x150:0x200]), ref)


if __name__ == '__main__':
    unittest.main()
