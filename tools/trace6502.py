"""Minimal NES CPU tracer (NROM) for audits that need to see every access.

A 6502 core (official opcodes), NMI every 29781 CPU cycles, a PPU stub that
keeps nametable and palette RAM ($2006/$2007, CHR reads buffered as on the
PPU) and reports vblank on every $2002 read, two pads from a script. No
rendering, no APU emulation, timing only per instruction (no page-crossing
cycles), so it is not a cycle-exact emulator; use it for "who touches what":

- every RAM access: address -> set of instruction PCs (ram_r, ram_w);
- every nametable/attribute write: VRAM address -> set of PCs (vram_w);
- APU register writes with frame number and PC (apu, when apu_log is set).
"""
from collections import defaultdict

FLAG_C, FLAG_Z, FLAG_I, FLAG_D, FLAG_B, FLAG_U, FLAG_V, FLAG_N = 1, 2, 4, 8, 16, 32, 64, 128


class CPU:
    def __init__(self, rom):
        prg = rom[16:16 + 0x4000 * rom[4]]
        if len(prg) == 0x2000:
            prg = prg * 4
        elif len(prg) == 0x4000:
            prg = prg * 2
        self.prg = prg
        self.chr = rom[16 + 0x4000 * rom[4]:][:0x2000]
        self.ppu_buf = 0
        self.ram = bytearray(0x800)
        self.vram = bytearray(0x1000)
        self.palette = bytearray(0x20)
        self.frame = 0
        self.apu_log = False
        self.apu = []           # (frame, register, value, pc)
        self.ppu_addr = 0
        self.ppu_latch = 0
        self.ppu_ctrl = 0
        self.pads = [0, 0]
        self.shift = [0, 0]
        self.strobe = 0
        self.a = self.x = self.y = 0
        self.s = 0xFD
        self.p = FLAG_I | FLAG_U
        self.pc = self.read16(0xFFFC)
        self.cycles = 0
        self.ram_r = defaultdict(set)
        self.ram_w = defaultdict(set)
        self.vram_w = defaultdict(set)
        self.cur = 0
        self.log = True
        self.on_write = None

    # ------------------------------------------------------------ bus
    def read(self, a):
        if a < 0x2000:
            a &= 0x7FF
            if self.log:
                self.ram_r[a].add(self.cur)
            return self.ram[a]
        if a < 0x4000:
            r = a & 7
            if r == 2:
                self.ppu_latch = 0
                return 0xC0
            if r == 7:                  # buffered read: returns the previous byte
                pa = self.ppu_addr
                v = self.ppu_buf
                self.ppu_buf = self.chr[pa] if pa < 0x2000 else self.vram[pa & 0xFFF]
                self.ppu_addr = (pa + (32 if self.ppu_ctrl & 4 else 1)) & 0x3FFF
                return v
            return 0
        if a == 0x4016 or a == 0x4017:
            i = a - 0x4016
            if self.strobe:
                return self.pads[i] >> 7 & 1 | 0x40
            v = self.shift[i] >> 7 & 1
            self.shift[i] = (self.shift[i] << 1 | 1) & 0xFF
            return v | 0x40
        if a >= 0x8000:
            return self.prg[a - 0x8000]
        return 0

    def write(self, a, v):
        if a < 0x2000:
            a &= 0x7FF
            if self.log:
                self.ram_w[a].add(self.cur)
            self.ram[a] = v
            if self.on_write:
                self.on_write(a, v)
            return
        if a < 0x4000:
            r = a & 7
            if r == 0:
                self.ppu_ctrl = v
            elif r == 6:
                if self.ppu_latch == 0:
                    self.ppu_addr = (v << 8 | self.ppu_addr & 0xFF) & 0x3FFF
                else:
                    self.ppu_addr = self.ppu_addr & 0xFF00 | v
                self.ppu_latch ^= 1
            elif r == 7:
                pa = self.ppu_addr
                if pa >= 0x3F00:
                    i = pa & 0x1F
                    self.palette[i & 0x0F if i & 3 == 0 else i] = v
                elif pa >= 0x2000:
                    self.vram[pa & 0xFFF] = v
                    if self.log:
                        self.vram_w[pa & 0xFFF].add(self.cur)
                self.ppu_addr = (pa + (32 if self.ppu_ctrl & 4 else 1)) & 0x3FFF
            elif r == 5:
                self.ppu_latch ^= 1
            return
        if self.apu_log and 0x4000 <= a <= 0x4017 and a != 0x4014 and a != 0x4016:
            self.apu.append((self.frame, a, v, self.cur))
        if a == 0x4014:
            self.cycles += 513
            return
        if a == 0x4016:
            self.strobe = v & 1
            if self.strobe:
                self.shift = list(self.pads)
            return

    def read16(self, a):
        return self.read(a) | self.read(a + 1) << 8

    def push(self, v):
        self.write(0x100 | self.s, v)
        self.s = (self.s - 1) & 0xFF

    def pull(self):
        self.s = (self.s + 1) & 0xFF
        return self.read(0x100 | self.s)

    def nmi(self):
        self.cur = 0xFFFA
        self.push(self.pc >> 8)
        self.push(self.pc & 0xFF)
        self.push(self.p & ~FLAG_B | FLAG_U)
        self.p |= FLAG_I
        self.pc = self.read16(0xFFFA)
        self.cycles += 7

    # ------------------------------------------------------------ flags
    def nz(self, v):
        self.p = self.p & 0x7D | (v & 0x80) | (0 if v else 2)
        return v

    def run_frame(self, cycles=29781):
        end = self.cycles + cycles
        ops = OPS
        while self.cycles < end:
            pc = self.pc
            self.cur = pc
            op = self.prg[pc - 0x8000] if pc >= 0x8000 else self.read(pc)
            fn, mode, cyc = ops[op]
            self.pc = (pc + 1) & 0xFFFF
            fn(self, mode)
            self.cycles += cyc
        self.frame += 1
        self.nmi()


