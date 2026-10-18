#!/usr/bin/env python3
"""Galaxian Coop tests.

    .venv/bin/python games/galaxian-coop/tests/test_coop.py [-v]

Static tests need only the original ROM (games/galaxian-coop/rom/ or $GALAXIAN_ROM).
Emulator tests need `pip install cynes numpy` and are skipped otherwise.
They drive the game through cynes and read CPU RAM; they do not replace a
play test on Mesen / hardware (see docs/TESTING.md).
"""
import hashlib
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parents[1]
sys.path[:0] = [str(REPO / 'tools'), str(GAME / 'src')]
import build  # noqa: E402
from nestest import NES, A, B, LEFT, RIGHT, SELECT, START, ines_compatible, pads, ram  # noqa: E402

ORIG = Path(os.environ.get('GALAXIAN_ROM', build.DEFAULT_ROM))

# RAM used by the mod (see docs/MEMORY_MAP.md)
COOP, P1_OUT, P2_STATE, P2_X, P2_BY = 0x05, 0x06, 0x08, 0x09, 0x0C
P2_OAM, P2_BUL_OAM = 0x02A0, 0x02B0
STATE, SUBSTATE, SHIP_X, P1_DEAD, LIVES1, LIVES2 = 0xFF, 0xFE, 0xE4, 0x4F, 0x42, 0x43


def score(nes, base):
    digits = ram(nes, base, 6)
    return int(''.join(str(d & 0x0F) for d in digits))


def p2_visible(nes):
    return any(nes[P2_OAM + k] < 0xEF for k in (0, 4, 8, 12))


@unittest.skipUnless(ORIG.exists(), f'original ROM not found: {ORIG}')
class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.rom_path = Path(cls.tmp.name) / 'coop.nes'
        cls.rom = build.build(ORIG, cls.rom_path)
        cls.orig = ORIG.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_reproducible(self):
        again = build.build(ORIG, Path(self.tmp.name) / 'again.nes')
        self.assertEqual(hashlib.sha256(again).digest(), hashlib.sha256(self.rom).digest())

    def test_original_untouched(self):
        self.assertEqual(hashlib.sha256(ORIG.read_bytes()).hexdigest(), build.ORIG_SHA256)

    def test_header(self):
        h = self.rom[:16]
        self.assertEqual(h[:4], b'NES\x1a')
        self.assertEqual(h[7] & 0x0C, 0x08, 'NES 2.0')
        self.assertEqual(h[4], 2, '32 KiB PRG')
        self.assertEqual(h[5], 1, '8 KiB CHR')
        self.assertEqual((h[6] >> 4) | (h[7] & 0xF0) | ((h[8] & 0x0F) << 8), 0, 'mapper 0')
        self.assertEqual(h[9], 0)
        self.assertEqual(len(self.rom), 16 + 0x8000 + 0x2000)

    def test_vectors(self):
        prg = self.rom[16:16 + 0x8000]
        nmi, reset, irq = (int.from_bytes(prg[0x7FFA + i:0x7FFC + i], 'little') for i in (0, 2, 4))
        self.assertEqual((nmi, reset, irq), (0xE20C, 0xE020, 0xE020))

    def test_original_code_only_changed_at_patches(self):
        prg = self.rom[16 + 0x6000:16 + 0x8000]
        orig = self.orig[16:16 + 0x2000]
        patched = set()
        for seg in build.assemble():
            if seg.org >= 0xE000:
                patched |= set(range(seg.org - 0xE000, seg.org - 0xE000 + len(seg.data)))
        diff = {i for i in range(0x2000) if prg[i] != orig[i]}
        self.assertTrue(diff <= patched, f'unexpected changes at {sorted(hex(0xE000 + i) for i in diff - patched)}')

    def test_stage1_hook_removed(self):
        # $E57A keeps the original controller selection; $07F0 is game RAM.
        self.assertEqual(self.rom[16 + 0x6000 + 0x57A:][:6], bytes.fromhex('0A AA B5 EF 85 4C'))

    def test_chr(self):
        chr_new, chr_old = self.rom[16 + 0x8000:], self.orig[16 + 0x2000:]
        diff = [i for i in range(0x2000) if chr_new[i] != chr_old[i]]
        allowed = set(build.LOGO_CELLS) | {t * 16 + k for t in build.P2_TILES for k in range(16)}
        self.assertTrue(set(diff) <= allowed)
        for off in build.LOGO_CELLS:
            self.assertEqual(chr_new[off], 0x10)


