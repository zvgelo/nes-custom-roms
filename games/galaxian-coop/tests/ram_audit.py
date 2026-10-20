#!/usr/bin/env python3
"""RAM audit: which RAM the original program (or the mod) uses while running.

    python3 games/galaxian-coop/tests/ram_audit.py [--rom ROM] [--runs 8] [--frames 100000] [--write]

Runs the ROM in tools/trace6502.py (title, demo, 1P and 2P games with random
play, game over, end screen; one process per run) and records every RAM
address read or written by code at $E000-$FFFF, without the reset-time
clear/copy loops. With --write the result for the original ROM replaces
src/original_ram.txt, which build.py uses to refuse new variables there.

For the mod ROM it also lists the mod's variables (coop.asm) that original
code touches at run time: only P1_BLOCK (read by the two patched P1 hit
checks) is expected.
"""
import argparse
import multiprocessing
import random
import sys
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parents[1] / 'tools'), str(GAME / 'src')]
import build  # noqa: E402
from trace6502 import CPU  # noqa: E402

# reset-time loops: RAM clear, CHR -> RAM copies, HUD buffer / score row fills, OAM clear
INIT_PCS = {0xE032, 0xE034, 0xE037, 0xE03A, 0xE058, 0xE0C6, 0xE0D6, 0xE0FA, 0xE072, 0xE19B, 0xF756}
A, B, SEL, START, LEFT, RIGHT = 0x80, 0x40, 0x20, 0x10, 0x02, 0x01


def run(args):
    rom, frames, seed = args
    rnd = random.Random(seed)
    c = CPU(Path(rom).read_bytes())
    games, plan, hold = 0, [], [0, 0]
    for _ in range(frames):
        st, sub = c.ram[0xFF], c.ram[0xFE]
        if plan:
            c.pads = list(plan.pop(0))
        elif st == 1 and sub >= 2 and rnd.random() < 0.02:
            if games % 3 == 2 and rnd.random() < 0.5:
                plan = [(0, 0)] * 900                    # let the demo start
            else:
                for _ in range(12):
                    if (c.ram[0x31] & 1) != games % 2:
                        plan += [(SEL, 0)] * 6 + [(0, 0)] * 6
                plan += [(START, 0)] * 6 + [(0, 0)] * 6
                games += 1
        elif st == 3:
            for i in (0, 1):
                if rnd.random() < 0.08:
                    hold[i] = rnd.choice([0, LEFT, RIGHT, LEFT, RIGHT, 0])
            fire = [B if rnd.random() < 0.35 else 0, A if rnd.random() < 0.35 else 0]
            extra = [0, 0]
            if rnd.random() < 0.003:
                extra[0] = START                         # pause
            if rnd.random() < 0.004:
                extra[rnd.randrange(2)] |= SEL           # life sharing
            c.pads = [hold[0] | fire[0] | extra[0], hold[1] | fire[1] | extra[1]]
        else:
            c.pads = [0, 0]
        c.run_frame()
    used = {a for a in range(0x800)
            if any(p >= 0xE000 and p not in INIT_PCS for p in c.ram_r.get(a, ()) | c.ram_w.get(a, ()))}
    return used, games


def ranges(addrs):
    out, start, prev = [], None, None
    for a in sorted(addrs):
        if start is None or a != prev + 1:
            if start is not None:
                out.append((start, prev))
            start = a
        prev = a
    if start is not None:
        out.append((start, prev))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rom', default=str(build.DEFAULT_ROM))
    ap.add_argument('--runs', type=int, default=8)
    ap.add_argument('--frames', type=int, default=100000)
    ap.add_argument('--write', action='store_true', help='rewrite src/original_ram.txt')
    a = ap.parse_args()
    from nestest import ines_compatible
    rom = ines_compatible(a.rom)                         # NES 2.0 8 KiB PRG -> iNES 16 KiB
    with multiprocessing.Pool(a.runs) as pool:
        results = pool.map(run, [(rom, a.frames, s) for s in range(a.runs)])
    used = set().union(*(r[0] for r in results)) | set(range(0x200, 0x300))   # OAM page whole
    print(f'{sum(r[1] for r in results)} games, {len(used)} RAM bytes used by original code')
    lines = [f'{s:04X}-{e:04X}' if s != e else f'{s:04X}' for s, e in ranges(used)]
    print(' '.join(lines))
    from asm6502 import Assembler
    asm = Assembler()
    build.assemble(asm)
    for name, size in build.RAM_SIZES.items():
        hit = [x for x in range(asm.symbols[name], asm.symbols[name] + size) if x in used]
        if hit:
            print(f'  mod variable {name} at {", ".join(f"${x:04X}" for x in hit)} touched by original code')
    if a.write:
        head = (GAME / 'src' / 'original_ram.txt').read_text().split('\n\n')[0]
        (GAME / 'src' / 'original_ram.txt').write_text(head + '\n\n' + '\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