# ---------------------------------------------------------------- addressing
def ea(c, mode):
    pc = c.pc
    if mode == 'imm':
        c.pc = pc + 1
        return pc
    if mode == 'zp':
        c.pc = pc + 1
        return c.prg[pc - 0x8000]
    if mode == 'zpx':
        c.pc = pc + 1
        return (c.prg[pc - 0x8000] + c.x) & 0xFF
    if mode == 'zpy':
        c.pc = pc + 1
        return (c.prg[pc - 0x8000] + c.y) & 0xFF
    if mode == 'abs':
        c.pc = pc + 2
        return c.prg[pc - 0x8000] | c.prg[pc - 0x7FFF] << 8
    if mode == 'abx':
        c.pc = pc + 2
        return ((c.prg[pc - 0x8000] | c.prg[pc - 0x7FFF] << 8) + c.x) & 0xFFFF
    if mode == 'aby':
        c.pc = pc + 2
        return ((c.prg[pc - 0x8000] | c.prg[pc - 0x7FFF] << 8) + c.y) & 0xFFFF
    if mode == 'izx':
        c.pc = pc + 1
        z = (c.prg[pc - 0x8000] + c.x) & 0xFF
        return c.read(z) | c.read((z + 1) & 0xFF) << 8
    if mode == 'izy':
        c.pc = pc + 1
        z = c.prg[pc - 0x8000]
        return ((c.read(z) | c.read((z + 1) & 0xFF) << 8) + c.y) & 0xFFFF
    raise ValueError(mode)


def val(c, mode):
    if mode == 'acc':
        return c.a
    return c.read(ea(c, mode))


def adc_(c, v):
    s = c.a + v + (c.p & 1)
    c.p = c.p & ~(FLAG_C | FLAG_V) | (1 if s > 0xFF else 0) | (FLAG_V if (~(c.a ^ v) & (c.a ^ s) & 0x80) else 0)
    c.a = c.nz(s & 0xFF)


def op_adc(c, m): adc_(c, val(c, m))
def op_sbc(c, m): adc_(c, val(c, m) ^ 0xFF)
def op_and(c, m): c.a = c.nz(c.a & val(c, m))
def op_ora(c, m): c.a = c.nz(c.a | val(c, m))
def op_eor(c, m): c.a = c.nz(c.a ^ val(c, m))
def op_lda(c, m): c.a = c.nz(val(c, m))
def op_ldx(c, m): c.x = c.nz(val(c, m))
def op_ldy(c, m): c.y = c.nz(val(c, m))
def op_sta(c, m): c.write(ea(c, m), c.a)
def op_stx(c, m): c.write(ea(c, m), c.x)
def op_sty(c, m): c.write(ea(c, m), c.y)


def cmp_(c, r, v):
    d = r - v
    c.p = c.p & 0x7C | (1 if d >= 0 else 0) | (d & 0x80) | (2 if d == 0 else 0)


def op_cmp(c, m): cmp_(c, c.a, val(c, m))
def op_cpx(c, m): cmp_(c, c.x, val(c, m))
def op_cpy(c, m): cmp_(c, c.y, val(c, m))


def op_bit(c, m):
    v = val(c, m)
    c.p = c.p & 0x3D | (v & 0xC0) | (0 if c.a & v else 2)


def rmw(fn):
    def op(c, m):
        if m == 'acc':
            c.a = fn(c, c.a)
        else:
            a = ea(c, m)
            c.write(a, fn(c, c.read(a)))
    return op