@unittest.skipUnless(ORIG.exists() and NES is not None, 'needs original ROM and cynes')
class TestEmulator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.rom = str(Path(cls.tmp.name) / 'coop.nes')
        build.build(ORIG, cls.rom)
        cls.orig = ines_compatible(ORIG)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def start(self, rom, two):
        n = NES(rom)
        n.step(150)
        if two:
            for _ in range(40):
                if n[0x31] & 1:
                    break
                n.controller = pads(SELECT); n.step(6); n.controller = 0; n.step(6)
        for _ in range(60):
            if n[STATE] == 3:
                break
            n.controller = pads(START); n.step(6); n.controller = 0; n.step(6)
        for _ in range(1200):
            if n[STATE] == 3 and n[SUBSTATE] == 8 and n[P1_DEAD] == 0:
                return n
            n.step()
        self.fail('game did not start')

    def test_chr_change_invisible_on_title(self):
        # Original program + only the new CHR (logo cells moved to tile $10,
        # P2 tiles added): title, menu and demo must be pixel-identical.
        data = Path(self.orig).read_bytes()
        chr_only = Path(self.tmp.name) / 'chr_only.nes'
        chr_only.write_bytes(data[:16 + 0x4000] + build.patch_chr(data[16 + 0x4000:]))
        a, b = NES(self.orig), NES(str(chr_only))
        for _ in range(40):
            fa, fb = a.step(30), b.step(30)
            self.assertTrue((fa == fb).all(), 'CHR change is visible')

    def test_one_player_has_no_p2(self):
        n = self.start(self.rom, two=False)
        self.assertEqual(n[COOP], 0)
        rnd = random.Random(1)
        for _ in range(1500):
            n.controller = pads(rnd.choice([0, A | RIGHT, A | LEFT]), rnd.choice([0, A, LEFT, RIGHT]))
            n.step()
            self.assertFalse(p2_visible(n))
            self.assertGreaterEqual(n[P2_BUL_OAM], 0xEF)

    def test_independent_movement(self):
        n = self.start(self.rom, two=True)
        n.step(2)  # P2 enters play on the first frame of normal play
        self.assertEqual((n[COOP], n[P2_STATE]), (1, 1))
        n.controller = pads(RIGHT, LEFT); n.step(40)
        self.assertEqual((n[SHIP_X], n[P2_X]), (40, 256 - 40))
        n.controller = pads(0, RIGHT); n.step(20)
        self.assertEqual((n[SHIP_X], n[P2_X]), (40, 256 - 20))
        n.controller = 0; n.step()
        self.assertTrue(p2_visible(n))
        self.assertEqual(n[P2_OAM + 3], (n[P2_X] + 0x79) & 0xFF)

    def test_p2_shots_score_for_p2(self):
        n = self.start(self.rom, two=True)
        n.controller = pads(0, LEFT); n.step(30)
        for i in range(400):
            n.controller = pads(0, B if i % 8 < 4 else 0)
            n.step()
        self.assertGreater(score(n, 0x129), 0, 'P2 score')
        self.assertEqual(score(n, 0x117), 0, 'P1 score must not change')

    def test_p2_death_respawn_and_lives(self):
        n = self.start(self.rom, two=True)
        n.controller = pads(0, LEFT); n.step(70); n.controller = 0
        lives1, lives2 = n[LIVES1], n[LIVES2]
        for _ in range(6000):
            n.step()
            if n[P2_STATE] == 2:
                break
        self.assertEqual(n[P2_STATE], 2, 'P2 never hit')
        for _ in range(600):
            n.step()
            if n[P2_STATE] == 1:
                break
        self.assertEqual(n[P2_STATE], 1, 'P2 did not respawn')
        self.assertEqual(n[LIVES2], lives2 - 1)
        self.assertLessEqual(n[LIVES1], lives1)  # P1 may have died on its own

    def test_game_over_only_when_both_out(self):
        n = self.start(self.rom, two=True)
        n.controller = pads(0, LEFT); n.step(70)
        saw_p1_out_playing = False
        for i in range(60 * 60 * 6):
            n.controller = pads(0, B if i % 8 < 4 else 0)
            n.step()
            if n[STATE] != 3:
                break
            if n[P1_OUT] and n[P2_STATE] in (1, 2, 3):
                saw_p1_out_playing = True
        self.assertEqual(n[STATE], 4, 'game over not reached')
        self.assertEqual((n[P2_STATE], n[LIVES2]), (0, 0))
        self.assertEqual(n[P1_OUT], 1)
        self.assertTrue(saw_p1_out_playing, 'P2 should have kept playing after P1 ran out')

    def scatter_trace_depends_on_pad2(self, rom):
        """Game-over animation (FB83/E400) moves sprite 0 by $07F0 each frame.
        Run it twice from one save state, P2 idle vs P2 holding every button."""
        n = self.start(rom, two=False)
        for _ in range(60 * 240):
            n.step()
            if n[STATE] == 4 and n[LIVES1] > 0:
                break
        self.assertEqual(n[STATE], 4)
        state = n.save()
        traces = []
        for pad2 in (0, 0xFF):
            n.load(state)
            ys = []
            for _ in range(40):
                n.controller = pads(0, pad2)
                n.step()
                ys.append(tuple(n[0x200 + 4 * k] for k in range(8)))
            traces.append(ys)
        return traces[0] != traces[1]

    def test_game_over_scatter_ignores_pad2(self):
        # Regression for the stage 1 hook, which copied $F1 into $07F0.
        self.assertFalse(self.scatter_trace_depends_on_pad2(self.rom))

    def test_stress_no_crash_or_overrun(self):
        rnd = random.Random(7)
        n = self.start(self.rom, two=True)
        prev = n[0x3A] | n[0x3B] << 8
        worst = 1 << 16
        c = 0
        for i in range(60 * 60 * 3):
            if i % 6 == 0:
                c = pads(rnd.choice([0, A, A | LEFT, A | RIGHT, LEFT, RIGHT]),
                         rnd.choice([0, A, A | LEFT, A | RIGHT, LEFT, RIGHT]))
            n.controller = c
            n.step()
            cur = n[0x3A] | n[0x3B] << 8
            if n[STATE] == 3 and n[SUBSTATE] == 8:
                worst = min(worst, (cur - prev) & 0xFFFF)
            prev = cur
        self.assertFalse(n.has_crashed)
        self.assertGreater(worst, 100, 'NMI handler close to overrunning the frame')


if __name__ == '__main__':
    unittest.main()
