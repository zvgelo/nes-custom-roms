#!/usr/bin/env python3
"""Build Galaxian Coop from the original Galaxian (Japan) ROM.

    python3 games/galaxian-coop/src/build.py [path/to/Galaxian (Japan).nes] [-o out.nes] [--bps]

The original ROM is only read. Output goes to games/galaxian-coop/build/.
"""
import argparse
import hashlib
import sys
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from asm6502 import Assembler, AsmError  # noqa: E402

ORIG_SHA256 = '1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e'
DEFAULT_ROM = GAME / 'private' / 'Galaxian (Japan).nes'
DEFAULT_OUT = GAME / 'build' / 'Galaxian_Coop.nes'
ASM = GAME / 'src' / 'asm' / 'coop.asm'

PRG_ORIG = 0x2000      # 8 KiB, mapped at $E000-$FFFF
PRG_NEW = 0x8000       # 32 KiB, $8000-$FFFF
CHR_SIZE = 0x2000

# Title logo nametable data lives in CHR (copied to RAM $0300 at reset).
# Tiles $E1/$EA of the sprite table are blank logo cells; the logo row
# string 0E references them at CHR $155F and $1568. Pointing those cells
# at tile $10 (also blank) frees $E1/$EA for the P2 ship.
LOGO_CELLS = {0x155F: 0xE1, 0x1568: 0xEA}
P2_TILES = (0xE1, 0xEA)                 # top half, bottom half
SHIP_BG_TILES = (0x62, 0x60, 0x63, 0x61)  # BG table: TL, TR, BL, BR (P1's ship)
# P2's own ship (RC5; RC1-RC4: a copy of P1's): the same 13 x 16 box, centre
# column 8 and twin pods, with a swept delta nose and white cockpit instead
# of the round dome, flat-topped pods and split tail fins. Sprite palette 0:
# 1 = white $30, 2 = blue $11, 3 = orange $27. Drawn as the left half
# (columns 1-8) twice, the right one H-flipped, so it must be symmetric.
P2_PIXELS = ['........3.......',
             '.......333......',
             '......33333.....',
             '.....3313133....',
             '....33.131.33...',
             '...2...131...2..',
             '..222..131..222.',
             '..212..131..212.',
             '..212.11311.212.',
             '..2121113111212.',
             '..2111113111112.',
             '..2121.131.1212.',
             '..212.11.11.212.',
             '..212.......212.',
             '..222.......222.',
             '..2.2.......2.2.']
# W4 laser: sprite tile $60 (never shown by the original: no code uses it
# as a tile, unseen in title/attract/demo/play, outside the CHR ranges the
# reset code copies to RAM). One colour (3) so each pilot's palette gives
# it the pilot's colour (P1 palette 2 = green, P2 palette 0 = orange). Its
# centre column is 4, like the bullet tile $30 (RC1-RC3: column 3, 1 px left
# of the ship's centre and of the x the hit tests use).
LASER_TILE = 0x60
LASER_ORIG = bytes.fromhex('60000c006a0009003a003000c9000907')
LASER_PIXELS = ['....3...',
                '...333..',
                '...333..',
                '...333..',
                '...333..',
                '...333..',
                '...333..',
                '....3...']

# Lower-case "s" for the overdrive countdown ("W4 30s", HUD row 2): background
# tile $36 of table $1000 (a one-dot tile). No nametable of the game uses it
# (traced runs of title, demo, 1P/2P games, game over, end screen: tile
# values written to $2000 and $2800). Colour 1, like the font's letters.
SECONDS_TILE = 0x36
SECONDS_ORIG = bytes.fromhex('00 00 00 00 08 00 00 00 00 00 00 00 08 00 00 00')
SECONDS_PIXELS = ['........',
                  '........',
                  '........',
                  '..11111.',
                  '.11.....',
                  '..1111..',
                  '.....11.',
                  '.11111..']


def tile_pixels(chr_data, table, idx):
    b = chr_data[table * 0x1000 + idx * 16:][:16]
    return [[((b[y] >> (7 - x)) & 1) | (((b[y + 8] >> (7 - x)) & 1) << 1) for x in range(8)]
            for y in range(8)]