def _asl(c, v):
    c.p = c.p & ~1 | v >> 7
    return c.nz(v << 1 & 0xFF)


def _lsr(c, v):
    c.p = c.p & ~1 | v & 1
    return c.nz(v >> 1)


def _rol(c, v):
    r = (v << 1 | c.p & 1) & 0xFF
    c.p = c.p & ~1 | v >> 7
    return c.nz(r)


def _ror(c, v):
    r = v >> 1 | (c.p & 1) << 7
    c.p = c.p & ~1 | v & 1
    return c.nz(r)


def _inc(c, v): return c.nz((v + 1) & 0xFF)
def _dec(c, v): return c.nz((v - 1) & 0xFF)


def branch(flag, want):
    def op(c, m):
        off = c.prg[c.pc - 0x8000]
        c.pc += 1
        if bool(c.p & flag) == want:
            c.pc = (c.pc + (off - 256 if off > 127 else off)) & 0xFFFF
            c.cycles += 1
    return op


def op_jmp(c, m):
    c.pc = ea(c, 'abs')


def op_jmpi(c, m):
    a = ea(c, 'abs')
    c.pc = c.read(a) | c.read(a & 0xFF00 | (a + 1) & 0xFF) << 8


def op_jsr(c, m):
    t = ea(c, 'abs')
    r = (c.pc - 1) & 0xFFFF
    c.push(r >> 8)
    c.push(r & 0xFF)
    c.pc = t


def op_rts(c, m):
    lo = c.pull()
    c.pc = ((c.pull() << 8 | lo) + 1) & 0xFFFF


def op_rti(c, m):
    c.p = c.pull() | FLAG_U
    lo = c.pull()
    c.pc = c.pull() << 8 | lo


def op_brk(c, m):
    c.pc += 1
    c.push(c.pc >> 8)
    c.push(c.pc & 0xFF)
    c.push(c.p | FLAG_B | FLAG_U)
    c.p |= FLAG_I
    c.pc = c.read16(0xFFFE)


def simple(fn):
    def op(c, m):
        fn(c)
    return op


def _tax(c): c.x = c.nz(c.a)
def _tay(c): c.y = c.nz(c.a)
def _txa(c): c.a = c.nz(c.x)
def _tya(c): c.a = c.nz(c.y)
def _tsx(c): c.x = c.nz(c.s)
def _txs(c): c.s = c.x
def _inx(c): c.x = c.nz((c.x + 1) & 0xFF)
def _iny(c): c.y = c.nz((c.y + 1) & 0xFF)
def _dex(c): c.x = c.nz((c.x - 1) & 0xFF)
def _dey(c): c.y = c.nz((c.y - 1) & 0xFF)
def _pha(c): c.push(c.a)
def _php(c): c.push(c.p | FLAG_B | FLAG_U)
def _pla(c): c.a = c.nz(c.pull())
def _plp(c): c.p = c.pull() | FLAG_U


def flagset(mask, on):
    def f(c):
        c.p = c.p | mask if on else c.p & ~mask
    return f


OPS = [None] * 256


def add(code, fn, mode, cyc):
    OPS[code] = (fn, mode, cyc)


