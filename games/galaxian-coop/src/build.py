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
from asm6502 import Assembler  # noqa: E402

ORIG_SHA256 = '1188cedf84657769f19daef474d9a20e7c2d16f9c5c5998d5baab59f74f3613e'
DEFAULT_ROM = GAME / 'rom' / 'Galaxian (Japan).nes'
DEFAULT_OUT = GAME / 'build' / 'Galaxian_Coop_stage2.nes'
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
SHIP_BG_TILES = (0x62, 0x60, 0x63, 0x61)  # BG table: TL, TR, BL, BR
# BG colour index -> sprite colour index (sprite palette 0 = $30,$11,$27)
SHIP_COLOR_MAP = {0: 0, 1: 3, 2: 2, 3: 1}


def tile_pixels(chr_data, table, idx):
    b = chr_data[table * 0x1000 + idx * 16:][:16]
    return [[((b[y] >> (7 - x)) & 1) | (((b[y + 8] >> (7 - x)) & 1) << 1) for x in range(8)]
            for y in range(8)]


def encode_tile(rows):
    lo = bytes(sum((p & 1) << (7 - x) for x, p in enumerate(r)) for r in rows)
    hi = bytes(sum((p >> 1) << (7 - x) for x, p in enumerate(r)) for r in rows)
    return lo + hi


def build_p2_tiles(chr_data):
    tl, tr, bl, br = (tile_pixels(chr_data, 1, t) for t in SHIP_BG_TILES)
    ship = [tl[y] + tr[y] for y in range(8)] + [bl[y] + br[y] for y in range(8)]
    for row in ship:  # symmetric about column 8, so the left half + H-flip rebuilds it
        assert row[0] == 0 and all(row[8 - k] == row[8 + k] for k in range(1, 8)), 'ship not symmetric'
    half = [[SHIP_COLOR_MAP[p] for p in row[1:9]] for row in ship]
    return encode_tile(half[:8]), encode_tile(half[8:])


def patch_chr(chr_data):
    chr_data = bytearray(chr_data)
    for off, old in LOGO_CELLS.items():
        assert chr_data[off] == old, f'CHR ${off:04X}: expected {old:02X}'
        chr_data[off] = 0x10
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
           'P2_TIMER', 'P2_FIRE', 'P2_BY', 'P2_BX', 'SAVE_BY', 'SAVE_BX', 'T0', 'T1', 'AIM_TOGGLE')


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
    rom = Path(rom_path).read_bytes()
    if hashlib.sha256(rom).hexdigest() != ORIG_SHA256:
        raise SystemExit('input is not Galaxian (Japan) [SHA-256 mismatch]')
    header, prg, chr_data = rom[:16], rom[16:16 + PRG_ORIG], rom[16 + PRG_ORIG:]
    assert header[:4] == b'NES\x1a' and (header[7] & 0x0C) == 0x08, 'expected NES 2.0 header'
    assert len(chr_data) == CHR_SIZE

    asm = Assembler()
    segments = assemble(asm)
    new_prg = patch_prg(prg, segments)
    new_chr = patch_chr(chr_data)

    hdr = bytearray(header)
    hdr[4] = PRG_NEW // 0x4000   # 2 x 16 KiB
    hdr[9] = 0x00                # plain size notation, PRG/CHR MSB = 0
    out = bytes(hdr) + new_prg + new_chr
    assert len(out) == 16 + PRG_NEW + CHR_SIZE
    assert out[16 + PRG_NEW - 6:16 + PRG_NEW] == prg[-6:], 'vectors moved'

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    out_path.with_suffix('.mlb').write_text(mesen_labels(asm))
    code_end = max(s.org + len(s.data) for s in segments if s.org < 0xE000)
    print(f'Saved:  {out_path}')
    print(f'Size:   {len(out)} bytes, new code $8000-${code_end - 1:04X} ({code_end - 0x8000} bytes)')
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
    build(a.rom, a.out, a.bps)


if __name__ == '__main__':
    main()