def encode_tile(rows):
    lo = bytes(sum((p & 1) << (7 - x) for x, p in enumerate(r)) for r in rows)
    hi = bytes(sum((p >> 1) << (7 - x) for x, p in enumerate(r)) for r in rows)
    return lo + hi


def p1_ship(chr_data):
    """P1's ship (BG tiles) as 16 rows of 16 colour indices."""
    tl, tr, bl, br = (tile_pixels(chr_data, 1, t) for t in SHIP_BG_TILES)
    return [tl[y] + tr[y] for y in range(8)] + [bl[y] + br[y] for y in range(8)]


def bounding_box(ship):
    cols = [x for row in ship for x, p in enumerate(row) if p]
    rows = [y for y, row in enumerate(ship) if any(row)]
    return min(cols), max(cols), min(rows), max(rows)


def build_p2_tiles(chr_data):
    ship = [['.123'.index(c) for c in row] for row in P2_PIXELS]
    for row in ship:  # symmetric about column 8, so the left half + H-flip rebuilds it
        assert len(row) == 16 and row[0] == 0 and all(row[8 - k] == row[8 + k] for k in range(1, 8)), \
            'P2 ship not symmetric'
    assert bounding_box(ship) == bounding_box(p1_ship(chr_data)), 'P2 ship size differs from P1'
    half = [row[1:9] for row in ship]
    return encode_tile(half[:8]), encode_tile(half[8:])


def patch_chr(chr_data):
    chr_data = bytearray(chr_data)
    for off, old in LOGO_CELLS.items():
        assert chr_data[off] == old, f'CHR ${off:04X}: expected {old:02X}'
        chr_data[off] = 0x10
    off = LASER_TILE * 16
    assert chr_data[off:off + 16] == LASER_ORIG, 'sprite tile $60 is not the expected original'
    chr_data[off:off + 16] = encode_tile([['.123'.index(c) for c in row] for row in LASER_PIXELS])
    off = 0x1000 + SECONDS_TILE * 16
    assert chr_data[off:off + 16] == SECONDS_ORIG, 'BG tile $36 is not the expected original'
    chr_data[off:off + 16] = encode_tile([['.123'.index(c) for c in row] for row in SECONDS_PIXELS])
    top, bot = build_p2_tiles(chr_data)
    for tile, data in zip(P2_TILES, (top, bot)):
        off = tile * 16
        assert not any(chr_data[off:off + 16]), f'sprite tile ${tile:02X} is not empty'
        chr_data[off:off + 16] = data
    return bytes(chr_data)


def assemble(asm=None):
    return (asm or Assembler()).assemble(ASM.read_text())


# RAM names exported to the Mesen label file (constants in coop.asm)
MLB_RAM = ('PAD1', 'PAD2', 'SHIP_X', 'P1_DEAD', 'STATE', 'SUBSTATE', 'CUR_PLAYER', 'LIVES1',
           'LIVES2', 'BONUS1', 'BONUS2', 'COOP', 'P1_OUT', 'P1_BLOCK', 'P2_STATE', 'P2_X',
           'P2_TIMER', 'FIRE_CNT', 'T2', 'CUR_SLOT', 'CUR_PL', 'T0', 'T1', 'AIM_TOGGLE',
           'P1_GRANTED', 'TITLE_STEP', 'P1_REDRAW', 'BUL_Y', 'BUL_X', 'BUL_F', 'WLEVEL',
           'BOOST_LO', 'BOOST_HI', 'NEXT_LIFE_LO', 'NEXT_LIFE_HI', 'STAGE1_DONE', 'NODEATH_LO',
           'NODEATH_HI', 'DCOUNT', 'BANNER_CUR', 'BANNER_ROW', 'W4_TIMER', 'W4_WHO', 'DI',
           'DLIST', 'HIT_DONE', 'SHOT_N', 'LOGIC_RAN', 'LASTK', 'LAG_COUNT', 'LAG_TOTAL', 'SHIELD', 'SCORE_NEW',
           'W2_OWNED', 'W4_USED', 'W4_SEC', 'W4_FRM', 'BUL_LV', 'STG_SHOWN', 'TMR_SHOWN', 'BY_SHOT', 'OD_SND')


