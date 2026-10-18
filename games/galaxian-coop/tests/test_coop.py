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
from nestest import NES, A, B, LEFT, RIGHT, SELECT, START, ines_compatible, pads, ram, save_png  # noqa: E402

ORIG = Path(os.environ.get('GALAXIAN_ROM', build.DEFAULT_ROM))


def _symbols():
    from asm6502 import Assembler
    asm = Assembler()
    build.assemble(asm)
    return asm.symbols


SYM = _symbols()        # addresses of the mod's variables, from coop.asm

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


def idle_counter(nes):
    """Main-loop counter $3A/$3B (idle CPU time). An NMI between INC $3A (wrap
    to 0) and INC $3B leaves the high byte one behind: then add 256. The
    interrupted PC: cynes state bytes 6-7 (PC), or the NMI's return address on
    the stack ($014C/$014D, S = $4A) when the step ended on the NMI entry."""
    state = bytes(nes.save())
    pc = state[6] | state[7] << 8
    if pc == 0xE20C:
        pc = nes[0x14C] | nes[0x14D] << 8
    value = nes[0x3A] | nes[0x3B] << 8
    if nes[0x3A] == 0 and pc in (0xE18D, 0xE192):
        value = (value + 256) & 0xFFFF
    return value


def nametable(nes, which=0):
    """Nametable bytes from a cynes save state: 0 = $2000 (play), 1 = $2800
    (title). The 2 KiB of nametable RAM start at offset 9186 (located by the
    HUD and title rows; RC2/RC3 used 10242 here, 32 bytes into the second
    table, so the one test that used it compared the wrong rows)."""
    state = bytes(nes.save())
    return state[9186 + 1024 * which:9186 + 1024 * (which + 1)]


def wait_hud(n, g, frames=16):
    """Lives shown after `frames` frames: the last readable HUD in that window
    (RC4 refreshes the HUD within 12 frames, so earlier frames can be stale)."""
    last = None
    for _ in range(frames):
        hud = lives_hud(n.step(), g)
        if hud is not None:
            last = hud
    return last