for name, fn, table in [
    ('adc', op_adc, {0x69: 'imm', 0x65: 'zp', 0x75: 'zpx', 0x6D: 'abs', 0x7D: 'abx', 0x79: 'aby', 0x61: 'izx', 0x71: 'izy'}),
    ('sbc', op_sbc, {0xE9: 'imm', 0xE5: 'zp', 0xF5: 'zpx', 0xED: 'abs', 0xFD: 'abx', 0xF9: 'aby', 0xE1: 'izx', 0xF1: 'izy'}),
    ('and', op_and, {0x29: 'imm', 0x25: 'zp', 0x35: 'zpx', 0x2D: 'abs', 0x3D: 'abx', 0x39: 'aby', 0x21: 'izx', 0x31: 'izy'}),
    ('ora', op_ora, {0x09: 'imm', 0x05: 'zp', 0x15: 'zpx', 0x0D: 'abs', 0x1D: 'abx', 0x19: 'aby', 0x01: 'izx', 0x11: 'izy'}),
    ('eor', op_eor, {0x49: 'imm', 0x45: 'zp', 0x55: 'zpx', 0x4D: 'abs', 0x5D: 'abx', 0x59: 'aby', 0x41: 'izx', 0x51: 'izy'}),
    ('lda', op_lda, {0xA9: 'imm', 0xA5: 'zp', 0xB5: 'zpx', 0xAD: 'abs', 0xBD: 'abx', 0xB9: 'aby', 0xA1: 'izx', 0xB1: 'izy'}),
    ('cmp', op_cmp, {0xC9: 'imm', 0xC5: 'zp', 0xD5: 'zpx', 0xCD: 'abs', 0xDD: 'abx', 0xD9: 'aby', 0xC1: 'izx', 0xD1: 'izy'}),
    ('sta', op_sta, {0x85: 'zp', 0x95: 'zpx', 0x8D: 'abs', 0x9D: 'abx', 0x99: 'aby', 0x81: 'izx', 0x91: 'izy'}),
    ('ldx', op_ldx, {0xA2: 'imm', 0xA6: 'zp', 0xB6: 'zpy', 0xAE: 'abs', 0xBE: 'aby'}),
    ('ldy', op_ldy, {0xA0: 'imm', 0xA4: 'zp', 0xB4: 'zpx', 0xAC: 'abs', 0xBC: 'abx'}),
    ('stx', op_stx, {0x86: 'zp', 0x96: 'zpy', 0x8E: 'abs'}),
    ('sty', op_sty, {0x84: 'zp', 0x94: 'zpx', 0x8C: 'abs'}),
    ('cpx', op_cpx, {0xE0: 'imm', 0xE4: 'zp', 0xEC: 'abs'}),
    ('cpy', op_cpy, {0xC0: 'imm', 0xC4: 'zp', 0xCC: 'abs'}),
    ('bit', op_bit, {0x24: 'zp', 0x2C: 'abs'}),
    ('asl', rmw(_asl), {0x0A: 'acc', 0x06: 'zp', 0x16: 'zpx', 0x0E: 'abs', 0x1E: 'abx'}),
    ('lsr', rmw(_lsr), {0x4A: 'acc', 0x46: 'zp', 0x56: 'zpx', 0x4E: 'abs', 0x5E: 'abx'}),
    ('rol', rmw(_rol), {0x2A: 'acc', 0x26: 'zp', 0x36: 'zpx', 0x2E: 'abs', 0x3E: 'abx'}),
    ('ror', rmw(_ror), {0x6A: 'acc', 0x66: 'zp', 0x76: 'zpx', 0x6E: 'abs', 0x7E: 'abx'}),
    ('inc', rmw(_inc), {0xE6: 'zp', 0xF6: 'zpx', 0xEE: 'abs', 0xFE: 'abx'}),
    ('dec', rmw(_dec), {0xC6: 'zp', 0xD6: 'zpx', 0xCE: 'abs', 0xDE: 'abx'}),
]:
    for code, mode in table.items():
        cyc = {'imm': 2, 'zp': 3, 'zpx': 4, 'zpy': 4, 'abs': 4, 'abx': 4, 'aby': 4, 'izx': 6, 'izy': 5, 'acc': 2}[mode]
        if name in ('asl', 'lsr', 'rol', 'ror', 'inc', 'dec') and mode != 'acc':
            cyc += 2 if mode in ('zp', 'zpx', 'abs') else 3
        if name == 'sta' and mode in ('abx', 'aby', 'izy'):
            cyc += 1
        add(code, fn, mode, cyc)

for code, flag, want in [(0x10, FLAG_N, False), (0x30, FLAG_N, True), (0x50, FLAG_V, False), (0x70, FLAG_V, True),
                         (0x90, FLAG_C, False), (0xB0, FLAG_C, True), (0xD0, FLAG_Z, False), (0xF0, FLAG_Z, True)]:
    add(code, branch(flag, want), None, 2)
add(0x4C, op_jmp, None, 3)
add(0x6C, op_jmpi, None, 5)
add(0x20, op_jsr, None, 6)
add(0x60, op_rts, None, 6)
add(0x40, op_rti, None, 6)
add(0x00, op_brk, None, 7)
for code, f, cyc in [(0xAA, _tax, 2), (0xA8, _tay, 2), (0x8A, _txa, 2), (0x98, _tya, 2), (0xBA, _tsx, 2), (0x9A, _txs, 2),
                     (0xE8, _inx, 2), (0xC8, _iny, 2), (0xCA, _dex, 2), (0x88, _dey, 2), (0x48, _pha, 3), (0x08, _php, 3),
                     (0x68, _pla, 4), (0x28, _plp, 4), (0xEA, lambda c: None, 2),
                     (0x18, flagset(FLAG_C, 0), 2), (0x38, flagset(FLAG_C, 1), 2), (0x58, flagset(FLAG_I, 0), 2),
                     (0x78, flagset(FLAG_I, 1), 2), (0xB8, flagset(FLAG_V, 0), 2), (0xD8, flagset(FLAG_D, 0), 2),
                     (0xF8, flagset(FLAG_D, 1), 2)]:
    add(code, simple(f), None, cyc)


def bad(c, m):
    raise RuntimeError(f'illegal opcode at {c.cur:04X}')


for i in range(256):
    if OPS[i] is None:
        OPS[i] = (bad, None, 2)