# new RAM: name -> size; build fails if two of them overlap
RAM_SIZES = {'COOP': 1, 'P1_OUT': 1, 'P1_BLOCK': 1, 'P2_STATE': 1, 'P2_X': 1, 'P2_TIMER': 1,
             'FIRE_CNT': 2, 'T2': 1, 'CUR_SLOT': 1, 'CUR_PL': 1, 'T0': 1, 'T1': 1, 'AIM_TOGGLE': 1,
             'P1_GRANTED': 1, 'TITLE_STEP': 1, 'P1_REDRAW': 1, 'BUL_Y': 8, 'BUL_X': 8,
             'STAGE1_DONE': 1, 'WLEVEL': 2, 'NODEATH_LO': 2, 'NODEATH_HI': 2, 'DCOUNT': 1,
             'BANNER_CUR': 1, 'BANNER_ROW': 1, 'W4_TIMER': 1, 'W4_WHO': 1, 'BOOST_LO': 2,
             'BOOST_HI': 2, 'DI': 1, 'NEXT_LIFE_LO': 2, 'NEXT_LIFE_HI': 2, 'BUL_F': 8, 'DLIST': 7,
             'HIT_DONE': 1, 'SHOT_N': 1, 'LOGIC_RAN': 1, 'LASTK': 2, 'LAG_COUNT': 1, 'SHIELD': 2, 'SCORE_NEW': 1,
             'PS_MASK2': 1, 'LAG_TOTAL': 1, 'OD_SND': 1, 'W2_OWNED': 2, 'W4_USED': 2, 'W4_SEC': 2,
             'W4_FRM': 2, 'BUL_LV': 8, 'STG_SHOWN': 1, 'TMR_SHOWN': 2, 'BY_SHOT': 1, 'DIVE_CELL': 7, 'DIVE_RR': 1}


# Zero-page addresses the original program reads or writes directly (from the
# full disassembly). None of the new variables may use them.
ORIGINAL_ZP = {int(a, 16) for a in """
    00 01 02 03 04 23 24 27 28 29 2A 2B 2C 2D 2E 2F 30 31 32 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F
    40 41 42 43 44 4C 4E 4F 50 51 53 54 57 58 59 5A 5B 63 64 65 66 67 68 6B 6C 6D 6E 6F 70 71 72 76
    79 7E 80 81 8E 8F 90 91 92 9C 9D 9E 9F C0 C1 C2 C3 C7 CD D7 D8 DA DB DC DD DE DF E0 E1 E2 E3 E4
    E5 E8 E9 EA EB EC ED EE EF F0 F1 F2 F6 F7 FA FB FD FE FF""".split()}


def original_ram():
    """RAM the original program uses at run time (src/original_ram.txt, from
    traced runs) plus the stack $0130-$014D."""
    used = set(range(0x130, 0x14E))
    for line in (GAME / 'src' / 'original_ram.txt').read_text().splitlines():
        line = line.split('#')[0].strip()
        if line:
            a, _, b = line.partition('-')
            used |= set(range(int(a, 16), int(b or a, 16) + 1))
    return used


def check_ram(asm):
    traced = original_ram()
    used = {}
    for name, size in RAM_SIZES.items():
        base = asm.symbols[name]
        for a in range(base, base + size):
            if a in used:
                raise SystemExit(f'RAM overlap at ${a:04X}: {used[a]} and {name}')
            used[a] = name
            if a in ORIGINAL_ZP:
                raise SystemExit(f'{name} uses ${a:02X}, which the original game uses')
            if a in traced:
                raise SystemExit(f'{name} uses ${a:04X}, which the original game uses at run time')
    # PreSplit is cycle-counted: its code and its tables each stay in one page
    for start, end in (('PreSplit', 'PreSplitCodeEnd'), ('PreSplitTables', 'PreSplitEnd')):
        if asm.symbols[start] >> 8 != (asm.symbols[end] - 1) >> 8:
            raise SystemExit(f'{start} crosses a page boundary')


def check_segments(segments):
    """No two blocks of new code may overlap (a grown routine running into
    the next .org block would be silently overwritten)."""
    spans = sorted((seg.org, seg.org + len(seg.data)) for seg in segments if seg.org < 0xE000 and seg.data)
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        if b0 < a1:
            raise SystemExit(f'code blocks overlap: ${a0:04X}-${a1 - 1:04X} and ${b0:04X}')