def wait_hud_p1(n, g, frames=16):
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
    elif n[P1_DEAD] == 0 or n[0x25]:      # alive, or next ship already granted (P1_GRANTED)
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
        allowed |= {0x1000 + build.SECONDS_TILE * 16 + k for k in range(16)}
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
            recent = (recent + [expected_lives(n)])[-14:]
            if i % 5 == 0 and len(set(recent)) == 1:  # HUD: update every 4th frame + stream (RC4: up to 12 frames)
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
        seen = False
        for _ in range(16):                              # shielded: it blinks
            n.step()
            seen |= p2_visible(n)
        self.assertTrue(seen)

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
                n.load(state)                       # sprite: laser only on W4; P1 palette 2 (RC4)
                n[self.WLEVEL0] = level
                n.controller = pads(B); n.step(3); n.controller = 0; n.step(2)
                tile, attr = n[0x281], n[0x282]
                self.assertEqual((tile, attr), (0x60, 2) if level == 3 else (0x30, 2))

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
        for boost, want in ((399, 1), (400, 2)):          # +3999 / +4000 points (RC4: was 5000)
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
        # banner "P1 GREAT SHOT", gone after ~2 s; RC4: row 2 shows the
        # overdrive countdown instead of "W4 RED LASER"
        g = glyphs(Path(self.rom).read_bytes(), tiles=list(range(0x10, 0x2B)) + [0x0A, 0x0B, 0x0C])
        n.step(6)
        self.assertEqual(self.read_row(n, g, 1).strip(), 'P1 GREAT SHOT')
        self.assertEqual(self.status_row(n)[0], 'W4 30s')
        n.step(130)
        self.assertEqual(self.read_row(n, g, 1).strip(), '')
        self.assertEqual(self.status_row(n)[0], 'W4 28s')
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
        n.step(16)                                       # RC4: the HUD is refreshed within 12 frames
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

    # ------------------------------------------------------------ RC2: fire, death, stage 1
    SHIELD0 = SYM['SHIELD']

    @staticmethod
    def calm(n):
        """No enemy bullets and no divers: only what the test sets up can hit."""
        for k in range(7):
            n[0x284 + 4 * k] = 0
        for k in range(8):
            n[0x738 + k] = 0

    def coop_at_edges(self):
        """Co-op game, P1 far left and P2 far right (outside the formation)."""
        n = self.start(self.rom, two=True)
        for _ in range(130):
            self.calm(n)
            n.controller = pads(LEFT, RIGHT)
            n.step()
        n.controller = 0
        n[LIVES1] = n[LIVES2] = 5
        self.run_pads(n, [0] * 60)                       # let every shot land
        return n

    def run_pads(self, n, seq1, seq2=None):
        """Feed buttons frame by frame (calm screen); frames with a new shot per pilot."""
        seq2 = seq2 if seq2 is not None else [0] * len(seq1)
        new = ([], [])
        prev = [n[self.BUL_Y0 + k] for k in range(8)]
        for i, (b1, b2) in enumerate(zip(seq1, seq2)):
            self.calm(n)
            n.controller = pads(b1, b2)
            n.step()
            cur = [n[self.BUL_Y0 + k] for k in range(8)]
            for k in range(8):
                if cur[k] > prev[k]:                     # shots only move up
                    new[k // 4].append(i)
            prev = cur
        n.controller = 0
        return new

    @staticmethod
    def presses(times, on=2, off=2):
        return ([B] * on + [0] * off) * times

    def flying(self, n, pilot):
        return sum(1 for k in range(4) if n[self.BUL_Y0 + 4 * pilot + k])

    def alive(self, n, pilot):
        if pilot == 0:
            return n[P1_DEAD] == 0 and not n[P1_OUT]
        return n[P2_STATE] == 1

    def kill(self, n, pilot):
        """An enemy bullet just above the pilot's ship."""
        x = n[SHIP_X] if pilot == 0 else n[P2_X]
        n[0x284], n[0x287] = 0xC4, (x + 0x7A + 2) & 0xFF
        for _ in range(12):
            n.step()
            if not self.alive(n, pilot):
                return
        self.fail(f'P{pilot + 1} not hit')

    def survives(self, n, pilot, shots=5):
        """True when enemy bullets fired at the pilot do not hit it."""
        for _ in range(shots):
            x = n[SHIP_X] if pilot == 0 else n[P2_X]
            n[0x284], n[0x287] = 0xC4, (x + 0x7A + 2) & 0xFF
            for _ in range(6):
                n.step()
                if not self.alive(n, pilot):
                    return False
        return True

    def wait_back(self, n, pilot, b1=0, b2=0, frames=900):
        """Until the pilot's ship is in normal play again; returns new shots meanwhile."""
        new = ([], [])
        for i in range(frames):
            if self.alive(n, pilot) and n[SUBSTATE] == 8:
                return new
            got = self.run_pads(n, [b1], [b2])
            new[0].extend(got[0]); new[1].extend(got[1])
        self.fail(f'P{pilot + 1} did not come back')

    def test_fire_one_shot_per_press(self):
        n = self.coop_at_edges()
        state = n.save()
        for level in range(4):
            shots = level + 1
            n.load(state)
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
            got = self.run_pads(n, [B] * 120, [B] * 120)
            self.assertEqual([len(g) for g in got], [1, 1], f'W{shots}: FIRE held 120 frames = 1 shot')
            n.load(state)
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
            got = self.run_pads(n, self.presses(shots + 1), self.presses(shots + 1))
            self.assertEqual([len(g) for g in got], [shots, shots], f'W{shots}: one shot per press, full pool blocks')
            self.assertEqual((self.flying(n, 0), self.flying(n, 1)), (shots, shots))
            for _ in range(80):                          # a shot reaches the top
                if self.flying(n, 0) < shots and self.flying(n, 1) < shots:
                    break
                self.run_pads(n, [0])
            got = self.run_pads(n, self.presses(1), self.presses(1))
            self.assertEqual([len(g) for g in got], [1, 1], f'W{shots}: a free slot fires on a new press')
            if level == 3:                               # W4: one press = one laser (RC4: P1's yellow)
                self.assertEqual((n[0x281], n[0x282]), (0x60, 2))
        n.load(state)                                    # independent buttons
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        got = self.run_pads(n, [B] * 40, self.presses(4))
        self.assertEqual([len(g) for g in got], [1, 4])
        n.load(state)
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        got = self.run_pads(n, self.presses(4), [B] * 40)
        self.assertEqual([len(g) for g in got], [4, 1])

    def test_death_resets_weapon_and_shots(self):
        n = self.coop_at_edges()
        state = n.save()
        for pilot in (0, 1):
            other = 1 - pilot
            for level in (1, 2, 3):
                n.load(state)
                for p in (0, 1):
                    n[self.WLEVEL0 + p], n[self.BOOST_LO0 + p], n[self.NODEATH_LO0 + p] = level, 150, 200
                self.run_pads(n, self.presses(level + 1), self.presses(level + 1))
                self.assertEqual(self.flying(n, pilot), level + 1)
                self.kill(n, pilot)
                tag = f'P{pilot + 1} dies on W{level + 1}'
                self.assertEqual((n[self.WLEVEL0 + pilot], n[self.BOOST_LO0 + pilot], n[self.BOOST_HI0 + pilot],
                                  n[self.NODEATH_LO0 + pilot], n[self.NODEATH_HI0 + pilot]), (0, 0, 0, 0, 0), tag)
                self.assertEqual(self.flying(n, pilot), 0, tag + ': its shots removed')
                self.assertEqual((n[self.WLEVEL0 + other], n[self.BOOST_LO0 + other]), (level, 150), tag + ': partner kept')
                self.assertGreater(self.flying(n, other), 0, tag + ": partner's shots fly on")
                self.run_pads(n, [0] * 50)
                seq = self.presses(3)
                got = self.run_pads(n, seq, seq)
                self.assertEqual(len(got[pilot]), 0, tag + ': no shots while dead')
                self.assertEqual(len(got[other]), min(3, level + 1), tag + ': partner fires on its level')
                held = (B, 0) if pilot == 0 else (0, B)  # FIRE held through the respawn
                got = self.wait_back(n, pilot, *held)
                got2 = self.run_pads(n, [held[0]] * 30, [held[1]] * 30)
                self.assertEqual(len(got[pilot]) + len(got2[pilot]), 0, tag + ': no shot from a held button')
                seq = self.presses(3)
                got = self.run_pads(n, seq if pilot == 0 else [0] * 12, seq if pilot == 1 else [0] * 12)
                self.assertEqual(len(got[pilot]), 1, tag + ': back on W1, one shot at a time')
                self.assertEqual(n[self.WLEVEL0 + pilot], 0)

    def w_digits(self, n, g, frames=24):
        """Weapon digits shown in the HUD (P1, P2)."""
        names = {1: 1, 2: 2, 3: 3, 0x0C: 4}
        for _ in range(frames):
            f = n.step()
            cells = read_tile(f, g, 3, 3), read_tile(f, g, 30, 3)
            if all(c in names for c in cells):
                return tuple(names[c] for c in cells)
        return None

    def test_stage_one_boost_for_pilots_in_game(self):
        """Co-op free W2 at the first cleared stage: pilots in play get it, and
        so does a pilot hit just before the clear with a reserve ship coming
        (it comes back with W2); a pilot hit on its last ship or already out
        gets none, also after a later revive."""
        g = glyphs(Path(self.rom).read_bytes(), tiles=[1, 2, 3, 0x0C])
        n = self.start(self.rom, two=True)               # both in play: both W2, HUD too
        n.step(3)
        self.clear_stage(n)
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (1, 1))
        for _ in range(300):
            n.step()
            if n[SUBSTATE] == 8:
                break
        self.assertEqual(self.w_digits(n, g), (2, 2), 'HUD W2 / W2')
        for pilot in (0, 1):                             # hit just before the clear, ship coming: W2
            n = self.coop_at_edges()
            self.kill(n, pilot)
            self.assertFalse(self.alive(n, pilot))
            self.clear_stage(n)
            self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (1, 1), f'P{pilot + 1} waiting at the clear')
            self.assertEqual(n[SYM['W2_OWNED'] + pilot], 1)
            self.wait_back(n, pilot)
            self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (1, 1), 'back with W2')
            for _ in range(300):
                n.step()
                if n[SUBSTATE] == 8:
                    break
            self.assertEqual(self.w_digits(n, g), (2, 2), 'HUD W2 / W2')
        for pilot in (0, 1):                             # hit on the last ship: none
            n = self.coop_at_edges()
            n[LIVES1 if pilot == 0 else LIVES2] = 0
            self.kill(n, pilot)
            self.clear_stage(n)
            want = [1, 1]
            want[pilot] = 0
            self.assertEqual([n[self.WLEVEL0], n[self.WLEVEL0 + 1]], want, f'P{pilot + 1} hit on its last ship')
            for _ in range(600):
                n.step()
            self.assertTrue(n[P1_OUT] if pilot == 0 else n[P2_STATE] == 0, 'eliminated')
            self.assertEqual(n[self.WLEVEL0 + pilot], 0)
        n = self.p1_out_p2_playing(p2_reserve=2)         # P1 X0: only P2
        self.clear_stage(n)
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (0, 1))
        for _ in range(300):
            n.step()
            if n[SUBSTATE] == 8:
                break
        self.press_select(n, p2=True)                    # revived later: still W1
        self.assertFalse(n[P1_OUT])
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (0, 1))
        n = self.p2_out_p1_playing(p1_reserve=2)         # P2 X0: only P1
        self.clear_stage(n)
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (1, 0))

    # ------------------------------------------------------------ respawn shield
    def ship_shown(self, n, frame, pilot):
        if pilot == 1:
            return n[P2_OAM] < 0xEF
        x = (120 + ((n[SHIP_X] + 128) & 0xFF) - 128) & 0xFF
        return int(frame[209:225, max(0, x - 4):x + 20].any(2).sum()) > 30

    @staticmethod
    def blink_hidden(shield):
        if shield == 0:
            return False
        return ((shield - 1) & 8) == 0 if shield > 60 else ((shield - 1) & 4) == 0

    def respawned(self, pilot):
        n = self.coop_at_edges()
        self.kill(n, pilot)
        self.assertEqual(n[self.SHIELD0 + pilot], 240, 'set when hit, waits for the ship')
        for _ in range(60):
            self.run_pads(n, [0])
            self.assertEqual(n[self.SHIELD0 + pilot], 240, 'no countdown while the ship is away')
            if self.alive(n, pilot):
                break
        self.wait_back(n, pilot)
        return n

    def check_shield(self, pilot):
        other = 1 - pilot
        n = self.respawned(pilot)
        state = n.save()
        self.assertEqual(n[self.WLEVEL0 + pilot], 0, 'W1 after the respawn')
        self.assertEqual(n[self.SHIELD0 + other], 0)
        start = n[self.SHIELD0 + pilot]                  # 240 game frames from the return
        self.assertIn(start, (239, 240))
        frames = 0
        while n[self.SHIELD0 + pilot]:
            before = n[self.SHIELD0 + pilot]
            self.run_pads(n, [0])
            self.assertEqual(n[self.SHIELD0 + pilot], before - 1, 'one tick per frame')
            frames += 1
        self.assertEqual(frames + (240 - start), 240)
        n.load(state)
        lives = n[LIVES1 + pilot]
        n[self.WLEVEL0 + pilot], n[self.BOOST_LO0 + pilot], n[self.NODEATH_LO0 + pilot] = 1, 77, 88
        self.assertTrue(self.survives(n, pilot), 'enemy bullets do not hit')
        self.assertEqual((n[LIVES1 + pilot], n[self.WLEVEL0 + pilot], n[self.BOOST_LO0 + pilot]), (lives, 1, 77))
        self.assertGreaterEqual(n[self.NODEATH_LO0 + pilot], 88, 'boost progress kept')
        x = n[SHIP_X] if pilot == 0 else n[P2_X]
        move = RIGHT if pilot == 0 else LEFT
        self.run_pads(n, *(([move] * 20, [0] * 20) if pilot == 0 else ([0] * 20, [move] * 20)))
        x2 = n[SHIP_X] if pilot == 0 else n[P2_X]
        self.assertEqual(abs(((x2 - x + 128) & 0xFF) - 128), 20, 'moves')
        held = [B] * 60
        got = self.run_pads(n, held if pilot == 0 else [0] * 60, held if pilot == 1 else [0] * 60)
        self.assertEqual(len(got[pilot]), 1, 'fires; held FIRE = one shot')
        self.assertGreater(n[self.SHIELD0 + pilot], 0)
        for _ in range(240):
            if n[self.SHIELD0 + pilot] == 0:
                break
            self.run_pads(n, [0])
        self.assertEqual(n[self.SHIELD0 + pilot], 0)
        self.kill(n, pilot)                              # shield over: hit again

    def test_shield_p1(self):
        self.check_shield(0)

    def test_shield_p2(self):
        self.check_shield(1)

    def test_shield_blocks_diver_collisions(self):
        """Natural diver collisions (enemy bullets removed) replayed with a shield."""
        import random
        found = {}
        rnd = random.Random(1)
        n = self.start(self.rom, two=True)
        hist, c = [], 0
        for i in range(60 * 60 * 6):
            for k in range(7):
                n[0x284 + 4 * k] = 0
            n[LIVES1] = n[LIVES2] = 5
            if i % 10 == 0:
                c = pads(rnd.choice([0, LEFT, RIGHT]), rnd.choice([0, LEFT, RIGHT]))
            n.controller = c
            hist = (hist + [(n.save(), c)])[-12:]
            was = [self.alive(n, 0), self.alive(n, 1)]
            n.step()
            for pilot in (0, 1):
                if was[pilot] and not self.alive(n, pilot) and pilot not in found:
                    found[pilot] = list(hist)
            if len(found) == 2:
                break
        self.assertEqual(sorted(found), [0, 1], 'no diver collision found for both pilots')
        for pilot, frames in found.items():
            for shield in (0, 200):
                m = NES(self.rom)
                m.load(frames[0][0])
                m[self.SHIELD0 + pilot] = shield
                hit = False
                for _, pad in frames + [(None, frames[-1][1])] * 8:
                    for k in range(7):
                        m[0x284 + 4 * k] = 0
                    m.controller = pad
                    m.step()
                    hit = hit or not self.alive(m, pilot)
                self.assertEqual(hit, shield == 0, f'P{pilot + 1} diver collision, shield {shield}')

    def test_shields_independent(self):
        n = self.coop_at_edges()
        n[0x284], n[0x287] = 0xC4, (n[SHIP_X] + 0x7C) & 0xFF   # both hit together
        n[0x288], n[0x28B] = 0xC4, (n[P2_X] + 0x7C) & 0xFF
        n.step(10)
        self.assertFalse(self.alive(n, 0) or self.alive(n, 1))
        self.assertEqual((n[self.SHIELD0], n[self.SHIELD0 + 1]), (240, 240))
        self.wait_back(n, 0)
        self.wait_back(n, 1)
        both = (n[self.SHIELD0], n[self.SHIELD0 + 1])
        self.assertTrue(all(both), 'both shielded at once')
        self.assertNotEqual(both[0], both[1], 'separate counters')
        self.assertTrue(self.survives(n, 0, 2) and self.survives(n, 1, 2))
        while n[self.SHIELD0]:                           # P1's ends first, P2 still shielded
            self.run_pads(n, [0])
        p2 = n[self.SHIELD0 + 1]
        self.assertGreater(p2, 0)
        n[self.WLEVEL0 + 1] = 2
        self.kill(n, 0)                                  # P1 dies: P2's shield and weapon stay
        self.assertEqual(n[self.SHIELD0], 240)
        self.assertLess(n[self.SHIELD0 + 1], p2)
        self.assertGreater(n[self.SHIELD0 + 1], 0)
        self.assertEqual(n[self.WLEVEL0 + 1], 2)
        self.assertTrue(self.survives(n, 1, 2), 'P2 still protected')

    def test_shield_after_life_sharing(self):
        n = self.p1_out_p2_playing(p2_reserve=2)
        n[self.SHIELD0 + 1] = 0
        self.press_select(n, p2=True)
        self.assertFalse(n[P1_OUT])
        self.assertGreater(n[self.SHIELD0], 220, 'receiver P1 shielded')
        self.assertEqual(n[self.SHIELD0 + 1], 0, 'donor not shielded')
        self.assertTrue(self.survives(n, 0))
        n = self.p2_out_p1_playing(p1_reserve=2)
        n[self.SHIELD0] = 0
        self.press_select(n, p1=True)
        self.assertEqual(n[P2_STATE], 1)
        self.assertGreater(n[self.SHIELD0 + 1], 220, 'receiver P2 shielded')
        self.assertEqual(n[self.SHIELD0], 0, 'donor not shielded')
        self.assertTrue(self.survives(n, 1))

    def test_no_shield_at_game_or_stage_start(self):
        n = self.start(self.rom, two=True)
        n.step(3)
        self.assertEqual((n[self.SHIELD0], n[self.SHIELD0 + 1]), (0, 0), 'new game')
        self.kill(n, 0)
        n = self.start(self.rom, two=True)
        n.step(3)
        self.clear_stage(n)
        for _ in range(300):
            n.step()
            if n[SUBSTATE] == 8 and n[P1_DEAD] == 0:
                break
        n.step(3)
        self.assertEqual((n[self.SHIELD0], n[self.SHIELD0 + 1]), (0, 0), 'next stage')
        self.kill(n, 1)

    def test_single_player_has_no_shield(self):
        n = self.start(self.rom, two=False)
        n[LIVES1] = 3
        n.controller = pads(LEFT); n.step(60); n.controller = 0
        self.kill(n, 0)
        self.assertEqual(n[self.SHIELD0], 0)
        self.wait_back(n, 0)
        self.assertEqual(n[self.SHIELD0], 0)
        for _ in range(30):                              # no blinking
            f = n.step()
            self.assertTrue(self.ship_shown(n, f, 0))
        self.kill(n, 0)

    def test_shield_blinking(self):
        for pilot in (0, 1):
            n = self.coop_at_edges()
            nt0 = nametable(n)[26 * 32:28 * 32]
            oam0 = [n[P2_OAM + k] for k in range(16)]
            self.kill(n, pilot)
            self.wait_back(n, pilot)
            hidden = shot_seen = 0
            if pilot == 1:                               # P2's shot stays visible while P2 blinks
                self.run_pads(n, [0], [B])
                n.controller = pads(0, B)
            for i in range(300):
                self.calm(n)
                sh = n[self.SHIELD0 + pilot]
                f = n.step()
                if pilot == 1:                           # P2 is drawn after this frame's countdown,
                    sh = n[self.SHIELD0 + 1]             # P1's background before it
                shown = self.ship_shown(n, f, pilot)
                self.assertEqual(shown, not self.blink_hidden(sh), f'P{pilot + 1} frame {i}, shield {sh}')
                hidden += not shown
                if pilot == 1 and not shown and n[self.BUL_Y0 + 4]:
                    self.assertLess(n[P2_BUL_OAM], 0xEF, "P2's shot drawn")
                    shot_seen += 1
                if pilot == 1 and i == 2:
                    n.controller = 0
                if sh == 0:
                    break
            self.assertGreater(hidden, 100)
            self.assertTrue(pilot == 0 or shot_seen, 'shot checked while P2 hidden')
            for _ in range(60):                          # visible for good afterwards
                self.calm(n)
                f = n.step()
                self.assertTrue(self.ship_shown(n, f, pilot))
                self.assertTrue(self.ship_shown(n, f, 1 - pilot))
            self.assertEqual(nametable(n)[26 * 32:28 * 32], nt0, 'ship rows unchanged')
            if pilot == 1:
                self.assertEqual([n[P2_OAM + k] for k in range(16) if k % 4 != 3],
                                 [oam0[k] for k in range(16) if k % 4 != 3], 'P2 sprites as before')

    # ------------------------------------------------------------ RC3: ghost shots, parity
    SHOT_OAM = (0x280, 0x2BC, 0x2C0, 0x2C4, 0x2B0, 0x2B4, 0x2B8, 0x2C8)

    def ghost_sprites(self, n, pilot):
        """Shot sprites queued for the pilot's slots (the pilot is not in play)."""
        return [a for a in self.SHOT_OAM[4 * pilot:4 * pilot + 4]
                if n[a] < 0xEF and n[a + 1] in (0x30, 0x60)]

    def away_without_shots(self, n, pilot, frames, until_back=True):
        """Pilot away (hit, READY, waiting or out) while the partner fights on W4
        and both pads mash FIRE: no shot of the pilot in RAM, OAM or score."""
        other = 1 - pilot
        row = 0x117 if pilot == 0 else 0x129
        before = score(n, row)
        phases = set()
        for i in range(frames):
            if until_back and self.alive(n, pilot) and n[SUBSTATE] == 8:
                break
            n[self.WLEVEL0 + other] = 3
            n[LIVES1 + other] = max(n[LIVES1 + other], 3)
            fire = B if (i // 3) % 2 == 0 else 0
            n.controller = pads(fire, fire)
            n.step()
            if until_back and self.alive(n, pilot) and n[SUBSTATE] == 8:
                break                                    # back: its ready shot may show
            phases.add((n[SUBSTATE], n[P1_DEAD] != 0 if pilot == 0 else n[P2_STATE]))
            self.assertEqual(self.flying(n, pilot), 0, f'P{pilot + 1} shot in RAM, frame {i}')
            self.assertEqual(self.ghost_sprites(n, pilot), [], f'P{pilot + 1} shot sprite, frame {i}')
        n.controller = 0
        self.assertEqual(score(n, row), before, f'P{pilot + 1} scored while away')
        return phases

    def test_p1_death_no_ghost_shots(self):
        for reserve in (1, 0):                           # X2 -> X1, X1 -> X0
            n = self.coop_at_edges()
            n[LIVES1] = reserve
            n[self.WLEVEL0] = 3
            self.run_pads(n, self.presses(4))
            self.assertEqual(self.flying(n, 0), 4)
            self.kill(n, 0)                              # a real hit by an enemy bullet
            self.assertEqual(self.flying(n, 0), 0, 'shots removed at once')
            self.assertEqual(self.ghost_sprites(n, 0), [], 'and their sprites')
            phases = self.away_without_shots(n, 0, 900 if reserve else 600, until_back=bool(reserve))
            if reserve:                                  # explosion, READY, back
                self.assertIn((8, True), phases)
                self.assertTrue(any(fe != 8 for fe, _ in phases), 'READY sequence covered')
            else:                                        # X0: out of the fight
                self.assertTrue(n[P1_OUT])
                n[LIVES2] = 2
                self.press_select(n, p2=True)            # revived by P2
                self.assertFalse(n[P1_OUT])
            self.assertEqual(n[self.WLEVEL0], 0, 'back on W1')
            self.assertGreater(n[self.SHIELD0], 200, 'with a shield')
            got = self.run_pads(n, [B] * 40)             # held through the return: nothing new
            self.assertLessEqual(len(got[0]), 1)
            got = self.run_pads(n, [0] * 4 + self.presses(3))
            self.assertEqual(len(got[0]), 1, 'a new press: one W1 shot')

    def test_p2_death_no_ghost_shots(self):
        for reserve in (1, 0):
            n = self.coop_at_edges()
            n[LIVES2] = reserve
            n[self.WLEVEL0 + 1] = 3
            self.run_pads(n, [0] * 16, self.presses(4))
            self.assertEqual(self.flying(n, 1), 4)
            self.kill(n, 1)
            self.assertEqual(self.flying(n, 1), 0)
            self.assertEqual(self.ghost_sprites(n, 1), [])
            self.away_without_shots(n, 1, 900 if reserve else 600, until_back=bool(reserve))
            if not reserve:
                self.assertEqual(n[P2_STATE], 0)
                n[LIVES1] = 2
                self.press_select(n, p1=True)
                self.assertEqual(n[P2_STATE], 1)
            self.assertEqual(n[self.WLEVEL0 + 1], 0)
            self.assertGreater(n[self.SHIELD0 + 1], 200)
            got = self.run_pads(n, [0] * 40, [B] * 40)
            self.assertLessEqual(len(got[1]), 1)
            got = self.run_pads(n, [0] * 16, [0] * 4 + self.presses(3))
            self.assertEqual(len(got[1]), 1)

    def shot_profile(self, n, pilot):
        """Press FIRE once: (frames to the shot, its Y per frame, X kept, flight)."""
        n.controller = 0
        self.calm(n)
        n.step()
        lat, ys, xs = None, [], set()
        for f in range(80):
            self.calm(n)
            n.controller = pads(B if f < 6 else 0, 0) if pilot == 0 else pads(0, B if f < 6 else 0)
            n.step()
            y = n[self.BUL_Y0 + 4 * pilot]
            if y and lat is None:
                lat = f + 1
            if lat is not None:
                if y == 0:
                    break
                ys.append(y)
                xs.add(n[0x0E + 4 * pilot])
        return lat, ys, len(xs) == 1

    def test_weapon_parity(self):
        n = self.coop_at_edges()
        state = n.save()
        flights = {0: 50, 1: 46, 2: 42, 3: 32}           # full flights measured at 100/110/120/160 %
        for level in range(4):
            got = []
            for pilot in (0, 1):
                n.load(state)
                n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
                lat, ys, x_kept = self.shot_profile(n, pilot)
                self.assertTrue(x_kept, f'P{pilot + 1} W{level + 1}: shot X never changes')
                n.load(state)
                n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
                presses = self.presses(level + 3)        # rapid presses, more than the pool
                seq = (presses, [0] * len(presses)) if pilot == 0 else ([0] * len(presses), presses)
                shots = self.run_pads(n, *seq)[pilot]
                xs = {n[0x0E + 4 * pilot + k] for k in range(4) if n[self.BUL_Y0 + 4 * pilot + k]}
                got.append((lat, ys, len(shots), self.flying(n, pilot)))
                self.assertEqual(len(xs), 1, f'P{pilot + 1} W{level + 1}: all shots from one X')
            self.assertEqual(got[0], got[1], f'W{level + 1}: P1 and P2 identical')
            lat, ys, shots, flying = got[0]
            self.assertEqual(lat, 2, 'shot on the 2nd frame of a press')
            self.assertEqual(len(ys), flights[level], f'W{level + 1} flight frames')
            self.assertEqual((shots, flying), (level + 1, level + 1), 'pool fills, extra presses blocked')
        n.load(state)                                    # both W4: 8 shots at most
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        most = 0
        for i in range(60):
            self.run_pads(n, [B if (i // 2) % 2 == 0 else 0], [B if (i // 2) % 2 == 0 else 0])
            most = max(most, self.flying(n, 0) + self.flying(n, 1))
        self.assertEqual(most, 8)

    def test_w4_with_shields_stable(self):
        import random
        rnd = random.Random(5)
        n = self.start(self.rom, two=True)
        lag, resets = n[0x67E], 0
        for i in range(60 * 60):
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            for p in (0, 1):
                if n[self.SHIELD0 + p] == 0:
                    n[self.SHIELD0 + p] = 240
            fire = B if (i // 3) % 2 == 0 else 0
            n.controller = pads(fire | rnd.choice([0, LEFT, RIGHT]), fire | rnd.choice([0, LEFT, RIGHT]))
            state = n[STATE]
            n.step()
            resets += state == 3 and n[STATE] in (0, 1)
        self.assertEqual((resets, n[0x67E]), (0, lag), 'no reset, no lag frame')
        self.assertFalse(n.has_crashed)

    def test_hud_scores_follow_points(self):
        """Scores and hi score are copied to the HUD only in frames with points
        (HudScores): the screen must still follow every change."""
        g = glyphs(Path(self.rom).read_bytes())
        for two in (False, True):
            n = self.start(self.rom, two=two)
            for k in range(6):                           # hi score 000000: beaten at once
                n[0x120 + k] = 0x10 if k < 5 else 0
            for _ in range(6):
                before = score(n, 0x117)
                for _ in range(600):
                    n[LIVES1] = max(n[LIVES1], 3)
                    n.controller = pads(B if n[0x104] & 4 else 0)
                    n.step()
                    if score(n, 0x117) != before:
                        break
                n.controller = 0
                for k in range(8):                       # no second kill while the HUD catches up
                    n[0x16 + k] = 0
                n.step(3)                                # RC4: copied in the 2 frames after the kill
                want = [n[0x117 + k] for k in range(6)]
                self.assertEqual([n[0x120 + k] for k in range(6)], want, 'hi score follows P1')
                shown = None
                for _ in range(12):
                    f = n.step()
                    p1 = [read_tile(f, g, c, 4) for c in range(4, 10)]
                    hi = [read_tile(f, g, c, 4) for c in range(13, 19)]
                    want = [n[0x117 + k] for k in range(6)]
                    if all(c is None or c == w for cells in (p1, hi) for c, w in zip(cells, want)) \
                            and min(sum(c is not None for c in p1), sum(c is not None for c in hi)) >= 4:
                        shown = p1                       # None: a star crosses the cell
                        break
                self.assertIsNotNone(shown, f'HUD shows {[n[0x117 + k] for k in range(6)]}, pixels {p1} {hi}')
        n = self.start(self.rom, two=True)               # P2 sets the hi score (CoopHiScore)
        for k in range(6):
            n[0x120 + k] = 0x10 if k < 5 else 0
        before = score(n, 0x129)
        for _ in range(600):
            n[LIVES2] = max(n[LIVES2], 3)
            n.controller = pads(0, B if n[0x104] & 4 else 0)
            n.step()
            if score(n, 0x129) != before:
                break
        n.controller = 0
        want = [n[0x129 + k] for k in range(6)]
        shown = None
        for _ in range(16):
            f = n.step()
            hi = [read_tile(f, g, c, 4) for c in range(13, 19)]
            if hi == want:
                shown = hi
                break
        self.assertEqual(shown, want, 'HUD hi score shows P2')

    # ------------------------------------------------------------ RC4: score HUD
    SCORE_VALUES = (0, 10, 90, 100, 990, 1000, 1990, 2000, 2130, 2810, 3990, 4000, 4140, 5000, 5010,
                    6000, 7000, 14000)
    HUD_ROW3 = [0x10, 0x6E, 0x27, None, 0x10, 0x0A, 0x25, 0x20, 0x10, 0x10, 0x10, 0x10,
                0x18, 0x19, 0x2B, 0x23, 0x13, 0x1F, 0x22, 0x15, 0x10, 0x10, 0x10,
                0x0B, 0x25, 0x20, 0x10, 0x10, 0x6E, 0x27, None, 0x10]      # W1 1UP HI-SCORE 2UP W1

    @staticmethod
    def score_cells(value):
        """The 6 score cells as the game keeps them: blanks, at least '00'."""
        text = str(value).rjust(6) if value else '    00'
        return [0x10 if ch == ' ' else int(ch) for ch in text]

    def expected_hud(self, n):
        """Rows 3 and 4 of the co-op HUD as RAM says they must look (None: cols
        whose content RAM alone doesn't fix). P1, hi score, P2 from their rows."""
        wl = [0x01, 0x02, 0x03, 0x0C]
        row3 = list(self.HUD_ROW3)
        row3[3], row3[30] = wl[n[self.WLEVEL0]], wl[n[self.WLEVEL0 + 1]]
        p1, p2 = expected_lives(n)
        row4 = ([0x10, 0x6F, 0x28, min(p1, 9)] + [n[0x117 + k] for k in range(6)] + [0x10] * 3
                + [n[0x120 + k] for k in range(6)] + [0x10] * 2 + [n[0x129 + k] for k in range(6)]
                + [0x10, 0x6F, 0x28, min(p2, 9), 0x10])
        return row3, row4

    def hud_settled(self, n, frames=16):
        """Step until HUD rows 3-4 equal what RAM requires (the HUD streams in
        over a few frames); returns the last (got, want) pair."""
        for _ in range(frames):
            n.step()
            nt = nametable(n)
            got = (list(nt[96:128]), list(nt[128:160]))
            want = self.expected_hud(n)
            if all(w is None or g == w for gr, wr in zip(got, want) for g, w in zip(gr, wr)):
                return got, want
        return got, want

    def assert_hud(self, n, msg=''):
        got, want = self.hud_settled(n)
        for r, (gr, wr) in enumerate(zip(got, want)):
            bad = [(c, hex(g), hex(w)) for c, (g, w) in enumerate(zip(gr, wr)) if w is not None and g != w]
            self.assertEqual(bad, [], f'HUD row {r + 3} (col, shown, expected) {msg}')

    def assert_hud_pixels(self, n, g, msg=''):
        """The rendered score digits read back from the picture (glyph match)."""
        f = n.step()
        for base, col in ((0x117, 4), (0x120, 13), (0x129, 21)):
            cells = [read_tile(f, g, col + k, 4) for k in range(6)]
            want = [n[base + k] for k in range(6)]
            ok = [c is None or c == w for c, w in zip(cells, want)]  # None: a star crosses the cell
            self.assertTrue(all(ok), f'pixels {cells} != {want} {msg}')
            self.assertGreaterEqual(sum(c is not None for c in cells), 4, msg)
        for col in (10, 11, 12, 19, 20, 27):
            self.assertIn(read_tile(f, g, col, 4), (0x10, None), f'row 4 col {col} not blank {msg}')

    def set_scores(self, n, p1, p2):
        self.set_score(n, 0, p1)
        self.set_score(n, 1, p2)
        n[SYM['SCORE_NEW']] = 2                          # as after points (AfterScore)

    def test_score_hud_values(self):
        """Every listed score shown exactly in the HUD (nametable and pixels),
        P1 and P2 independent, hi score = the best of them, nothing beside."""
        g = glyphs(Path(self.rom).read_bytes())
        n = self.start(self.rom, two=True)
        n.step(200)                                      # some dives: the RC3 bug needed them
        best = score(n, 0x120)
        for i, v in enumerate(self.SCORE_VALUES):
            v2 = self.SCORE_VALUES[-1 - i]
            n[LIVES1], n[LIVES2] = 3, 3
            self.set_scores(n, v, v2)
            self.assert_hud(n, f'P1 {v} P2 {v2}')
            best = max(best, v, v2)
            self.assertEqual(score(n, 0x120), best, 'hi score')
            self.assertEqual([n[0x117 + k] for k in range(6)], self.score_cells(v), 'P1 row')
            self.assert_hud_pixels(n, g, f'P1 {v} P2 {v2}')

    def test_score_hud_photo_cases(self):
        """photos from manual testing: P1 2130 / P2 2810 / HI 5000 (W1), P1 4140 /
        P2 5010 (W2), and P1 out (X0) at 14530 with P2 on W4 near 20000 and
        the revive prompt on screen."""
        g = glyphs(Path(self.rom).read_bytes())
        for p1, p2, level in ((2130, 2810, 0), (4140, 5010, 1)):
            n = self.start(self.rom, two=True)
            for i in range(900):                         # natural play first (dives, shots)
                n[LIVES1], n[LIVES2] = 3, 3
                n.controller = pads(B if i % 6 < 2 else 0, B if i % 6 < 3 else 0)
                n.step()
            n.controller = 0
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
            self.set_scores(n, p1, p2)
            self.assert_hud(n, f'{p1}/{p2}')
            self.assert_hud_pixels(n, g)
            n.controller = pads(START); n.step(); n.controller = 0     # pause
            n.step(30)
            self.assert_hud(n, 'paused')
            self.assert_hud_pixels(n, g, 'paused')
            n.controller = pads(START); n.step(); n.controller = 0
            n.step(30)
            self.assert_hud(n, 'resumed')
        n = self.p1_out_p2_playing(p2_reserve=2)
        n[self.WLEVEL0 + 1] = 3
        for i in range(600):                             # P2 keeps playing, dives go on
            n[LIVES2] = max(n[LIVES2], 2)
            n.controller = pads(0, B if i % 6 < 3 else 0)
            n.step()
        n.controller = 0
        self.set_scores(n, 14530, 20000)
        self.assertEqual(self.read_row(n, glyphs(Path(self.rom).read_bytes(),
                         tiles=list(range(0x10, 0x2B)) + [0x0A, 0x0B, 0x0C]), 1).strip(), 'P2 SELECT TO REVIVE P1')
        self.assert_hud(n, 'P1 out')
        self.assert_hud_pixels(n, g, 'P1 out')
        self.assertEqual(expected_lives(n)[0], 0)

    def test_score_hud_long_session(self):
        """Three minutes of both pilots scoring (lives kept up): whenever the
        scores rest, the HUD shows them exactly; no stray tile in rows 0-4."""
        rnd = random.Random(7)
        n = self.start(self.rom, two=True)
        checks = 0
        hold = [0, 0]
        for i in range(60 * 180):
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            if i % 20 == 0:
                hold = [rnd.choice([0, LEFT, RIGHT]), rnd.choice([0, LEFT, RIGHT])]
            n.controller = pads(hold[0] | (B if i % 4 < 2 else 0), hold[1] | (B if (i + 1) % 4 < 2 else 0))
            n.step()
            if i % 600 == 599:
                n.controller = 0
                self.calm(n)
                for k in range(8):
                    n[self.BUL_Y0 + k] = 0
                self.assert_hud(n, f'frame {i}')
                nt = nametable(n)
                self.assertEqual(set(nt[0:64]) - {0x10} - set(range(0x11, 0x2B)) - {0x0A, 0x0B, 0x0C}, set(),
                                 'rows 0-1: blank or banner text')
                self.assertEqual(set(nt[64:96]) - {0x10, 0x27, 0x0C, build.SECONDS_TILE, 0x23, 0x24, 0x17}
                                 - set(range(10)), set(), 'row 2: status row')
                checks += 1
        self.assertGreater(score(n, 0x117) + score(n, 0x129), 2000)
        self.assertEqual(checks, 18)

    def test_title_score_row_clean(self):
        """After GAME OVER the title shows the score row ($0116-$012F, FB70):
        digits and blanks only (RC2/RC3 kept variables between the scores)."""
        n = self.start(self.rom, two=True)
        for i in range(600):                             # some points and dives first
            if n[P2_STATE] == 1:                         # last ships (P2 entered from its reserve)
                n[LIVES1], n[LIVES2] = 0, 0
            n.controller = pads(B if i % 6 < 2 else 0, B if i % 6 < 3 else 0)
            n.step()
        n.controller = 0
        for pilot in (0, 1):
            for _ in range(600):
                if self.alive(n, pilot):
                    break
                n.step()
            self.kill(n, pilot)
        for _ in range(60 * 30):
            n.step()
            if n[STATE] == 1:
                break
        self.assertEqual(n[STATE], 1, 'back on the title')
        n.controller = 0
        n.step(30)
        row = list(nametable(n, 1)[4 * 32 + 3:4 * 32 + 29])
        self.assertTrue(all(t == 0x10 or t <= 9 for t in row), [hex(t) for t in row])
        self.assertEqual(row[7:9] + row[16:19], [0x10] * 5, 'gaps between the scores blank')

    # ------------------------------------------------------------ RC4: weapons, overdrive
    BASE_POINTS = {30, 40, 50, 60, 80, 100, 150, 200, 300, 800}

    def status_row(self, n):
        """HUD row 2 as text: P1 timer (cols 2-7), stage (13-18), P2 timer (22-27)."""
        names = {**{i: str(i) for i in range(10)}, 0x10: ' ', 0x0C: '4', build.SECONDS_TILE: 's',
                 **{0x11 + i: chr(65 + i) for i in range(26)}}
        row = nametable(n)[64:96]
        text = lambda a, b: ''.join(names.get(t, '?') for t in row[a:b])
        return text(2, 8), text(13, 19), text(22, 28), row

    def overdrive(self, n, pilot):
        """W3 with 7990 no-death points, then one kill: overdrive (W4) starts."""
        n[self.WLEVEL0 + pilot] = 2
        n[self.NODEATH_LO0 + pilot], n[self.NODEATH_HI0 + pilot] = 799 & 0xFF, 799 >> 8
        n[LIVES1 if pilot == 0 else LIVES2] = 5
        if (n[SHIP_X] if pilot == 0 else n[P2_X]) in range(0x60, 0xA0):   # under the formation
            n[SHIP_X if pilot == 0 else P2_X] = 0xE0 if pilot == 0 else 0x20
            n.step(2)
        self.calm_points(n, pilot)
        self.assertEqual(n[self.WLEVEL0 + pilot], 3, 'overdrive on')

    def calm_points(self, n, pilot, frames=1500):
        """Fire until the pilot scores, with no enemy fire or dives (no death)."""
        row = 0x117 if pilot == 0 else 0x129
        before = score(n, row)
        for i in range(frames):
            self.calm(n)
            btn = B if i % 4 < 2 else 0
            if i >= 240:                                 # nothing above: sweep for enemies
                btn |= LEFT if (i // 200) % 2 else RIGHT
            n.controller = pads(btn) if pilot == 0 else pads(0, btn)
            n.step()
            if score(n, row) != before:
                n.controller = 0
                return score(n, row) - before
        self.fail('no points scored')

    def play_frames(self, n, frames, fire=(False, False), keep=True):
        """Normal play for `frames` frames (lives kept, no enemy fire or
        dives), firing as asked; returns the frames spent in normal play (FE=8)."""
        played = 0
        for i in range(frames):
            if keep:
                n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
                self.calm(n)
            n.controller = pads(B if fire[0] and i % 4 < 2 else 0, B if fire[1] and i % 4 < 2 else 0)
            n.step()
            played += n[SUBSTATE] == 8
        n.controller = 0
        return played

    def test_w3_needs_4000_after_w2(self):
        """W2 -> W3: 4000 points counted from when W2 was given (no surplus
        carried over), plus a cleared stage; 3999 is not enough."""
        n = self.start(self.rom, two=False)
        n.step(3)
        n[self.BOOST_LO0], n[self.BOOST_HI0] = 350 & 0xFF, 350 >> 8   # 3500 points on W1
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 1, 'W2')
        self.assertEqual((n[self.BOOST_LO0], n[self.BOOST_HI0]), (0, 0), 'the 1500 surplus is not carried over')
        for boost, want in ((399, 1), (400, 2)):
            st = n.save()
            n[self.BOOST_LO0], n[self.BOOST_HI0] = boost & 0xFF, boost >> 8
            n.step(60)
            self.assertEqual(n[self.WLEVEL0], 1, 'no W3 before the stage is cleared')
            self.clear_stage(n)
            self.assertEqual(n[self.WLEVEL0], want, f'W2 + {boost * 10} points')
            n.load(st)
        n2 = self.start(self.rom, two=True)               # co-op: free W2 at 800 points
        n2.step(3)
        self.set_score(n2, 1, 800)
        n2[self.BOOST_LO0 + 1] = 80
        for _ in range(300):
            if n2[P2_STATE] == 1:
                break
            n2.step()
        self.clear_stage(n2)
        self.assertEqual(n2[self.WLEVEL0 + 1], 1)
        self.assertEqual(n2[self.BOOST_LO0 + 1], 0, 'progress to W3 starts at 0')
        self.assertEqual(n2[SYM['W2_OWNED'] + 1], 1)
        n2[self.BOOST_LO0 + 1] = 400 & 0xFF                # 4000 more: W3 with a 4800 total
        n2[self.BOOST_HI0 + 1] = 400 >> 8
        self.set_score(n2, 1, 4800)
        for _ in range(300):
            if n2[SUBSTATE] == 8:
                break
            n2.step()
        self.clear_stage(n2)
        self.assertEqual(n2[self.WLEVEL0 + 1], 2, 'W3 at a 4800 total')

    def test_persistent_w2(self):
        """A pilot who unlocked W2 comes back on W2 after a death (from W2, W3
        or W4); one who never did comes back on W1. W3 progress, no-death
        points and overdrive are reset; the score is kept."""
        n = self.coop_at_edges()
        for pilot in (0, 1):
            n[self.WLEVEL0 + pilot] = 1
            n[self.SHIELD0 + pilot] = 0
            self.kill(n, pilot)
            self.assertEqual(n[self.WLEVEL0 + pilot], 0, 'W2 never unlocked: W1')
            self.wait_back(n, pilot)
        n = self.coop_at_edges()
        for pilot in (0, 1):
            n[SYM['W2_OWNED'] + pilot] = 1                 # as after a stage-clear W2
            for level in (1, 2, 3):
                n[self.WLEVEL0 + pilot] = level
                n[self.BOOST_LO0 + pilot], n[self.NODEATH_LO0 + pilot] = 300 & 0xFF, 120
                n[SYM['W4_SEC'] + pilot] = 12 if level == 3 else 0
                sc = score(n, 0x117 if pilot == 0 else 0x129)
                n[self.SHIELD0 + pilot] = 0
                self.kill(n, pilot)
                n.step(2)
                self.assertEqual(n[self.WLEVEL0 + pilot], 1, f'W{level + 1} -> W2')
                self.assertEqual((n[self.BOOST_LO0 + pilot], n[self.NODEATH_LO0 + pilot]), (0, 0))
                self.assertEqual((n[SYM['W4_SEC'] + pilot], n[SYM['W4_USED'] + pilot]), (0, 0), 'overdrive off')
                self.assertGreaterEqual(score(n, 0x117 if pilot == 0 else 0x129), sc)
                self.wait_back(n, pilot)
                self.assertEqual(n[self.WLEVEL0 + pilot], 1, 'back on W2')
        st = n.save()                                      # after the death W3 needs 4000 again
        n[self.BOOST_LO0], n[self.BOOST_HI0] = 399 & 0xFF, 399 >> 8
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 1, '3990 points: still W2')
        n.load(st)
        n[self.BOOST_LO0], n[self.BOOST_HI0] = 400 & 0xFF, 400 >> 8
        self.clear_stage(n)
        self.assertEqual(n[self.WLEVEL0], 2, '4000 points: W3')

    def test_life_share_keeps_w2_rule(self):
        for owned, want in ((0, 0), (1, 1)):
            n = self.p2_out_p1_playing(p1_reserve=2)
            n[SYM['W2_OWNED'] + 1] = owned
            n[self.WLEVEL0 + 1] = 3                        # stale value must not survive
            self.press_select(n, p1=True)
            self.assertEqual(n[P2_STATE], 1)
            self.assertEqual(n[self.WLEVEL0 + 1], want, f'revived P2, W2 unlocked: {owned}')
            n = self.p1_out_p2_playing(p2_reserve=2)
            n[SYM['W2_OWNED']] = owned
            self.press_select(n, p2=True)
            self.assertEqual(n[P1_OUT], 0)
            self.assertEqual(n[self.WLEVEL0], want, f'revived P1, W2 unlocked: {owned}')

    def test_overdrive_lasts_30_seconds(self):
        """W4 for 1800 frames of normal play, the countdown on HUD row 2
        ("W4 30s" .. "W4 01s"), then W3 and the field blank; once per life."""
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        self.assertEqual(n[SYM['W4_SEC']], 30)
        n.step(8)
        self.assertEqual(self.status_row(n)[0], 'W4 30s')
        seen = set()
        played = 0
        while n[self.WLEVEL0] == 3 and played < 2000:
            played += self.play_frames(n, 1)
            if n[self.WLEVEL0] == 3:
                seen.add(n[SYM['W4_SEC']])
                shown = self.status_row(n)[0]
                self.assertIn(shown, ('W4 %02ds' % n[SYM['W4_SEC']], 'W4 %02ds' % (n[SYM['W4_SEC']] + 1)))
        self.assertEqual(n[self.WLEVEL0], 2, 'W3 after the overdrive')
        self.assertAlmostEqual(played + 8, 1800, delta=2)          # + the 8 frames before the loop
        self.assertEqual(seen, set(range(1, 31)))
        n.step(8)
        self.assertEqual(self.status_row(n)[0], '      ', 'countdown gone')
        self.assertEqual(self.status_row(n)[3][2:8], bytes([0x10] * 6))
        n[self.NODEATH_LO0], n[self.NODEATH_HI0] = 900 & 0xFF, 900 >> 8   # still >= 8000: no second W4
        self.calm_points(n, 0)
        self.assertEqual(n[self.WLEVEL0], 2, 'overdrive only once per life')
        self.kill(n, 0)                                    # a new life may use it again
        self.wait_back(n, 0)
        self.overdrive(n, 0)

    def test_overdrive_pause_and_stage_change(self):
        """Pause and the stage-change sequence don't use up overdrive time;
        the stage change doesn't renew it."""
        n = self.coop_at_edges()
        self.overdrive(n, 1)
        self.play_frames(n, 200)
        n.controller = pads(START); n.step(); n.controller = 0
        n.step(2)
        self.assertTrue(n[0x4E], 'paused')
        sec, frm = n[SYM['W4_SEC'] + 1], n[SYM['W4_FRM'] + 1]
        n.step(600)
        self.assertEqual((n[SYM['W4_SEC'] + 1], n[SYM['W4_FRM'] + 1]), (sec, frm), 'paused')
        n.controller = pads(START); n.step(); n.controller = 0
        n.step(3)
        sec = n[SYM['W4_SEC'] + 1]
        stage = n[0x59]
        for k in range(10):
            n[0xC3 + k] = 0
        for k in range(8):
            n[0x738 + k] = 0
        played = 0
        for _ in range(900):
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            n.step()
            played += n[SUBSTATE] == 8
            if n[0x59] != stage and n[SUBSTATE] == 8:
                break
        self.assertNotEqual(n[0x59], stage, 'next stage')
        left = n[SYM['W4_SEC'] + 1] * 60 + n[SYM['W4_FRM'] + 1]
        self.assertAlmostEqual(sec * 60 - left, played, delta=62, msg='only normal-play frames counted')
        self.assertLess(left, sec * 60 + 60, 'not renewed')
        self.assertEqual(n[self.WLEVEL0 + 1], 3)

    def test_overdrive_independent_pilots(self):
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        self.play_frames(n, 300)
        self.overdrive(n, 1)
        n.step(8)
        p1, stage, p2, _ = self.status_row(n)
        self.assertEqual(p2, 'W4 30s')
        self.assertIn(p1, ('W4 24s', 'W4 25s', 'W4 23s'))
        self.assertEqual(stage, 'STG 01')
        self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), (3, 3), 'both on W4')
        self.kill(n, 0)                                    # P1's death ends only P1's overdrive
        n.step(8)
        p1, _, p2, _ = self.status_row(n)
        self.assertEqual(p1, '      ')
        self.assertTrue(p2.startswith('W4 '))
        self.assertEqual(n[self.WLEVEL0 + 1], 3)

    def test_overdrive_shots_finish_their_flight(self):
        """Lasers flying when W4 ends keep their speed and look; new shots are
        W3 (3 slots), the 4th slot is not reused while its laser flies."""
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        n[SYM['W4_SEC']], n[SYM['W4_FRM']] = 1, 12
        for k in range(4):
            n[self.BUL_Y0 + k] = 0
        most = 0
        for i in range(40):                                # four lasers
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0)
            n.step()
            most = max(most, sum(1 for k in range(4) if n[self.BUL_Y0 + k]))
            if n[self.WLEVEL0] != 3:
                break
        n.controller = 0
        self.assertEqual(n[self.WLEVEL0], 2, 'W4 over')
        flying = [k for k in range(4) if n[self.BUL_Y0 + k]]
        self.assertTrue(flying)
        ys = {k: n[self.BUL_Y0 + k] for k in flying}
        n.step()
        for k in flying:
            if n[self.BUL_Y0 + k]:
                self.assertAlmostEqual(ys[k] - n[self.BUL_Y0 + k], 6.4, delta=0.7, msg='laser speed kept')
                oam = (0x280, 0x2BC, 0x2C0, 0x2C4)[k]
                self.assertEqual(n[oam + 1], 0x60, 'laser tile kept')
        most = 0
        for i in range(120):
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0)
            n.step()
            most = max(most, sum(1 for k in range(3) if n[self.BUL_Y0 + k]))
            self.assertTrue(n[self.BUL_Y0 + 3] == 0 or n[SYM['BUL_LV'] + 3] == 3, 'slot 4 only holds the old laser')
        n.controller = 0
        self.assertEqual(most, 3)

    def score_steps(self, n, frames, fire=(True, True)):
        """Score increments per pilot over `frames` frames of firing."""
        steps = ([], [])
        prev = [score(n, 0x117), score(n, 0x129)]
        for i in range(frames):
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            for k in range(7):                           # no enemy fire, shields: no death changes W4
                n[0x284 + 4 * k] = 0
            n[self.SHIELD0], n[self.SHIELD0 + 1] = 200, 200
            sweep = LEFT if (i // 200) % 2 else RIGHT      # find enemies above
            n.controller = pads((B if fire[0] and i % 4 < 2 else 0) | sweep,
                                (B if fire[1] and (i + 1) % 4 < 2 else 0) | sweep ^ (LEFT | RIGHT))
            n.step()
            for p, base in ((0, 0x117), (1, 0x129)):
                now = score(n, base)
                if now != prev[p]:
                    steps[p].append(now - prev[p])
                    prev[p] = now
        n.controller = 0
        return steps

    def test_double_score_in_overdrive(self):
        """x2 for the overdrive pilot's own kills only; the other pilot x1;
        back to x1 the moment W4 ends; the life-sharing bonus is never doubled."""
        double = {2 * p for p in self.BASE_POINTS}
        n = self.coop_at_edges()
        n[SHIP_X], n[P2_X] = 0xE0, 0x20                  # both under the formation
        self.overdrive(n, 0)
        n[SYM['W4_SEC']] = 30
        p1, p2 = self.score_steps(n, 1500)
        self.assertGreater(len(p1), 3)
        self.assertGreater(len(p2), 3)
        self.assertTrue(set(p1) <= double | {2 * 800 + 0}, f'P1 on W4: {sorted(set(p1))}')
        self.assertTrue(set(p2) <= self.BASE_POINTS, f'P2 on W1: {sorted(set(p2))}')
        self.overdrive(n, 1)                              # both on W4
        n[SYM['W4_SEC']], n[SYM['W4_SEC'] + 1] = 30, 30
        p1, p2 = self.score_steps(n, 1200)
        self.assertTrue(set(p1) <= double and set(p2) <= double, (sorted(set(p1)), sorted(set(p2))))
        n[SYM['W4_SEC']], n[SYM['W4_FRM']] = 1, 2          # P1's W4 ends: x1 at once
        n.step(3)
        self.assertEqual(n[self.WLEVEL0], 2)
        p1, _ = self.score_steps(n, 1200, fire=(True, False))
        self.assertTrue(p1 and set(p1) <= self.BASE_POINTS, sorted(set(p1)))
        # life-sharing bonus from a donor in overdrive: +200, not 400
        n = self.p2_out_p1_playing(p1_reserve=2)
        self.overdrive(n, 0)
        before = score(n, 0x117)
        self.press_select(n, p1=True)
        self.assertEqual(score(n, 0x117) - before, 200)

    def test_double_score_extra_life_and_hi_score(self):
        """Doubled points are real points: they reach the extra-life threshold
        (every 7000) and the hi score, shown correctly in the HUD."""
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        n[SYM['W4_SEC']] = 30
        self.set_score(n, 0, 6950)
        n[SYM['LASTK']] = 6
        n[LIVES1] = 2
        lives = expected_lives(n)[0]
        for k in range(6):
            n[0x120 + k] = 0x10 if k < 2 else (5 if k == 2 else 0)        # hi 5000
        gained = self.score_points(n, 0)
        self.assertIn(gained, {2 * p for p in self.BASE_POINTS})
        self.assertGreaterEqual(score(n, 0x117), 7000)
        self.assertEqual(expected_lives(n)[0], lives + 1, 'extra life at 7000')
        n.step(3)                                          # the copy follows in the next 2 frames
        self.assertEqual(score(n, 0x120), score(n, 0x117), 'hi score')
        self.assert_hud(n, 'after a doubled score')

    def test_new_game_clears_overdrive(self):
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        n[SYM['W2_OWNED']] = 1
        n[LIVES1], n[LIVES2] = 0, 0                        # lose the game
        for pilot in (0, 1):
            for _ in range(600):
                if self.alive(n, pilot):
                    break
                n.step()
            self.kill(n, pilot)
        for _ in range(60 * 60):
            n.step()
            if n[STATE] == 1:
                break
        self.assertEqual(n[STATE], 1)
        n.step(60)
        n2 = n
        for _ in range(60):
            if n2[STATE] == 3:
                break
            n2.controller = pads(START); n2.step(6); n2.controller = 0; n2.step(6)
        for _ in range(600):
            if n2[SUBSTATE] == 8:
                break
            n2.step()
        self.assertEqual([n2[SYM[k] + p] for k in ('W4_SEC', 'W4_USED', 'W2_OWNED') for p in (0, 1)], [0] * 6)
        self.assertEqual((n2[self.WLEVEL0], n2[self.WLEVEL0 + 1]), (0, 0))
        n2.step(10)
        self.assertEqual(self.status_row(n2)[0], '      ')

    # ------------------------------------------------------------ RC4: shots, colours
    def ship_centre(self, n, frame, pilot):
        """Centre column of a ship's visible pixels (rows 210-223)."""
        import numpy as np
        f = np.asarray(frame)[210:224].any(2).any(0)
        cols = np.nonzero(f)[0]
        x = ((n[SHIP_X] if pilot == 0 else n[P2_X]) + 0x80) & 0xFF
        near = [c for c in cols if abs(int(c) - x) <= 8]
        return (min(near) + max(near)) / 2 if near else None

    def attack_stats(self, n, frames, overdrive):
        """Play `frames` frames without firing, both pilots shielded (no hit
        ends the run); overdrive = (P1, P2) kept running or off. Returns dive
        launches, the divers' average y step per frame, the share of dive
        targets on P2's side (P1 left edge, P2 right edge) and enemy shots
        heading right."""
        launches, steps, moved, right, aims, shots_r, shots = 0, 0, 0, 0, 0, 0, 0
        prev = [n[0x738 + k] for k in range(8)]
        prev_y = [n[0x200 + 16 * k] for k in range(8)]
        prev_eb = [n[0x284 + 4 * k] for k in range(7)]
        eb_x, eb_age = [0] * 7, [None] * 7
        for i in range(frames):
            for p in (0, 1):
                n[self.WLEVEL0 + p] = 3 if overdrive[p] else 0
                n[SYM['W4_SEC'] + p] = 30 if overdrive[p] else 0
                n[self.SHIELD0 + p] = 200
            n[LIVES1], n[LIVES2] = 5, 5
            n.step()
            for k in range(7):
                st = n[0x738 + k]
                if st == 1 and prev[k] != 1:
                    launches += 1
                if st == 2 and prev[k] == 1:              # aimed (EE4E) this frame: heading right?
                    aims += 1
                    right += n[0x740 + k] > n[0x203 + 16 * k]
                if st in (2, 7) and prev[k] in (2, 7):
                    dy = (n[0x200 + 16 * k] - prev_y[k]) & 0xFF
                    if dy <= 3:
                        steps += dy
                        moved += 1
                prev[k] = st
                prev_y[k] = n[0x200 + 16 * k]
            for k in range(7):                           # enemy shots: x 24 frames after firing
                y = n[0x284 + 4 * k]
                if y and not prev_eb[k]:
                    eb_x[k], eb_age[k] = n[0x287 + 4 * k], 0
                elif y and eb_age[k] is not None:
                    eb_age[k] += 1
                    if eb_age[k] == 24:
                        shots += 1
                        shots_r += n[0x287 + 4 * k] > eb_x[k]
                        eb_age[k] = None
                if not y:
                    eb_age[k] = None
                prev_eb[k] = y
        return launches, steps / max(moved, 1), right / max(aims, 1), shots_r / max(shots, 1)

    def test_overdrive_aggression(self):
        """From the same moment: with P2 in overdrive the enemies start more
        dives, dive faster and go for P2 more often than without; with no
        overdrive running the new hooks change nothing (identical RAM), so
        nothing stays after an overdrive ends."""
        n = self.coop_at_edges()
        for _ in range(60 * 20):                           # attack level up a little ($65)
            for p in (0, 1):
                n[self.SHIELD0 + p] = 200
            n.step()
        st = n.save()
        off = self.attack_stats(n, 60 * 90, (False, False))
        ram_off = [n[a] for a in range(0x800)]
        n.load(st)
        off2 = self.attack_stats(n, 60 * 90, (False, False))
        self.assertEqual([n[a] for a in range(0x800)], ram_off, 'deterministic, hooks inert without overdrive')
        n.load(st)
        on = self.attack_stats(n, 60 * 90, (False, True))
        self.assertGreaterEqual(on[0], off[0] * 1.15, f'dive launches {off[0]} -> {on[0]}')
        self.assertGreater(on[1], off[1] * 1.08, f'dive speed {off[1]:.3f} -> {on[1]:.3f} px/frame')
        self.assertLess(on[1], off[1] * 1.2)
        self.assertGreater(on[2], off[2] + 0.12, f'dives at P2 {off[2]:.2f} -> {on[2]:.2f}')
        self.assertGreater(on[3], off[3] + 0.2, f'shots at P2 {off[3]:.2f} -> {on[3]:.2f}')
        self.assertEqual(off, off2)

    def test_stage_one_boost_natural(self):
        """Stage 1 played to its natural end (both pilots move and fire, lives
        kept up, the formation shot down by them): at the frame of the stage
        change (INC $59) each pilot that is in play gets W2 and one that is
        exploding or waiting for its next ship (lives kept up: a reserve ship
        is always coming) gets it too; nothing changes the
        weapons during the change to stage 2; HUD and RAM agree afterwards."""
        cases = set()
        for seed in (3, 4, 5, 14, 17):
            rnd = random.Random(seed)
            n = self.start(self.rom, two=True)
            tgt = [0, 0]
            for f in range(60 * 60 * 3):
                n[LIVES1], n[LIVES2] = max(n[LIVES1], 2), max(n[LIVES2], 2)
                if f % 30 == 0:
                    tgt = [rnd.randrange(0x96, 0x16A) & 0xFF for _ in range(2)]
                pad = [0, 0]
                for i, x in enumerate((n[SHIP_X], n[P2_X])):
                    d = ((tgt[i] - x + 128) & 0xFF) - 128
                    pad[i] = (RIGHT if d > 2 else LEFT if d < -2 else 0) | (B if (f + i) % 6 < 2 else 0)
                alive = (self.alive(n, 0), self.alive(n, 1))
                n.controller = pads(*pad)
                n.step()
                if n[0x59] == 1:
                    break
            self.assertEqual(n[0x59], 1, f'seed {seed}: stage 1 cleared')
            n.controller = 0
            w = (n[self.WLEVEL0], n[self.WLEVEL0 + 1])
            self.assertEqual(w, (1, 1), f'seed {seed}: in play {alive}, weapons {w}')
            cases.add(alive)
            for _ in range(900):
                n.step()
                self.assertEqual((n[self.WLEVEL0], n[self.WLEVEL0 + 1]), w, 'stage change keeps the weapons')
                if n[SUBSTATE] == 8 and n[P1_DEAD] == 0 and n[0x59] == 1:
                    break
            self.assert_hud(n, f'seed {seed} stage 2')
            self.assertEqual(self.status_row(n)[1], 'STG 02')
        self.assertIn((True, True), cases)

    def test_raster_split_below_formation(self):
        """The P1 ship split (scroll by P1's x, after PreSplit in the NMI's
        wait) still happens between the formation and the ship: two runs from
        the same moment that differ only in P1's x give identical pictures down
        to the ship's rows, with 8 lasers flying (PreSplit's longest work)."""
        import numpy as np
        n = self.coop_at_edges()
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        for i in range(24):
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0, B if i % 4 < 2 else 0)
            n.step()
        n.controller = 0
        self.calm(n)
        st = n.save()
        frames = []
        for x in (0xA0, 0x40):
            n.load(st)
            n[SHIP_X] = x
            self.calm(n)
            n.step()
            frames.append(np.asarray(n.step()).copy())
        diff = (frames[0] != frames[1]).any(2).any(1)
        rows = np.nonzero(diff)[0]
        self.assertTrue(len(rows), 'the ship moved')
        self.assertGreaterEqual(rows.min(), 200, f'first differing line {rows.min()}: the split is above the ship')
        self.assertTrue(diff[209] or diff[210], "the ship's first rows already follow its x (split not late)")
        self.assertGreaterEqual(sum(n[self.BUL_Y0 + k] > 0 for k in range(8)), 6, 'lasers in flight')

    def test_shots_centred_on_ships(self):
        """Every slot, W1 and W4, both pilots, at both edges and in the middle:
        the shot's x (RAM, used by the hit tests) + 4 is the ship's visible
        centre, and the rendered shot is centred on it."""
        import numpy as np
        drawn = 0
        for level in (0, 3):
            n = self.coop_at_edges()
            for pos in range(3):
                for pilot in (0, 1):
                    n[self.WLEVEL0 + pilot] = level
                    n[SYM['W4_SEC'] + pilot] = 30 if level == 3 else 0
                    if pos == 1:
                        n[SHIP_X if pilot == 0 else P2_X] = (0xE8 if pilot == 0 else 0x18)
                    if pos == 2:
                        n[SHIP_X if pilot == 0 else P2_X] = (0x6A if pilot == 0 else 0x96)
                    for k in range(8):
                        n[self.BUL_Y0 + k] = 0
                    self.calm(n)
                    n.step()                               # P1's split uses last frame's x
                    f = n.step()
                    centre = self.ship_centre(n, f, pilot)
                    self.assertIsNotNone(centre)
                    oam = (0x280, 0x2BC, 0x2C0, 0x2C4, 0x2B0, 0x2B4, 0x2B8, 0x2C8)
                    for i in range(14):                    # fire all slots of this level
                        self.calm(n)
                        n.controller = pads(B if i % 3 < 2 and pilot == 0 else 0,
                                            B if i % 3 < 2 and pilot == 1 else 0)
                        shown = [(n[oam[4 * pilot + k]], n[oam[4 * pilot + k] + 3]) for k in range(4)]
                        f = np.asarray(n.step())       # shows the OAM written before this step
                        for k in range(4):
                            s = 4 * pilot + k
                            y = n[self.BUL_Y0 + s]
                            if not y:
                                continue
                            self.assertEqual(n[0x0E + s] + 4, centre, f'P{pilot + 1} slot {k} x (RAM)')
                        for k in range(4):
                            oy, ox = shown[k]
                            if oy >= 0xC0 or oy < 0x30:
                                continue
                            mid = f[oy + 6, ox + 4]          # a pixel of the shot's centre column
                            self.assertTrue(mid.any(), f'P{pilot + 1} slot {k} drawn at x+4')
                            if f[oy + 6, ox + 1].any() or f[oy + 6, ox + 7].any():
                                continue                         # over an enemy or a star
                            lit = [(f[oy + 6, ox + 4 + d] == mid).all() for d in range(-3, 4)]
                            if sum(lit) != (3 if level == 3 else 1):
                                continue                         # another sprite touches it
                            self.assertEqual(lit, lit[::-1], f'P{pilot + 1} slot {k} symmetric about x+4: {lit}')
                            drawn += 1
                    n.controller = 0
                    flown = sum(n[SYM['BUL_LV'] + 4 * pilot + k] == level for k in range(4))
                    self.assertGreaterEqual(flown, 1)
        self.assertGreater(drawn, 40, 'rendered shots checked')

    def palette_ram(self, n):
        """The 32 palette bytes from the cynes save state (located by search)."""
        state = bytes(n.save())
        want = bytes.fromhex('0F16302C0F1611270F2311270F1A1127')
        i = state.find(want)
        self.assertGreaterEqual(i, 0, 'BG palette not found')
        return state[i:i + 32]

    def test_palette_only_one_colour_changed(self):
        """Only sprite palette 2 colour 3 changes ($27 -> $2A, RC4: $28); the
        rest of the palettes (BG, ships, enemies, HUD, badge) is the original's."""
        n = self.start(self.rom, two=True)
        pal = self.palette_ram(n)
        orig = bytes.fromhex('0F16302C0F1611270F2311270F1A11270F3011270F1611270F2311270F1A1127')
        diff = [i for i in range(32) if pal[i] != orig[i]
                and i not in (0x05, 0x10, 0x14, 0x18, 0x1C)]   # $3F05 set per frame; mirrors of BG colour 0
        self.assertEqual(diff, [0x1B])
        self.assertEqual(pal[0x1B], 0x2A)

    def test_stage_counter(self):
        """Co-op HUD row 2 shows the stage being played: 01 at the start, then
        02, 03; deaths and life sharing don't change it; two digits up to 99;
        a new game starts at 01; 1P keeps the original look (no counter)."""
        n = self.start(self.rom, two=True)
        n.step(10)
        self.assertEqual(self.status_row(n)[1], 'STG 01')
        for want in ('STG 02', 'STG 03'):
            self.clear_stage(n)
            for _ in range(600):
                if n[SUBSTATE] == 8:
                    break
                n.step()
            n.step(10)
            self.assertEqual(self.status_row(n)[1], want)
            self.assert_hud(n, want)
        n[LIVES1] = 3
        self.kill(n, 0)
        self.wait_back(n, 0)
        n.step(10)
        self.assertEqual(self.status_row(n)[1], 'STG 03', 'a death keeps the stage')
        n[0x59] = 98                                      # the game's last stage number
        n.step(10)
        self.assertEqual(self.status_row(n)[1], 'STG 99')
        self.clear_stage(n)                               # FC3B: after stage 99 the game restarts at 1
        for _ in range(600):
            if n[SUBSTATE] == 8:
                break
            n.step()
        n.step(10)
        self.assertEqual(self.status_row(n)[1], 'STG 01')
        row = self.status_row(n)[3]
        self.assertEqual(set(row[:13]) | set(row[19:]), {0x10}, 'nothing else on row 2')
        n = self.p2_out_p1_playing(p1_reserve=2)
        stage = self.status_row(n)[1]
        self.press_select(n, p1=True)
        n.step(10)
        self.assertEqual(self.status_row(n)[1], stage, 'life sharing keeps the stage')
        n = self.start(self.rom, two=False)               # 1P: original HUD, row 2 blank
        n.step(30)
        self.assertEqual(set(self.status_row(n)[3]), {0x10})

    # ------------------------------------------------------------ RC5: player visual identity
    # cynes RGB of the NES colours involved (measured in play)
    RGB = {0x30: (236, 238, 236), 0x16: (152, 34, 32), 0x2C: (56, 180, 204), 0x11: (8, 76, 196),
           0x27: (212, 136, 32), 0x2A: (76, 208, 32), 0x1A: (8, 124, 0), 0x23: (176, 98, 236)}
    ORIG_PALETTE = bytes.fromhex('0F16302C0F1611270F2311270F1A11270F3011270F1611270F2311270F1A1127')
    SCREENSHOTS = GAME / 'build' / 'screenshots'

    def screenshot(self, name, frame, scale=1):
        """Picture for a person to look at: build/screenshots/<name>.png (not in git)."""
        save_png(self.SCREENSHOTS / f'{name}.png', frame, scale)

    def shot_colour(self, pilot):
        return self.RGB[0x2A] if pilot == 0 else self.RGB[0x27]

    def ship_art(self, pilot):
        """A ship's 16 x 16 picture: RGB per pixel, None where transparent.
        P1: the original BG tiles in BG palette 0; P2: build.P2_PIXELS in
        sprite palette 0."""
        if pilot == 0:
            rows, pal = build.p1_ship(Path(self.rom).read_bytes()[-0x2000:]), (None, 0x16, 0x30, 0x2C)
        else:
            rows, pal = [['.123'.index(c) for c in r] for r in build.P2_PIXELS], (None, 0x30, 0x11, 0x27)
        return [[self.RGB[pal[v]] if v else None for v in r] for r in rows]

    @staticmethod
    def find_ship(frame, art, top, left, slack=2):
        """x where the frame shows exactly `art` (16 x 16 at row `top`), within
        `slack` px of `left`; transparent pixels black (a star may add 2)."""
        for dx in sorted(range(-slack, slack + 1), key=abs):
            x = left + dx
            if x < 0 or x + 16 > 256 or top + 16 > 240:
                continue
            box = frame[top:top + 16, x:x + 16]
            extra = 0
            ok = True
            for y in range(16):
                for c in range(16):
                    px = tuple(int(v) for v in box[y, c])
                    if art[y][c] is None:
                        extra += px != (0, 0, 0)
                    elif px != art[y][c]:
                        ok = False
                        break
                if not ok:
                    break
            if ok and extra <= 2:
                return x
        return None

    @staticmethod
    def ship_empty(frame, top, left):
        box = frame[top:top + 16, max(0, left - 2):left + 18]
        return int(box.any(2).sum()) <= 2

    def ship_place(self, n, pilot, oam):
        """(top, left) of the ship's picture for the frame about to be shown."""
        if pilot == 0:
            return 209, 120 + ((n[SHIP_X] + 128) & 0xFF) - 128
        if oam[0] >= 0xEF:                               # hidden (shield blink): where it would be
            return 209, ((n[P2_X] + 0x79) & 0xFF) - 1
        return oam[0] + 1, oam[3] - 1

    def test_ship_silhouettes(self):
        """RC5: two different, stable ship pictures, matched pixel by pixel
        while both ships move (screen edges included): P1 the original ship
        (BG tiles, BG palette 0: red dome, white pods, cyan core), P2 its own
        symmetric ship (delta nose, white cockpit, flat-topped pods, split fins;
        sprite palette 0: orange, blue, white). Same 13 x 16 box (columns 2-14)
        and centre column. Saves build/screenshots/ships.png."""
        import numpy as np
        arts = self.ship_art(0), self.ship_art(1)
        masks = [[[c is not None for c in r] for r in a] for a in arts]
        self.assertNotEqual(masks[0], masks[1], 'different silhouettes')
        diff = sum(a != b for ra, rb in zip(*masks) for a, b in zip(ra, rb))
        self.assertTrue(10 <= diff <= 60, f'{diff} px differ: recognisable, still the same kind of ship')
        for m in masks:
            self.assertEqual(build.bounding_box([[int(v) for v in r] for r in m]), (2, 14, 0, 15))
        n = self.coop_at_edges()
        matched, edges = [0, 0], [set(), set()]
        for i in range(260):
            self.calm(n)
            p1 = RIGHT if (i // 65) % 2 == 0 else LEFT
            n.controller = pads(p1, RIGHT if p1 == LEFT else LEFT)
            oam = [n[P2_OAM + k] for k in range(16)]
            places = [self.ship_place(n, p, oam) for p in (0, 1)]
            f = np.asarray(n.step())
            for p in (0, 1):
                x = self.find_ship(f, arts[p], *places[p])
                self.assertIsNotNone(x, f'P{p + 1} picture, frame {i}')
                matched[p] += 1
                edges[p].add(x)
        n.controller = 0
        self.assertEqual(matched, [260, 260])
        self.assertLessEqual(min(edges[0]), 20)
        self.assertGreaterEqual(max(edges[1]), 220)
        n[SHIP_X], n[P2_X] = 0xF0, 0x10                  # side by side for the screenshot
        self.calm(n)
        n.step()
        f = np.asarray(n.step())
        self.screenshot('ships', f[196:232, 88:168], 8)

    def test_p2_sprites_and_oam_use(self):
        """P2 is still 4 sprites at $02A0-$02AF (tiles $E1 top / $EA bottom, the
        right half H-flipped, 1 px overlap) at the same place relative to P2_X
        (hit tests use P2_X); with both pilots on W4 and 8 lasers no other OAM
        entry uses the ship tiles, shots only use their 8 slots and the stars
        keep their 13 sprites: no sprite added."""
        n = self.coop_at_edges()
        n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
        n[SYM['W4_SEC']], n[SYM['W4_SEC'] + 1] = 30, 30
        most = 0
        for i in range(120):
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0, B if i % 4 < 2 else 0)
            n.step()
            oam = [n[0x200 + k] for k in range(256)]
            y, x = oam[0xA0], oam[0xA3]
            self.assertEqual([oam[0xA1 + 4 * k] for k in range(4)], [0xE1, 0xE1, 0xEA, 0xEA])
            self.assertEqual([oam[0xA2 + 4 * k] & 0xC3 for k in range(4)], [0, 0x40, 0, 0x40])
            self.assertEqual([oam[0xA0 + 4 * k] for k in range(4)], [y, y, y + 8, y + 8])
            self.assertEqual([oam[0xA3 + 4 * k] for k in range(4)], [x, x + 7, x, x + 7])
            self.assertEqual(x, (n[P2_X] + 0x79) & 0xFF)
            self.assertEqual(y, 0xD0)
            ship = [a for a in range(0, 256, 4) if oam[a + 1] in (0xE1, 0xEA) and oam[a] < 0xEF]
            self.assertEqual(ship, [0xA0, 0xA4, 0xA8, 0xAC])
            shots = [0x200 + a for a in range(0, 256, 4) if oam[a] < 0xEF and oam[a + 1] in (0x30, 0x60)]
            self.assertTrue(set(shots) <= set(self.SHOT_OAM), [hex(a) for a in shots])
            most = max(most, len(shots))
            stars = [a for a in range(0xCC, 0x100, 4)]
            self.assertEqual(len(stars), 13)
            self.assertTrue(all(oam[a + 1] == 0x32 for a in stars if oam[a] < 0xEF))
        n.controller = 0
        self.assertEqual(most, 8, 'all 8 shot sprites in use')

    def test_ship_hitboxes_unchanged(self):
        """An enemy bullet coming down at P1 and at P2 from the same offsets
        (-12..12 px around the hit position used by kill()): both hit from the
        same offsets, which are the original's P1 box (11 px)."""
        n = self.coop_at_edges()
        self.calm(n)
        state = n.save()
        hits = ([], [])
        for pilot in (0, 1):
            for d in range(-12, 13):
                n.load(state)
                self.calm(n)
                x = n[SHIP_X] if pilot == 0 else n[P2_X]
                n[0x284], n[0x287] = 0xC4, (x + 0x7A + d) & 0xFF
                for _ in range(14):
                    n.step()
                    if not self.alive(n, pilot):
                        hits[pilot].append(d)
                        break
        n.load(state)
        self.assertEqual(hits[0], hits[1])
        self.assertEqual(hits[0], list(range(hits[0][0], hits[0][0] + 11)), hits[0])

    def shot_pixels(self, f, oam):
        """{slot: colour of its shot's middle column} for shots in mid screen."""
        out = {}
        for k, a in enumerate(self.SHOT_OAM):
            y, tile, attr, x = oam[a - 0x200:a - 0x200 + 4]
            if y < 0xEF and tile in (0x30, 0x60) and 0x30 <= y < 0xB8 and x < 248:
                out[k] = (tuple(int(v) for v in f[y + 6, x + 4]), attr & 3)
        return out

    def test_shot_colours(self):
        """RC5: P1 shots green (sprite palette 2, colour 3 = $2A), P2 orange
        (palette 0, colour 3 = $27) on W1-W4 in all 8 slots, both pilots firing
        in the same frames and alternately (no mixing); P1's green is not the
        green aliens' ($1A) nor the white of enemy bullets. Same after a death
        and after a revive by Life Sharing. Picture and OAM. (RC4: yellow $28.)"""
        import numpy as np
        green, orange = self.shot_colour(0), self.shot_colour(1)
        self.assertNotEqual(green, self.RGB[0x1A])
        self.assertTrue(green[1] > green[0] + 100 and green[1] > green[2] + 100, 'P1: bright green')
        self.assertTrue(orange[0] > orange[1] > orange[2] + 60, 'P2: orange')
        n = self.coop_at_edges()
        slots = [set() for _ in range(8)]
        for level in (0, 1, 2, 3):
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = level, level
            n[SYM['W4_SEC']], n[SYM['W4_SEC'] + 1] = (30, 30) if level == 3 else (0, 0)
            for together in (True, False):
                for i in range(70):
                    self.calm(n)
                    b2 = i if together else i + 2
                    n.controller = pads(B if i % 4 < 2 else 0, B if b2 % 4 < 2 else 0)
                    oam = [n[0x200 + k] for k in range(256)]
                    f = np.asarray(n.step())
                    for k, (rgb, pal) in self.shot_pixels(f, oam).items():
                        self.assertEqual(pal, 2 if k < 4 else 0, f'slot {k} palette')
                        self.assertEqual(rgb, green if k < 4 else orange, f'slot {k} W{level + 1} colour')
                        slots[k].add(level)
        n.controller = 0
        self.assertEqual([sorted(s) for s in slots],
                         [[0, 1, 2, 3], [1, 2, 3], [2, 3], [3]] * 2, 'every slot seen on every level it is used')

        def fire_and_check(n, pilot, what):
            seen = False
            for i in range(40):
                self.calm(n)
                n.controller = pads(B if pilot == 0 and i % 4 < 2 else 0, B if pilot == 1 and i % 4 < 2 else 0)
                oam = [n[0x200 + k] for k in range(256)]
                f = np.asarray(n.step())
                for k, (rgb, pal) in self.shot_pixels(f, oam).items():
                    self.assertEqual(rgb, green if k < 4 else orange, f'{what}: slot {k}')
                    seen |= k // 4 == pilot
            n.controller = 0
            self.assertTrue(seen, f'{what}: shot seen')

        for pilot in (0, 1):                             # after a death and the respawn
            self.kill(n, pilot)
            self.wait_back(n, pilot)
            fire_and_check(n, pilot, f'P{pilot + 1} after a death')
        n = self.p1_out_p2_playing(p2_reserve=2)         # revived P1
        self.press_select(n, p2=True)
        fire_and_check(n, 0, 'P1 revived')
        n = self.p2_out_p1_playing(p1_reserve=2)         # revived P2
        self.press_select(n, p1=True)
        fire_and_check(n, 1, 'P2 revived')

    def test_laser_shape_and_colours(self):
        """W4 lasers (tile $60, both pilots firing): every laser drawn alone in
        mid screen is exactly the 3 x 8 laser of build.LASER_PIXELS (centre
        column 4) in its pilot's colour. Saves build/screenshots/w4_w4.png (both
        pilots in overdrive, enemies attacking, shields on)."""
        import numpy as np
        mask = np.array([[c != '.' for c in r] for r in build.LASER_PIXELS])
        n = self.coop_at_edges()
        for p in (0, 1):
            n[self.WLEVEL0 + p], n[SYM['W4_SEC'] + p] = 3, 30
        checked = [0, 0]
        for i in range(160):
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0, B if (i + 1) % 4 < 2 else 0)
            oam = [n[0x200 + k] for k in range(256)]
            f = np.asarray(n.step())
            for k, a in enumerate(self.SHOT_OAM):
                y, tile, attr, x = oam[a - 0x200:a - 0x200 + 4]
                if tile != 0x60 or not 0x30 <= y < 0xB8 or x >= 248:
                    continue
                box = f[y + 1:y + 9, x:x + 8]
                lit = box.any(2)
                if (lit & ~mask).any():
                    continue                             # a star next to it
                self.assertTrue((lit == mask).all(), f'slot {k} laser shape')
                cols = {tuple(int(v) for v in box[r, c]) for r, c in zip(*np.nonzero(mask))}
                self.assertEqual(cols, {self.shot_colour(k // 4)}, f'slot {k} laser colour')
                checked[k // 4] += 1
        n.controller = 0
        self.assertTrue(min(checked) >= 30, checked)
        n = self.start(self.rom, two=True)               # a real scene for the screenshot
        rnd = random.Random(2)
        best, frame = -1, None
        for i in range(1500):
            for p in (0, 1):                             # (no shield: a shielded ship blinks)
                n[self.WLEVEL0 + p], n[SYM['W4_SEC'] + p] = 3, 30
                n[LIVES1 + p] = max(n[LIVES1 + p], 3)
            if i % 20 == 0:
                hold = [rnd.choice([0, LEFT, RIGHT]) for _ in (0, 1)]
            n.controller = pads(hold[0] | (B if i % 4 < 2 else 0), hold[1] | (B if (i + 1) % 4 < 2 else 0))
            f = n.step()
            if i > 300 and n[SUBSTATE] == 8 and n[P1_DEAD] == 0 and n[P2_STATE] == 1 and n[self.SHIELD0] == 0 \
                    and n[self.SHIELD0 + 1] == 0:
                score_ = sum(n[self.BUL_Y0 + k] > 0x40 for k in range(8)) + sum(n[0x738 + k] in (2, 7) for k in range(8))
                if score_ > best:
                    best, frame = score_, np.asarray(f).copy()
        n.controller = 0
        self.assertIsNotNone(frame, 'a frame with both ships in play')
        self.screenshot('w4_w4', frame, 3)

    def test_enemy_colours_unchanged(self):
        """Enemy sprites (divers of all three colours, flagships, explosions,
        enemy bullets: OAM $0200-$029F without P1's shot) drawn in natural play:
        every opaque pixel not overlapped by another sprite shows the original
        palette colour, except colour 3 of sprite palette 2 (2 px of a diving
        purple alien), now $2A instead of $27 (RC4: $28)."""
        import numpy as np
        chr_data = Path(self.rom).read_bytes()[-0x2000:]
        tiles = {}
        def pixels(t):
            if t not in tiles:
                tiles[t] = np.array(build.tile_pixels(chr_data, 0, t))
            return tiles[t]
        checked = {}
        rnd = random.Random(1)
        n = self.start(self.rom, two=True)
        for i in range(3000):
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 2), max(n[LIVES2], 2)
            n[self.SHIELD0], n[self.SHIELD0 + 1] = 200, 200
            if i % 20 == 0:
                hold = [rnd.choice([0, LEFT, RIGHT]) for _ in (0, 1)]
            n.controller = pads(hold[0] | (B if i % 6 < 2 else 0), hold[1] | (B if (i + 3) % 6 < 2 else 0))
            oam = [n[0x200 + k] for k in range(256)]
            f = np.asarray(n.step())
            if i % 3:
                continue
            boxes = [(oam[a], oam[a + 3]) for a in range(0, 256, 4) if oam[a] < 0xEF]
            for a in range(0, 0xA0, 4):
                y, t, attr, x = oam[a:a + 4]
                if a == 0x80 or y >= 0xC8 or x > 248 or y < 0x10 or attr & 0x20:
                    continue
                if sum(1 for by, bx in boxes if abs(by - y) < 8 and abs(bx - x) < 8) > 1:
                    continue                             # overlapped by another sprite
                before = [oam[b] for b in range(0, a, 4) if oam[b] < 0xEF]
                if any(sum(1 for by in before if by <= y + r < by + 8) >= 8 for r in range(8)):
                    continue                             # dropped on a line (8 sprites per line)
                px = pixels(t)
                if attr & 0x40:
                    px = px[:, ::-1]
                if attr & 0x80:
                    px = px[::-1]
                pal = attr & 3
                for r, c in zip(*np.nonzero(px)):
                    v = int(px[r, c])
                    want = 0x2A if (pal, v) == (2, 3) else self.ORIG_PALETTE[0x10 + 4 * pal + v]
                    got = tuple(int(q) for q in f[y + 1 + r, x + c])
                    self.assertEqual(got, self.RGB[want], f'tile {t:02X} palette {pal} colour {v} frame {i}')
                    checked[(pal, v)] = checked.get((pal, v), 0) + 1
        n.controller = 0
        for key in ((1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3), (0, 1)):
            self.assertGreater(checked.get(key, 0), 0, f'palette {key[0]} colour {key[1]} seen')

    def test_shield_blink_silhouettes(self):
        """Respawn shield (4 s blink) with the RC5 ships: in every frame each
        ship is either its exact picture or not drawn at all (no stray tiles,
        no mixed picture); afterwards both stay exactly as before; P1's
        nametable rows and P2's sprites are as before the death."""
        import numpy as np
        arts = self.ship_art(0), self.ship_art(1)
        for pilot in (0, 1):
            n = self.coop_at_edges()
            nt0 = nametable(n)[26 * 32:28 * 32]
            n = self.respawned(pilot)
            shown = hidden = 0
            for i in range(300):
                self.calm(n)
                oam = [n[P2_OAM + k] for k in range(16)]
                places = [self.ship_place(n, p, oam) for p in (0, 1)]
                sh = n[self.SHIELD0 + pilot]
                f = np.asarray(n.step())
                x = self.find_ship(f, arts[pilot], *places[pilot])
                if x is None:
                    self.assertTrue(self.ship_empty(f, *places[pilot]), f'P{pilot + 1} frame {i}: partly drawn')
                    hidden += 1
                else:
                    shown += 1
                self.assertIsNotNone(self.find_ship(f, arts[1 - pilot], *places[1 - pilot]), 'partner')
                if sh == 0:
                    break
            self.assertGreater(hidden, 60)
            self.assertGreater(shown, 60)
            for i in range(60):
                self.calm(n)
                oam = [n[P2_OAM + k] for k in range(16)]
                places = [self.ship_place(n, p, oam) for p in (0, 1)]
                f = np.asarray(n.step())
                for p in (0, 1):
                    self.assertIsNotNone(self.find_ship(f, arts[p], *places[p]), f'P{p + 1} after the shield')
            self.assertEqual(nametable(n)[26 * 32:28 * 32], nt0, 'P1 ship rows')

    def test_hud_in_overdrive(self):
        """Both pilots in overdrive (started by points, as in play): HUD scores,
        lives and weapon fields, the status row (countdowns, stage) read back
        from RAM and from the picture, also while lasers fly through the HUD."""
        g = glyphs(Path(self.rom).read_bytes())
        n = self.coop_at_edges()
        self.overdrive(n, 0)
        self.overdrive(n, 1)
        n.step(30)
        self.assert_hud(n, 'W4/W4')
        self.assert_hud_pixels(n, g, 'W4/W4')
        t1, stage, t2, _ = self.status_row(n)
        self.assertRegex(t1, r'^W4 [0-3][0-9]s$')
        self.assertRegex(t2, r'^W4 [0-3][0-9]s$')
        self.assertEqual(stage, 'STG 01')
        for i in range(64):                              # shots fly through the HUD rows
            self.calm(n)
            n.controller = pads(B if i % 4 < 2 else 0, B if i % 4 < 2 else 0)
            n.step()
            if i % 16 == 15:
                n.controller = 0
                self.assert_hud_pixels(n, g, f'W4/W4 firing, frame {i}')
        n.controller = 0
        self.assert_hud(n, 'W4/W4 after firing')

    def test_w4_stress_no_overrun(self):
        """Both pilots on W4 firing all the time (lives kept up), RC4: with the
        overdrive kept running (timer, x2 scoring, enemy aggression): no frame
        overrun, no lag frame."""
        rnd = random.Random(3)
        n = self.start(self.rom, two=True)
        prev = idle_counter(n)
        worst = 1 << 16
        lag = n[SYM['LAG_TOTAL']]                        # NMIs that overlapped
        for i in range(60 * 60 * 2):
            n[self.WLEVEL0], n[self.WLEVEL0 + 1] = 3, 3
            n[SYM['W4_SEC']], n[SYM['W4_SEC'] + 1] = 30, 30
            n[LIVES1], n[LIVES2] = max(n[LIVES1], 3), max(n[LIVES2], 3)
            fire = B if (i // 3) % 2 == 0 else 0
            n.controller = pads(fire | rnd.choice([0, LEFT, RIGHT]), fire | rnd.choice([0, LEFT, RIGHT]))
            state = n[STATE]
            n.step()
            self.assertFalse(state == 3 and n[STATE] in (0, 1), 'NMI overrun reset the game')
            cur = idle_counter(n)
            if n[STATE] == 3:
                worst = min(worst, (cur - prev) & 0xFFFF)
            prev = cur
        self.assertGreater(worst, 0)
        self.assertEqual(n[SYM['LAG_TOTAL']], lag, 'no lag frames')

    def test_stress_no_crash_or_overrun(self):
        rnd = random.Random(7)
        n = self.start(self.rom, two=True)
        prev = idle_counter(n)
        worst = 1 << 16
        c = 0
        for i in range(60 * 60 * 3):
            if i % 6 == 0:
                c = pads(rnd.choice([0, A, A | LEFT, A | RIGHT, LEFT, RIGHT]),
                         rnd.choice([0, A, A | LEFT, A | RIGHT, LEFT, RIGHT]))
            n.controller = c
            n.step()
            cur = idle_counter(n)
            if n[STATE] == 3 and n[SUBSTATE] == 8:
                worst = min(worst, (cur - prev) & 0xFFFF)
            prev = cur
        self.assertFalse(n.has_crashed)
        self.assertGreater(worst, 100, 'NMI handler close to overrunning the frame')


if __name__ == '__main__':
    unittest.main()
