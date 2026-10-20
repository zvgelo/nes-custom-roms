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


def save_png(path, frame, scale=1):
    """Write an RGB frame (H x W x 3, uint8; a cynes frame or a crop of one)
    as a PNG, each pixel enlarged to scale x scale. No image library needed."""
    import struct
    import zlib
    import numpy as np
    img = np.ascontiguousarray(np.asarray(frame, dtype=np.uint8)[:, :, :3])
    img = img.repeat(scale, 0).repeat(scale, 1)
    h, w = img.shape[:2]
    raw = b''.join(b'\x00' + img[y].tobytes() for y in range(h))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
