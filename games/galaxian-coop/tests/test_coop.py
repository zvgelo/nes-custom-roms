#!/usr/bin/env python3
"""Galaxian Coop tests.

    .venv/bin/python games/galaxian-coop/tests/test_coop.py [-v]

Static tests need only the original ROM (games/galaxian-coop/private/ or $GALAXIAN_ROM).
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


def glyphs(rom_bytes, table=1, tiles=None):
    """Pixel masks of BG tiles (table 1 = $1000, in-game BG; table 0 = title BG)."""
    import numpy as np
    chr_data = rom_bytes[-0x2000:]
    out = {}
    for t in tiles or list(range(10)) + [0x10, 0x28, 0x6E, 0x6F]:
        b = chr_data[0x1000 * table + t * 16:]
        out[t] = np.array([[((b[y] | b[y + 8]) >> (7 - x)) & 1 for x in range(8)] for y in range(8)], bool)
    return out


def read_tile(frame, glyph_masks, col, row):
    """BG tile shown at nametable (col, row) in play (Y scroll puts row r at y = 8r+1)."""
    block = frame[8 * row + 1:8 * row + 9, 8 * col:8 * col + 8].any(2)
    for t, m in glyph_masks.items():
        if (m == block).all():
            return t
    return None  # e.g. a star sprite crossing the cell


def lives_hud(frame, g):
    """(P1, P2) lives shown as icon + X + digit, or None if a cell is unreadable."""
    p1 = [read_tile(frame, g, c, 4) for c in (1, 2, 3)] + [read_tile(frame, g, 1, 3)]
    p2 = [read_tile(frame, g, c, 4) for c in (28, 29, 30)] + [read_tile(frame, g, 28, 3)]
    ok = all(v is not None for v in p1 + p2)
    if not ok or p1[:2] + p2[:2] != [0x6F, 0x28] * 2 or (p1[3], p2[3]) != (0x6E, 0x6E):
        return None
    return p1[2], p2[2]


def wait_hud(n, g, frames=10):
    for _ in range(frames):
        hud = lives_hud(n.step(), g)
        if hud is not None:
            return hud
    return None


def wait_hud_p1(n, g, frames=10):
    for _ in range(frames):
        f = n.step()
        cells = [read_tile(f, g, c, 4) for c in (1, 2, 3)]
        if cells[:2] == [0x6F, 0x28] and cells[2] is not None:
            return cells[2]
    return None


def expected_lives(n):
    """Total ships left (in play + reserve), from RAM, as the HUD defines it."""
    if n[P1_OUT]:
        p1 = 0
    elif n[P1_DEAD] == 0 or n[0x13]:      # alive, or next ship already granted (P1_GRANTED)
        p1 = n[LIVES1] + 1
    else:
        p1 = n[LIVES1]
    p2 = n[LIVES2] + (1 if n[P2_STATE] == 1 else 0)
    return p1, p2


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

    def test_bps_patch(self):
        # the patch rebuilds the ROM exactly and carries no original game data
        from bps import apply_bps, create_bps
        patch = create_bps(self.orig, self.rom)
        self.assertEqual(apply_bps(self.orig, patch), self.rom)
        chunks = [self.orig[i:i + 32] for i in range(16, len(self.orig) - 32, 16)]
        leaked = [c for c in chunks if len(set(c)) > 4 and c in patch]
        self.assertEqual(leaked, [], 'original data found in the BPS patch')

    def test_chr(self):
        chr_new, chr_old = self.rom[16 + 0x8000:], self.orig[16 + 0x2000:]
        diff = [i for i in range(0x2000) if chr_new[i] != chr_old[i]]
        allowed = set(build.LOGO_CELLS) | {t * 16 + k for t in build.P2_TILES + (build.LASER_TILE,) for k in range(16)}
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
        # cynes' power-on phase can differ between instances; start b from a's
        # state so both run in lockstep and only the CHR data can differ
        a, b = NES(self.orig), NES(str(chr_only))
        b.load(a.save())  # at power-on: the reset code copies data from CHR into RAM
        for i in range(40):
            fa, fb = a.step(30), b.step(30)
            diff = (fa != fb).any(2)
            ys, xs = diff.nonzero()
            self.assertFalse(diff.any(), f'CHR change is visible: frame {30 * (i + 1)}, {int(diff.sum())} px, '
                             f'rows {ys.min() if len(ys) else 0}-{ys.max() if len(ys) else 0}, '
                             f'cols {xs.min() if len(xs) else 0}-{xs.max() if len(xs) else 0}, '
                             f'RAM diff {[hex(x) for x in range(0x800) if a[x] != b[x]][:8]}')

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
        x1, x2 = n[SHIP_X], n[P2_X]                      # spawn: P1 left, P2 right
        n.controller = pads(RIGHT, LEFT); n.step(40)
        self.assertEqual((n[SHIP_X], n[P2_X]), ((x1 + 40) & 0xFF, (x2 - 40) & 0xFF))
        n.controller = pads(0, RIGHT); n.step(20)
        self.assertEqual((n[SHIP_X], n[P2_X]), ((x1 + 40) & 0xFF, (x2 - 20) & 0xFF))
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
        n.step(3)
        n[LIVES2] = 5           # P2 outlives P1, so the "P1 out, P2 plays on" phase happens
        n.controller = pads(0, LEFT); n.step(70)
        saw_one_out_other_playing = False
        for i in range(60 * 60 * 6):
            n.controller = pads(0, B if i % 8 < 4 else 0)
            n.step()
            if n[STATE] != 3:
                break
            last_lives1 = n[LIVES1]                     # FB83 reuses $42 after game over
            if n[P1_OUT] and n[P2_STATE] in (1, 2, 3):
                saw_one_out_other_playing = True
            if n[P2_STATE] == 0 and not n[P1_OUT] and n[SUBSTATE] == 8 and n[P1_DEAD] == 0:
                saw_one_out_other_playing = True
        self.assertEqual(n[STATE], 4, 'game over not reached')
        self.assertEqual((n[P2_STATE], n[LIVES2]), (0, 0))
        self.assertEqual(last_lives1, 0)
        self.assertTrue(saw_one_out_other_playing, 'one pilot should keep playing after the other is out')

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

    def test_top_line_blank(self):
        # Regression: Y scroll $FF showed attribute bytes as tiles on line 0
        # (white dashes, also in the original ROM). Fixed by ScrollFix.
        for two in (False, True):
            n = self.start(self.rom, two=two)
            rnd = random.Random(11)
            for _ in range(300):
                n.controller = pads(rnd.choice([0, A | LEFT, A | RIGHT]), rnd.choice([0, A | LEFT, A | RIGHT]))
                frame = n.step()
                self.assertFalse(frame[0].any(), 'pixels on screen line 0 during play')
        # title / attract: blank whenever the scroll is settled ($EF title, $FF play);
        # during the title scroll-in line 0 shows the scrolling picture, as in the original
        b = NES(self.rom)
        for _ in range(40):
            fb = b.step(30)
            if b[0xF7] in (0xEF, 0xFF):
                self.assertFalse(fb[0].any(), f'pixels on line 0 with Y scroll ${b[0xF7]:02X}')

    def test_no_stray_zero_top_left(self):
        # Regression: F753 cleared OAM with tile $00, so free sprite slots (Y=0)
        # drew a "0" at the top-left on lines 1-8. Lines 0-8 hold no HUD.
        for two in (False, True):
            n = self.start(self.rom, two=two)
            rnd = random.Random(5)
            for _ in range(1500):
                n.controller = pads(rnd.choice([0, A | LEFT, A | RIGHT]), rnd.choice([0, A | LEFT, A | RIGHT]))
                frame = n.step()
                if n[STATE] != 3:
                    break
                self.assertFalse(frame[0:9].any(), 'pixels in screen lines 0-8 during play')
        n = self.start(self.orig, two=False)            # the original shows it
        self.assertTrue(n.step()[1:9, 0:8].any())

    def test_original_has_top_line_dashes(self):
        # Documents the cause: the unmodified game draws them, so the fix is ours.
        n = self.start(self.orig, two=False)
        self.assertEqual(n[0xF7], 0xFF)
        self.assertTrue(n.step()[0].any())

    def test_lives_hud_start_and_full_game(self):
        g = glyphs(Path(self.rom).read_bytes())
        n = self.start(self.rom, two=True)
        n.step(3)
        self.assertEqual(expected_lives(n), (3, 3))
        self.assertEqual(wait_hud(n, g), (3, 3))
        n.controller = pads(0, LEFT); n.step(70)
        shown, deaths1, deaths2, recent = [], 0, 0, []
        prev_dead, prev_p2 = n[P1_DEAD], n[P2_STATE]
        for i in range(60 * 60 * 6):
            n.controller = pads(0, B if i % 8 < 4 else 0)
            frame = n.step()
            if n[STATE] != 3:
                break
            if prev_dead == 0 and n[P1_DEAD] not in (0, 0x22):
                deaths1 += 1
            if prev_p2 == 1 and n[P2_STATE] == 2:
                deaths2 += 1
            prev_dead, prev_p2 = n[P1_DEAD], n[P2_STATE]
            recent = (recent + [expected_lives(n)])[-8:]
            if i % 5 == 0 and len(set(recent)) == 1:  # HUD: refresh every 2nd frame + 1-2 frames streaming
                hud = lives_hud(frame, g)
                if hud is not None:
                    self.assertEqual(hud, expected_lives(n), f'frame {i}')
                    if not shown or shown[-1] != hud:
                        shown.append(hud)
        self.assertEqual(n[STATE], 4)
        self.assertEqual((deaths1, deaths2), (3, 3), 'each player loses exactly 3 ships')
        self.assertEqual(shown[0], (3, 3))
        self.assertEqual(shown[-1], (0, 0))
        for a, b in zip(shown, shown[1:]):  # ships are only lost here, never gained
            self.assertTrue(b[0] <= a[0] and b[1] <= a[1] and b != a, f'{a} -> {b}')

    def test_one_player_lives_hud(self):
        # 1P uses the same "icon X<lives>" display as co-op; no P2 data, stage flag kept
        g = glyphs(Path(self.rom).read_bytes(), tiles=list(range(10)) + [0x10, 0x28, 0x6C, 0x6D, 0x6E, 0x6F])
        n = self.start(self.rom, two=False)
        n.step(5)
        frame = n.step()
        self.assertEqual(expected_lives(n)[0], 3)
        self.assertEqual([read_tile(frame, g, c, 4) for c in (1, 2, 3)], [0x6F, 0x28, 3])
        self.assertEqual([read_tile(frame, g, c, 4) for c in (21, 22, 23)], [0x10, 0x10, 0x10])
        self.assertEqual([read_tile(frame, g, c, 4) for c in (28, 29, 30)], [0x10, 0x10, 0x10])
        self.assertEqual(read_tile(frame, g, 25, 4), 0x6D, 'stage flag still shown')
        for _ in range(60 * 60 * 3):                    # after a death the counter follows
            n.step()
            if n[P1_DEAD]:
                break
        n.step(10)
        self.assertEqual(expected_lives(n)[0], 2)
        self.assertEqual(wait_hud_p1(n, g), 2)

    def p1_out_p2_playing(self, p2_reserve):
        """Co-op game where P1 has just been eliminated and P2 is in play."""
        n = self.start(self.rom, two=True)
        n.step(3)
        n[LIVES1] = 0                       # P1's ship in play is its last
        n.controller = pads(0, LEFT); n.step(70)
        for i in range(60 * 60 * 3):
            n.controller = pads(0, B if i % 8 < 4 else 0)
            n.step()
            if n[P1_OUT] and n[SUBSTATE] == 8 and n[P2_STATE] == 1 and n[P1_DEAD] == 0:
                n.controller = 0
                n[LIVES2] = p2_reserve
                n.step(5)
                return n
        self.fail('P1 was never eliminated while P2 was in play')

    def p2_out_p1_playing(self, p1_reserve):
        n = self.start(self.rom, two=True)
        n.step(3)
        n[LIVES2] = 0
        n.controller = pads(LEFT); n.step(80); n.controller = 0
        for _ in range(60 * 60 * 3):
            n.step()
            if n[P2_STATE] == 0 and n[SUBSTATE] == 8 and n[P1_DEAD] == 0 and not n[P1_OUT]:
                n[LIVES1] = p1_reserve
                n.step(5)
                return n
        self.fail('P2 was never eliminated while P1 was in play')

    def press_select(self, n, p1=False, p2=False, frames=1):
        for k in range(8):                              # no shot in flight may score meanwhile
            n[0x16 + k] = 0
        n.controller = pads(SELECT if p1 else 0, SELECT if p2 else 0)
        n.step(frames)
        n.controller = 0
        n.step(8)

    def test_share_p2_revives_p1(self):
        g = glyphs(Path(self.rom).read_bytes())
        n = self.p1_out_p2_playing(p2_reserve=2)
        self.assertEqual(expected_lives(n), (0, 3))
        score2 = score(n, 0x129)
        self.press_select(n, p2=True)
        self.assertEqual(expected_lives(n), (1, 2))
        self.assertEqual(n[P1_OUT], 0)
        n.step(4)
        self.assertEqual(wait_hud(n, g), (1, 2))
        x = n[SHIP_X]
        n.controller = pads(RIGHT); n.step(30); n.controller = 0; n.step()
        self.assertEqual(n[SHIP_X], (x + 30) & 0xFF, 'revived P1 moves')
        frame = n.step()
        x0 = 120 + ((n[SHIP_X] + 128) & 0xFF) - 128
        self.assertTrue(frame[209:225, x0:x0 + 16].any(), 'P1 ship drawn again')

    def test_share_p1_revives_p2(self):
        g = glyphs(Path(self.rom).read_bytes())
        n = self.p2_out_p1_playing(p1_reserve=2)
        self.assertEqual(expected_lives(n), (3, 0))
        self.press_select(n, p1=True)
        self.assertEqual(expected_lives(n), (2, 1))
        self.assertEqual(n[P2_STATE], 1)
        n.step(4)
        self.assertEqual(wait_hud(n, g), (2, 1))
        self.assertTrue(p2_visible(n))

    def test_share_blocked_cases(self):
        n = self.p1_out_p2_playing(p2_reserve=0)        # donor has only 1 life
        self.press_select(n, p2=True)
        self.assertEqual(expected_lives(n), (0, 1))
        self.press_select(n, p1=True)                   # eliminated player can't give
        self.assertEqual(expected_lives(n), (0, 1))

    def test_share_hold_and_both_pads(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        state = n.save()
        self.press_select(n, p2=True, frames=90)        # held: one transfer
        self.assertEqual(expected_lives(n), (1, 2))
        n.load(state)
        self.press_select(n, p1=True, p2=True)          # both pads at once: one transfer
        self.assertEqual(expected_lives(n), (1, 2))

    def test_share_select_held_before_elimination(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        n[LIVES1] = 0
        n.controller = pads(0, LEFT); n.step(70)
        for i in range(60 * 60 * 3):                    # P2 holds SELECT the whole time
            n.controller = pads(0, SELECT | (B if i % 8 < 4 else 0))
            n.step()
            if n[P1_OUT] and n[SUBSTATE] == 8 and n[P2_STATE] == 1:
                break
        self.assertEqual(n[P1_OUT], 1)
        n[LIVES2] = 2
        n.controller = pads(0, SELECT); n.step(40)
        self.assertEqual(expected_lives(n), (0, 3), 'no new press, no transfer')
        n.controller = 0; n.step(2)
        self.press_select(n, p2=True)
        self.assertEqual(expected_lives(n), (1, 2))

    def test_share_needs_new_press_after_pause(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        n.controller = pads(START); n.step(3); n.controller = 0; n.step(5)
        self.assertNotEqual(n[0x4E], 0, 'paused')
        n.controller = pads(0, SELECT); n.step(10)
        n.controller = pads(START, SELECT); n.step(3)
        n.controller = pads(0, SELECT); n.step(20)
        self.assertEqual(n[0x4E], 0, 'unpaused')
        self.assertEqual(expected_lives(n), (0, 3), 'press during pause ignored')
        n.controller = 0; n.step(2)
        self.press_select(n, p2=True)
        self.assertEqual(expected_lives(n), (1, 2))

    def test_share_refused_while_partner_has_lives(self):
        n = self.start(self.rom, two=True)
        n.step(5)
        for p1_res, p2_res in ((0, 4), (1, 4), (4, 0), (4, 1)):   # recipient X1 / X2
            n[LIVES1], n[LIVES2] = p1_res, p2_res
            n.step(2)
            before = expected_lives(n)
            self.press_select(n, p1=True)
            self.press_select(n, p2=True)
            self.assertEqual(expected_lives(n), before, f'reserves {p1_res}/{p2_res}')

    def test_share_with_both_in_play_does_nothing(self):
        n = self.start(self.rom, two=True)
        n.step(5)
        before = expected_lives(n)
        for _ in range(3):
            self.press_select(n, p1=True)
            self.press_select(n, p2=True)
        self.assertEqual(expected_lives(n), before)

    def test_select_in_one_player_game(self):
        n = self.start(self.rom, two=False)
        lives = n[LIVES1]
        for _ in range(3):
            self.press_select(n, p1=True)
            self.press_select(n, p2=True)
        self.assertEqual((n[LIVES1], n[COOP], n[STATE]), (lives, 0, 3))
        self.assertFalse(p2_visible(n))

    def test_revived_player_can_be_eliminated_again(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        self.press_select(n, p2=True)
        self.assertEqual(n[P1_OUT], 0)
        n[LIVES2] = 6           # P2 stays in the game, so P1 can be eliminated again
        n.controller = pads(0, LEFT); n.step(60); n.controller = 0
        for _ in range(60 * 60 * 3):
            n.step()
            if n[P1_OUT] or n[STATE] != 3:
                break
        self.assertEqual(n[P1_OUT], 1, 'revived P1 was hit and is out again')
        self.assertEqual(expected_lives(n)[0], 0)

    # ------------------------------------------------------------ title screen
    TITLE_TEXT = {16: (12, '1 PILOT'), 18: (12, '2 PILOTS CO-OP'), 28: (6, 'HACK BY ZVGELO ©2026')}

    def title_text_ok(self, frames, g):
        """Each text cell must match its tile in at least one frame (stars drift over text)."""
        def tile(ch):
            if ch.isdigit():
                return int(ch)
            return {' ': 0x10, '©': 0x2D, '-': 0x2B}.get(ch, 0x11 + ord(ch) - 65)
        for row, (col, text) in self.TITLE_TEXT.items():
            for i, ch in enumerate(text):
                want = {16: 0x0A, 18: 0x0B}[row] if (row in (16, 18) and i == 0) else tile(ch)
                if not any((f[8 * row + 1:8 * row + 9, 8 * (col + i):8 * (col + i) + 8].any(2) == g[want]).all()
                           for f in frames):
                    return f'row {row} col {col + i} {ch!r}'
        return None

    def wait_title(self, n, frames=900):
        for _ in range(frames):
            frame = n.step()
            if n[STATE] == 1 and n[SUBSTATE] == 2 and n[0xF7] == 0xEF:
                n.step(2)  # the frame just drawn still used the previous scroll value
                return [n.step(7).copy() for _ in range(6)]
        self.fail('title screen not reached')

    def test_title_text(self):
        data = Path(self.rom).read_bytes()
        g = glyphs(data, table=0, tiles=list(range(0x30)))
        n = NES(self.rom)
        frames = self.wait_title(n)
        self.assertIsNone(self.title_text_ok(frames, g))
        # original rows (namcot, NAMCO lines): BG cells identical in some frame pair
        fo = self.wait_title(NES(self.orig))
        for row in (21, 24, 26):
            for col in range(3, 29):
                ys, xs = slice(8 * row + 1, 8 * row + 9), slice(8 * col, 8 * col + 8)
                self.assertTrue(any((a[ys, xs] == b[ys, xs]).all() for a in fo for b in frames),
                                f'row {row} col {col} changed')

    def test_title_after_game_over(self):
        data = Path(self.rom).read_bytes()
        g = glyphs(data, table=0, tiles=list(range(0x30)))
        n = self.start(self.rom, two=False)
        for _ in range(60 * 60 * 5):
            n.step()
            if n[STATE] == 1:
                break
        self.assertEqual(n[STATE], 1, 'back on the title after game over')
        self.assertIsNone(self.title_text_ok(self.wait_title(n), g))
        n2 = self.start(self.rom, two=True)             # menu still starts co-op
        self.assertEqual(n2[COOP], 1)

    def test_title_badge(self):
        n = NES(self.rom)
        self.wait_title(n)
        g1 = glyphs(Path(self.rom).read_bytes(), table=1, tiles=[0x13, 0x1F, 0x2B, 0x20])
        attrs = set()
        for _ in range(70):
            frame = n.step()
            oam = [(n[P2_OAM + 4 * k], n[P2_OAM + 4 * k + 1], n[P2_OAM + 4 * k + 2], n[P2_OAM + 4 * k + 3])
                   for k in range(5)]
            self.assertEqual([o[1] for o in oam], [0x13, 0x1F, 0x2B, 0x1F, 0x20], 'C O - O P')
            self.assertEqual([o[0] for o in oam], [99, 97, 95, 93, 91], 'diagonal')
            attrs.add(oam[0][2])
        self.assertEqual(attrs, {0, 1}, 'red with a white glint')
        y, x = 100, 168                                  # "C" on screen (sprite table 1)
        cells = frame[y:y + 8, x:x + 8][g1[0x13]]
        self.assertEqual(len({tuple(int(v) for v in c) for c in cells}), 1, 'glyph drawn in one sprite colour')
        n2 = self.start(self.rom, two=True)              # badge gone in the game
        self.assertTrue(all(n2[P2_OAM + 4 * k] >= 0xEF or n2[P2_STATE] == 1 for k in range(4)))

    # ------------------------------------------------------------ weapons
    WLEVEL0, BUL_Y0, BOOST_LO0, BOOST_HI0, NODEATH_LO0, NODEATH_HI0 = 0x45, 0x16, 0x7A, 0x7C, 0x47, 0x49

    def clear_stage(self, n, frames=900):
        """Empty the formation and stop the divers; the original end-of-wave
        sequence (E937 -> FA52 -> FC1A) then runs and calls StageCleared."""
        stage = n[0x59]
        for k in range(10):
            n[0xC3 + k] = 0
        for k in range(8):
            n[0x738 + k] = 0
        for _ in range(frames):
            n.step()
            if n[0x59] != stage:
                n.step(5)
                return
        self.fail('stage did not end')

    def fire_burst(self, n, pilot, frames=120):
        most = 0
        base = 4 * pilot
        for i in range(frames):
            btn = B if (i // 2) % 2 == 0 else 0           # each press held 2 frames (E5A8 rule)
            n.controller = pads(btn, 0) if pilot == 0 else pads(0, btn)
            n.step()
            most = max(most, sum(1 for k in range(4) if n[self.BUL_Y0 + base + k]))
        n.controller = 0
        return most

    def bullet_speed(self, n, pilot):
        """Average px/frame of a freshly fired bullet over 12 frames, free of hits."""
        base = 4 * pilot
        for _ in range(20):
            for k in range(4):
                n[self.BUL_Y0 + base + k] = 0
            n.controller = 0
            n.step(2)
            for i in range(6):                           # hold B until it fires
                n.controller = pads(B, 0) if pilot == 0 else pads(0, B)
                n.step()
                if n[self.BUL_Y0 + base]:
                    break
            n.controller = 0
            y0 = n[self.BUL_Y0 + base]
            ys = [y0]
            for _ in range(12):
                n.step()
                ys.append(n[self.BUL_Y0 + base])
            if all(ys) and all(a > b for a, b in zip(ys, ys[1:])):
                return (ys[0] - ys[-1]) / 12
            n.step(60)
        self.fail('no clean bullet flight measured')

    def test_weapon_levels(self):
        for two in (False, True):
            n = self.start(self.rom, two=two)
            n.step(3)
            self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (0, 0), 'new game: W1')
            n.controller = pads(0, LEFT); n.step(40); n.controller = 0
            state = n.save()
            for level, shots, speed in ((0, 1, 4.0), (1, 2, 4.4), (2, 3, 4.8), (3, 4, 6.4)):
                n.load(state)
                n[self.WLEVEL0] = level
                n[LIVES1] = 5
                self.assertEqual(self.fire_burst(n, 0), shots, f'W{level + 1} shots')
                n.load(state)
                n[self.WLEVEL0] = level
                n[LIVES1] = 5
                v = self.bullet_speed(n, 0)
                self.assertAlmostEqual(v, speed, delta=0.12, msg=f'W{level + 1} speed {v}')
                n.load(state)                       # sprite: red laser only on W4
                n[self.WLEVEL0] = level
                n.controller = pads(B); n.step(3); n.controller = 0; n.step(2)
                tile, attr = n[0x281], n[0x282]
                self.assertEqual((tile, attr), (0x60, 1) if level == 3 else (0x30, 0))

    def test_boost_thresholds(self):
        n = self.start(self.rom, two=False)           # 1P: no free W2
        n.step(3)
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 0, '1P: clearing stage 1 gives nothing')
        for boost, want in ((199, 0), (200, 1)):          # 1999 / 2000 points
            st = n.save()
            n[self.BOOST_LO0], n[self.BOOST_HI0] = boost & 0xFF, boost >> 8
            n.step(120)
            self.assertEqual(n[self.WLEVEL0], 0, 'no boost without a cleared stage')
            self.clear_stage(n)
            self.assertEqual(n[self.WLEVEL0], want, f'{boost * 10} points')
            if want:
                self.assertEqual((n[self.BOOST_LO0], n[self.BOOST_HI0]), (0, 0), 'points restart')
            n.load(st)
        n[self.WLEVEL0] = 1
        for boost, want in ((499, 1), (500, 2)):          # +4999 / +5000 points
            st = n.save()
            n[self.BOOST_LO0], n[self.BOOST_HI0] = boost & 0xFF, boost >> 8
            self.clear_stage(n)
            self.assertEqual(n[self.WLEVEL0], want, f'W2 + {boost * 10} points')
            n.load(st)
        n[self.WLEVEL0] = 2                               # W3 -> W4 only by no-death points
        n[self.BOOST_LO0], n[self.BOOST_HI0] = 0xFF, 0x03
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 2, 'stage clears never give W4')

    def score_points(self, n, pilot, frames=1500):
        """Let pilot fire until its score changes."""
        row = 0x117 if pilot == 0 else 0x129
        before = score(n, row)
        for i in range(frames):
            btn = B if i % 4 < 2 else 0
            n.controller = pads(btn) if pilot == 0 else pads(0, btn)
            n.step()
            if score(n, row) != before:
                n.controller = 0
                return score(n, row) - before
        self.fail('no points scored')

    def test_w4_red_laser(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        n.controller = pads(0, LEFT); n.step(40); n.controller = 0
        st = n.save()
        # W3 with 7990 no-death points: +30..+800 crosses 8000 -> W4 at once
        n[self.WLEVEL0] = 2
        n[self.NODEATH_LO0], n[self.NODEATH_HI0] = 799 & 0xFF, 799 >> 8
        n[LIVES1] = 5
        self.score_points(n, 0)
        self.assertEqual(n[self.WLEVEL0], 3, 'W4 when 8000 no-death points are reached on W3')
        self.assertEqual(n[self.WLEVEL0 + 1], 0, 'P2 unaffected')
        # banner "P1 GREAT SHOT" / "W4 RED LASER", gone after ~2 s
        g = glyphs(Path(self.rom).read_bytes(), tiles=list(range(0x10, 0x2B)) + [0x0A, 0x0B, 0x0C])
        n.step(6)
        self.assertEqual(self.read_row(n, g, 1).strip(), 'P1 GREAT SHOT')
        self.assertEqual(self.read_row(n, g, 2).strip(), 'W4 RED LASER')
        n.step(130)
        self.assertEqual(self.read_row(n, g, 1).strip(), '')
        self.assertEqual(self.read_row(n, g, 2).strip(), '')
        # W2 with plenty of no-death points: no W4 before W3
        n.load(st)
        n[self.WLEVEL0] = 1
        n[self.NODEATH_LO0], n[self.NODEATH_HI0] = 0xFF, 0x03
        n[LIVES1] = 5
        self.score_points(n, 0)
        self.assertEqual(n[self.WLEVEL0], 1)
        n[self.BOOST_LO0], n[self.BOOST_HI0] = 500 & 0xFF, 500 >> 8
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 3, 'W3 granted, and W4 right away')
        # both pilots on W4: up to 8 bullets, 4 each
        n.load(st)
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        most = 0
        for i in range(150):
            btn = B if (i // 2) % 2 == 0 else 0
            n.controller = pads(btn, btn)
            n.step()
            most = max(most, sum(1 for k in range(8) if n[self.BUL_Y0 + k]))
        self.assertLessEqual(most, 8)
        self.assertGreaterEqual(most, 7)

    def test_death_resets_weapon(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 2
        n[self.BOOST_LO0], n[self.NODEATH_LO0] = 100, 120
        n[LIVES2] = 5
        n.controller = pads(0, LEFT); n.step(60); n.controller = 0
        sc = score(n, 0x117)
        for _ in range(60 * 60 * 3):
            n.step()
            n[self.WLEVEL0 + 1] = 2                 # keep P2 on W3 even if P2 dies
            if n[P1_DEAD]:
                break
        self.assertTrue(n[P1_DEAD])
        n.step(2)
        self.assertEqual((n[self.WLEVEL0], n[self.BOOST_LO0], n[self.NODEATH_LO0]), (0, 0, 0))
        self.assertGreaterEqual(score(n, 0x117), sc, 'score kept')

    def test_first_stage_boost_coop(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        self.clear_stage(n)
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (1, 1), 'W2 / W2 after stage 1')
        self.assertEqual((n[self.BOOST_LO0], n[self.BOOST_LO0 + 1]), (0, 0))
        n[self.WLEVEL0] = 0                              # as after a death
        for _ in range(60):
            n.step()
            if n[SUBSTATE] == 8:
                break
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 0, 'the free W2 is given once per game')

    def test_revive_comes_back_on_w1(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        n[self.WLEVEL0 + 1] = 2
        n[self.WLEVEL0] = 3                              # stale value must not survive
        p2_score = score(n, 0x129)
        self.press_select(n, p2=True)
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (0, 2))
        self.assertEqual(score(n, 0x129), p2_score + 200, '+200 for the donor')
        self.assertGreaterEqual(n[self.NODEATH_LO0 + 1] | n[self.NODEATH_HI0 + 1] << 8, 20, 'bonus counts')

    # ------------------------------------------------------------ extra lives
    def set_score(self, n, pilot, value):
        row = 0x117 if pilot == 0 else 0x129
        digits = f'{value:06d}'
        lead = True
        for i, d in enumerate(digits):
            if lead and d == '0' and i < 4:
                n[row + i] = 0x10
            else:
                lead = False
                n[row + i] = int(d)

    def test_extra_lives(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        n.controller = pads(0, LEFT); n.step(40); n.controller = 0
        st = n.save()
        self.set_score(n, 0, 6990)
        lives = expected_lives(n)
        self.score_points(n, 0)
        self.assertEqual(expected_lives(n)[0], lives[0] + 1, '7000: +1')
        self.assertEqual(expected_lives(n)[1], lives[1], 'P2 unaffected')
        self.score_points(n, 0)
        self.assertEqual(expected_lives(n)[0], lives[0] + 1, 'threshold used once')
        self.set_score(n, 0, 13990)
        self.score_points(n, 0)
        self.assertEqual(expected_lives(n)[0], lives[0] + 2, '14000: +1')
        g = glyphs(Path(self.rom).read_bytes())
        n.step(8)
        self.assertEqual(wait_hud(n, g)[0], lives[0] + 2, 'HUD shows it')
        # one score crossing two thresholds gives both
        n.load(st)
        self.set_score(n, 0, 13990)
        self.score_points(n, 0)
        self.assertEqual(expected_lives(n)[0], lives[0] + 2, '7000 and 14000 at once')
        # new game: thresholds reset
        n2 = self.start(self.rom, two=False)
        self.assertEqual((n2[0xE6], n2[0xF8]), (7, 0))

    def test_extra_life_from_share_bonus(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        self.set_score(n, 1, 6900)
        n[0xE7], n[0xF9] = 7, 0                       # P2's next threshold: 7000
        before = expected_lives(n)[1]
        self.press_select(n, p2=True)
        self.assertEqual(score(n, 0x129), 7100)
        self.assertEqual(expected_lives(n)[1], before - 1 + 1, '-1 shared, +1 extra life')

    # ------------------------------------------------------------ banner, spawn
    def read_row(self, n, g, row, frames=8):
        best = ''
        inv = {v: k for k, v in {**{i: str(i) for i in range(10)}, 0x10: ' ', 0x0A: '1', 0x0B: '2', 0x0C: '4',
                                 **{0x11 + i: chr(65 + i) for i in range(26)}}.items()}
        for _ in range(frames):
            f = n.step()
            cells = [read_tile(f, g, c, row) for c in range(3, 29)]
            if None in cells:
                continue
            names = {**{i: str(i) for i in range(10)}, 0x10: ' ', 0x0A: '1', 0x0B: '2', 0x0C: '4',
                     **{0x11 + i: chr(65 + i) for i in range(26)}}
            return ''.join(names.get(c, '?') for c in cells)
        return best

    def test_revive_prompt(self):
        g = glyphs(Path(self.rom).read_bytes(), tiles=list(range(0x10, 0x2B)) + list(range(10)) + [0x0A, 0x0B, 0x0C])
        n = self.p1_out_p2_playing(p2_reserve=2)
        n.step(6)
        self.assertEqual(self.read_row(n, g, 1).strip(), 'P2 SELECT TO REVIVE P1')
        st = n.save()
        self.press_select(n, p2=True)
        n.step(6)
        self.assertEqual(self.read_row(n, g, 1).strip(), '', 'prompt removed after the revive')
        n.load(st)
        n[LIVES2] = 0                                   # P2 on X1: no prompt
        n.step(6)
        self.assertEqual(self.read_row(n, g, 1).strip(), 'P1 OUT')
        n2 = self.p2_out_p1_playing(p1_reserve=2)
        n2.step(6)
        self.assertEqual(self.read_row(n2, g, 1).strip(), 'P1 SELECT TO REVIVE P2')

    def test_spawn_positions(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        self.assertEqual((n[SHIP_X], n[P2_X]), (0xF4, 0x0C), 'P1 left, P2 right')
        frame = n.step()
        p2_left = (n[P2_X] + 0x79) & 0xFF
        p1_right = 120 + (n[SHIP_X] - 256) + 14
        self.assertGreater(p2_left, p1_right, 'no overlap')
        n.controller = pads(LEFT, RIGHT); n.step(30); n.controller = 0
        self.clear_stage(n)
        for _ in range(300):
            n.step()
            if n[SUBSTATE] == 8:
                break
        self.assertEqual((n[SHIP_X], n[P2_X]), (0xF4, 0x0C), 'next stage')
        n1 = self.start(self.rom, two=False)
        self.assertEqual(n1[SHIP_X], 0, '1P keeps the centre')
        r = self.p1_out_p2_playing(p2_reserve=2)        # revive beside the partner
        p2x = r[P2_X]
        self.press_select(r, p2=True)
        self.assertEqual(r[P2_X], p2x, 'donor not moved')
        self.assertEqual(abs(((r[SHIP_X] - p2x + 128) & 0xFF) - 128), 24)

    def test_w4_stress_no_overrun(self):
        """Both pilots on W4 firing all the time (lives kept up): no frame overrun."""
        rnd = random.Random(3)
        n = self.start(self.rom, two=True)
        prev = n[0x3A] | n[0x3B] << 8
        worst = 1 << 16
        for i in range(60 * 60 * 2):
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            fire = B if (i // 3) % 2 == 0 else 0
            n.controller = pads(fire | rnd.choice([0, LEFT, RIGHT]), fire | rnd.choice([0, LEFT, RIGHT]))
            state = n[STATE]
            n.step()
            self.assertFalse(state == 3 and n[STATE] in (0, 1), 'NMI overrun reset the game')
            cur = n[0x3A] | n[0x3B] << 8
            if n[STATE] == 3:
                worst = min(worst, (cur - prev) & 0xFFFF)
            prev = cur
        self.assertGreater(worst, 0)

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