def mesen_labels(asm):
    """Mesen 2 .mlb label file (PRG ROM offsets, internal RAM addresses)."""
    lines = [f'NesPrgRom:{asm.symbols[n] - 0x8000:04X}:{n}' for n in sorted(asm.labels, key=asm.symbols.get)]
    lines += [f'NesInternalRam:{asm.symbols[n]:04X}:{n}' for n in MLB_RAM]
    return '\n'.join(lines) + '\n'


def patch_prg(orig_prg, segments):
    prg = bytearray([0xFF]) * (PRG_NEW - PRG_ORIG) + bytearray(orig_prg)
    used = set()
    for seg in segments:
        start, end = seg.org, seg.org + len(seg.data)
        if not (0x8000 <= start and end <= 0x10000):
            raise SystemExit(f'segment ${start:04X} outside PRG')
        if start >= 0xE000 or end > 0xE000:
            if seg.expect is None:
                raise SystemExit(f'segment ${start:04X} writes original code without .patch')
            have = bytes(prg[start - 0x8000:end - 0x8000])
            if have != seg.expect:
                raise SystemExit(f'.patch ${start:04X}: original bytes {have.hex(" ")} != {seg.expect.hex(" ")}')
        span = set(range(start, end))
        if span & used:
            raise SystemExit(f'segment ${start:04X} overlaps another segment')
        used |= span
        prg[start - 0x8000:end - 0x8000] = seg.data
    return bytes(prg)


def build(rom_path, out_path, bps=False):
    rom_path, out_path = Path(rom_path), Path(out_path)
    if not rom_path.is_file():
        raise SystemExit(f'original ROM not found: {rom_path}\n'
                         f'copy your Galaxian (Japan).nes there (see README)')
    if out_path.resolve() == rom_path.resolve():
        raise SystemExit('refusing to overwrite the original ROM')
    rom = rom_path.read_bytes()
    if hashlib.sha256(rom).hexdigest() != ORIG_SHA256:
        raise SystemExit('input is not Galaxian (Japan) [SHA-256 mismatch]')
    header, prg, chr_data = rom[:16], rom[16:16 + PRG_ORIG], rom[16 + PRG_ORIG:]
    assert header[:4] == b'NES\x1a' and (header[7] & 0x0C) == 0x08, 'expected NES 2.0 header'
    assert len(chr_data) == CHR_SIZE

    asm = Assembler()
    segments = assemble(asm)
    check_ram(asm)
    check_segments(segments)
    new_prg = patch_prg(prg, segments)
    new_chr = patch_chr(chr_data)

    hdr = bytearray(header)
    hdr[4] = PRG_NEW // 0x4000   # 2 x 16 KiB
    hdr[9] = 0x00                # plain size notation, PRG/CHR MSB = 0
    out = bytes(hdr) + new_prg + new_chr
    assert len(out) == 16 + PRG_NEW + CHR_SIZE
    assert out[16 + PRG_NEW - 6:16 + PRG_NEW] == prg[-6:], 'vectors moved'

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    out_path.with_suffix('.mlb').write_text(mesen_labels(asm))
    new_code = sum(len(s.data) for s in segments if s.org < 0xE000)
    patched = sum(len(s.data) for s in segments if s.org >= 0xE000)
    print(f'Saved:  {out_path}')
    print(f'Size:   {len(out)} bytes; new code {new_code} bytes, {patched} bytes patched in $E000-$FFFF')
    print(f'SHA256: {hashlib.sha256(out).hexdigest()}')
    if bps:
        from bps import create_bps
        patch_path = GAME / 'patches' / (out_path.stem + '.bps')
        patch_path.write_bytes(create_bps(rom, out))
        print(f'BPS:    {patch_path}')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('rom', nargs='?', default=DEFAULT_ROM)
    ap.add_argument('-o', '--out', default=DEFAULT_OUT)
    ap.add_argument('--bps', action='store_true', help='also write a BPS patch to patches/')
    a = ap.parse_args()
    try:
        build(a.rom, a.out, a.bps)
    except AsmError as e:
        raise SystemExit(f'assembler: {e}')


if __name__ == '__main__':
    main()
