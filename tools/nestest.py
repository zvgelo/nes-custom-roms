"""Headless emulator helpers for ROM tests (requires `pip install cynes numpy`).

cynes does not read the NES 2.0 exponent size notation used by some 8 KiB
PRG dumps; `ines_compatible()` rewrites such a ROM as an equivalent
iNES image (8 KiB PRG mirrored to 16 KiB) for testing only.
"""
import tempfile
from pathlib import Path

try:
    from cynes import NES
except ImportError:  # tests skip themselves when the emulator is missing
    NES = None

RIGHT, LEFT, DOWN, UP, START, SELECT, B, A = (1 << i for i in range(8))


def ines_compatible(path):
    data = Path(path).read_bytes()
    if data[9] & 0x0F != 0x0F:
        return str(path)
    prg = data[16:16 + 0x2000]
    out = b'NES\x1a\x01\x01\x00\x00' + bytes(8) + prg + prg + data[16 + 0x2000:]
    tmp = tempfile.NamedTemporaryFile(suffix='.nes', delete=False)
    tmp.write(out)
    tmp.close()
    return tmp.name


def pads(p1=0, p2=0):
    return p1 | p2 << 8


def ram(nes, addr, length=1):
    return bytes(nes[addr + i] for i in range(length))
