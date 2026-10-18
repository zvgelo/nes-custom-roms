#!/usr/bin/env python3
"""VCDIFF (RFC 3284) decoder for xdelta3 patches, pure Python.

Supports the default code table, VCD_SOURCE/VCD_TARGET windows, the xdelta3
application header and Adler-32 window checksums. Patches that use
secondary compression or a custom code table are rejected with
`Unsupported`; use the `xdelta3` binary for those.

    python3 tools/vcdiff.py source patch.xdelta out
"""
import sys
import zlib


class Unsupported(Exception):
    pass


RUN, ADD, COPY = 1, 2, 3
NEAR, SAME = 4, 3


def _default_table():
    t = [((RUN, 0, 0), (0, 0, 0))]
    t += [((ADD, s, 0), (0, 0, 0)) for s in range(18)]
    for mode in range(9):
        t += [((COPY, s, mode), (0, 0, 0)) for s in (0, *range(4, 19))]
    for mode in range(6):
        t += [((ADD, a, 0), (COPY, c, mode)) for a in range(1, 5) for c in range(4, 7)]
    for mode in range(6, 9):
        t += [((ADD, a, 0), (COPY, 4, mode)) for a in range(1, 5)]
    t += [((COPY, 4, mode), (ADD, 1, 0)) for mode in range(9)]
    assert len(t) == 256
    return t


TABLE = _default_table()


class _Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def byte(self):
        b = self.data[self.pos]
        self.pos += 1
        return b

    def varint(self):
        v = 0
        while True:
            b = self.byte()
            v = (v << 7) | (b & 0x7F)
            if not b & 0x80:
                return v

    def take(self, n):
        out = self.data[self.pos:self.pos + n]
        if len(out) != n:
            raise ValueError('truncated patch')
        self.pos += n
        return out


def _adler32(data):
    return zlib.adler32(data) & 0xFFFFFFFF


def decode(source, patch):
    r = _Reader(patch)
    if r.take(3) != b'\xd6\xc3\xc4' or r.byte() != 0:
        raise ValueError('not a VCDIFF v0 file')
    hdr = r.byte()
    if hdr & 0x01:
        raise Unsupported('secondary compression')
    if hdr & 0x02:
        raise Unsupported('custom code table')
    if hdr & 0x04:
        r.take(r.varint())  # xdelta3 application header (file names)
    out = bytearray()
    while r.pos < len(patch):
        win = r.byte()
        seg_len = seg_pos = 0
        if win & 0x03:
            seg_len, seg_pos = r.varint(), r.varint()
            if win & 0x01:
                segment = source[seg_pos:seg_pos + seg_len]
            else:
                segment = bytes(out[seg_pos:seg_pos + seg_len])
            if len(segment) != seg_len:
                raise ValueError('source segment out of range')
        else:
            segment = b''
        r.varint()  # length of the delta encoding
        tgt_len = r.varint()
        if r.byte():
            raise Unsupported('compressed delta sections')
        data_len, inst_len, addr_len = r.varint(), r.varint(), r.varint()
        checksum = int.from_bytes(r.take(4), 'big') if win & 0x04 else None
        data = _Reader(r.take(data_len))
        inst = _Reader(r.take(inst_len))
        addr = _Reader(r.take(addr_len))

        target = bytearray()
        near, near_slot, same = [0] * NEAR, 0, [0] * (SAME * 256)
        while inst.pos < inst_len:
            for kind, size, mode in TABLE[inst.byte()]:
                if not kind:
                    continue
                if size == 0:
                    size = inst.varint()
                if kind == ADD:
                    target += data.take(size)
                elif kind == RUN:
                    target += bytes([data.byte()]) * size
                else:
                    here = seg_len + len(target)
                    if mode == 0:
                        a = addr.varint()
                    elif mode == 1:
                        a = here - addr.varint()
                    elif mode < 2 + NEAR:
                        a = near[mode - 2] + addr.varint()
                    else:
                        a = same[(mode - 2 - NEAR) * 256 + addr.byte()]
                    near[near_slot] = a
                    near_slot = (near_slot + 1) % NEAR
                    same[a % (SAME * 256)] = a
                    for i in range(size):  # byte-wise: copies may overlap
                        p = a + i
                        target.append(segment[p] if p < seg_len else target[p - seg_len])
        if len(target) != tgt_len:
            raise ValueError('target window size mismatch')
        if checksum is not None and _adler32(target) != checksum:
            raise ValueError('window Adler-32 mismatch')
        out += target
    return bytes(out)


def main(argv):
    if len(argv) != 4:
        raise SystemExit(__doc__)
    src = open(argv[1], 'rb').read()
    patch = open(argv[2], 'rb').read()
    out = decode(src, patch)
    open(argv[3], 'wb').write(out)
    print(f'wrote {argv[3]} ({len(out)} bytes)')


if __name__ == '__main__':
    main(sys.argv)
