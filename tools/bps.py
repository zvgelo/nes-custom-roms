#!/usr/bin/env python3
"""BPS patch creation / application (byuu's beat format).

The encoder uses SourceCopy for any data found in the source ROM and
TargetCopy for byte runs, so the patch carries only new bytes and never
the original game's data.

    python3 tools/bps.py create source.nes target.nes out.bps
    python3 tools/bps.py apply  source.nes patch.bps  out.nes
"""
import sys
import zlib

SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY = range(4)
MIN_MATCH = 8


def _enc(n):
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _dec(buf, pos):
    data, shift = 0, 1
    while True:
        x = buf[pos]
        pos += 1
        data += (x & 0x7F) * shift
        if x & 0x80:
            return data, pos
        shift <<= 7
        data += shift


def _signed(n):
    return _enc((abs(n) << 1) | (n < 0))


def create_bps(source, target):
    source, target = bytes(source), bytes(target)
    index = {}
    for i in range(len(source) - MIN_MATCH + 1):
        index.setdefault(source[i:i + MIN_MATCH], []).append(i)

    out = bytearray(b'BPS1' + _enc(len(source)) + _enc(len(target)) + _enc(0))
    src_rel = tgt_rel = 0
    literal = bytearray()
    pos = 0

    def flush():
        nonlocal literal
        if literal:
            out.extend(_enc(((len(literal) - 1) << 2) | TARGET_READ))
            out.extend(literal)
            literal = bytearray()

    while pos < len(target):
        best_len, best_src = 0, 0
        for cand in index.get(target[pos:pos + MIN_MATCH], ()):
            n = 0
            while pos + n < len(target) and cand + n < len(source) and source[cand + n] == target[pos + n]:
                n += 1
            if n > best_len:
                best_len, best_src = n, cand
        run = 1
        while pos + run < len(target) and target[pos + run] == target[pos]:
            run += 1
        if best_len >= MIN_MATCH and best_len >= run:
            flush()
            if best_src == pos:
                out.extend(_enc(((best_len - 1) << 2) | SOURCE_READ))
            else:
                out.extend(_enc(((best_len - 1) << 2) | SOURCE_COPY))
                out.extend(_signed(best_src - src_rel))
                src_rel = best_src + best_len
            pos += best_len
        elif run >= MIN_MATCH:
            literal.append(target[pos])  # one literal, then copy it forward
            flush()
            out.extend(_enc(((run - 2) << 2) | TARGET_COPY))
            out.extend(_signed(pos - tgt_rel))
            tgt_rel = pos + run - 1
            pos += run
        else:
            literal.append(target[pos])
            pos += 1
    flush()
    out += zlib.crc32(source).to_bytes(4, 'little') + zlib.crc32(target).to_bytes(4, 'little')
    out += zlib.crc32(out).to_bytes(4, 'little')
    patch = bytes(out)
    assert apply_bps(source, patch) == target
    return patch


def apply_bps(source, patch):
    if patch[:4] != b'BPS1':
        raise ValueError('not a BPS patch')
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], 'little'):
        raise ValueError('patch CRC mismatch')
    if zlib.crc32(source) != int.from_bytes(patch[-12:-8], 'little'):
        raise ValueError('source ROM CRC mismatch')
    pos = 4
    src_size, pos = _dec(patch, pos)
    tgt_size, pos = _dec(patch, pos)
    meta, pos = _dec(patch, pos)
    pos += meta
    if src_size != len(source):
        raise ValueError('source size mismatch')
    target = bytearray()
    src_rel = tgt_rel = 0
    end = len(patch) - 12
    while pos < end:
        data, pos = _dec(patch, pos)
        cmd, length = data & 3, (data >> 2) + 1
        if cmd == SOURCE_READ:
            target += source[len(target):len(target) + length]
        elif cmd == TARGET_READ:
            target += patch[pos:pos + length]
            pos += length
        else:
            off, pos = _dec(patch, pos)
            off = -(off >> 1) if off & 1 else off >> 1
            if cmd == SOURCE_COPY:
                src_rel += off
                target += source[src_rel:src_rel + length]
                src_rel += length
            else:
                tgt_rel += off
                for _ in range(length):
                    target.append(target[tgt_rel])
                    tgt_rel += 1
    if len(target) != tgt_size or zlib.crc32(target) != int.from_bytes(patch[-8:-4], 'little'):
        raise ValueError('target CRC mismatch')
    return bytes(target)


def main(argv):
    if len(argv) != 5 or argv[1] not in ('create', 'apply'):
        raise SystemExit(__doc__)
    a, b = open(argv[2], 'rb').read(), open(argv[3], 'rb').read()
    result = create_bps(a, b) if argv[1] == 'create' else apply_bps(a, b)
    open(argv[4], 'wb').write(result)
    print(f'wrote {argv[4]} ({len(result)} bytes)')


if __name__ == '__main__':
    main(sys.argv)
