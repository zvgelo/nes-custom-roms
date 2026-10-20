#!/usr/bin/env python3
"""Minimal two-pass 6502 assembler used by the ROM patchers in this repo.

Supported syntax (a small ca65-like subset):

    ; comment
    NAME = expr              constant
    label:                   label (may share a line with an instruction)
    .org expr                set program counter
    .patch expr, "A9 00"     set program counter for a patch over original
                             code; the bytes that follow (up to the next
                             .org/.patch) must replace exactly the listed
                             original bytes
    .byte expr, ...          (.db) bytes
    .word expr, ...          (.dw) little-endian words
    .res n[, fill]           reserve n bytes

Operands: #imm, zp/abs (auto by value), a:expr forces absolute,
expr,X  expr,Y  (zp,X)  (zp),Y  (abs) for JMP, A for accumulator.
Expressions: $hex, %bin, decimal, symbols, + - * / & | ^ << >> ( ),
<expr (low byte), >expr (high byte).
"""
import re

OPCODES = {
    'ADC': {'imm': 0x69, 'zp': 0x65, 'zpx': 0x75, 'abs': 0x6D, 'abx': 0x7D, 'aby': 0x79, 'izx': 0x61, 'izy': 0x71},
    'AND': {'imm': 0x29, 'zp': 0x25, 'zpx': 0x35, 'abs': 0x2D, 'abx': 0x3D, 'aby': 0x39, 'izx': 0x21, 'izy': 0x31},
    'ASL': {'acc': 0x0A, 'zp': 0x06, 'zpx': 0x16, 'abs': 0x0E, 'abx': 0x1E},
    'BCC': {'rel': 0x90}, 'BCS': {'rel': 0xB0}, 'BEQ': {'rel': 0xF0}, 'BMI': {'rel': 0x30},
    'BNE': {'rel': 0xD0}, 'BPL': {'rel': 0x10}, 'BVC': {'rel': 0x50}, 'BVS': {'rel': 0x70},
    'BIT': {'zp': 0x24, 'abs': 0x2C},
    'BRK': {'imp': 0x00}, 'CLC': {'imp': 0x18}, 'CLD': {'imp': 0xD8}, 'CLI': {'imp': 0x58}, 'CLV': {'imp': 0xB8},
    'CMP': {'imm': 0xC9, 'zp': 0xC5, 'zpx': 0xD5, 'abs': 0xCD, 'abx': 0xDD, 'aby': 0xD9, 'izx': 0xC1, 'izy': 0xD1},
    'CPX': {'imm': 0xE0, 'zp': 0xE4, 'abs': 0xEC},
    'CPY': {'imm': 0xC0, 'zp': 0xC4, 'abs': 0xCC},
    'DEC': {'zp': 0xC6, 'zpx': 0xD6, 'abs': 0xCE, 'abx': 0xDE},
    'DEX': {'imp': 0xCA}, 'DEY': {'imp': 0x88},
    'EOR': {'imm': 0x49, 'zp': 0x45, 'zpx': 0x55, 'abs': 0x4D, 'abx': 0x5D, 'aby': 0x59, 'izx': 0x41, 'izy': 0x51},
    'INC': {'zp': 0xE6, 'zpx': 0xF6, 'abs': 0xEE, 'abx': 0xFE},
    'INX': {'imp': 0xE8}, 'INY': {'imp': 0xC8},
    'JMP': {'abs': 0x4C, 'ind': 0x6C}, 'JSR': {'abs': 0x20},
    'LDA': {'imm': 0xA9, 'zp': 0xA5, 'zpx': 0xB5, 'abs': 0xAD, 'abx': 0xBD, 'aby': 0xB9, 'izx': 0xA1, 'izy': 0xB1},
    'LDX': {'imm': 0xA2, 'zp': 0xA6, 'zpy': 0xB6, 'abs': 0xAE, 'aby': 0xBE},
    'LDY': {'imm': 0xA0, 'zp': 0xA4, 'zpx': 0xB4, 'abs': 0xAC, 'abx': 0xBC},
    'LSR': {'acc': 0x4A, 'zp': 0x46, 'zpx': 0x56, 'abs': 0x4E, 'abx': 0x5E},
    'NOP': {'imp': 0xEA},
    'ORA': {'imm': 0x09, 'zp': 0x05, 'zpx': 0x15, 'abs': 0x0D, 'abx': 0x1D, 'aby': 0x19, 'izx': 0x01, 'izy': 0x11},
    'PHA': {'imp': 0x48}, 'PHP': {'imp': 0x08}, 'PLA': {'imp': 0x68}, 'PLP': {'imp': 0x28},
    'ROL': {'acc': 0x2A, 'zp': 0x26, 'zpx': 0x36, 'abs': 0x2E, 'abx': 0x3E},
    'ROR': {'acc': 0x6A, 'zp': 0x66, 'zpx': 0x76, 'abs': 0x6E, 'abx': 0x7E},
    'RTI': {'imp': 0x40}, 'RTS': {'imp': 0x60},
    'SBC': {'imm': 0xE9, 'zp': 0xE5, 'zpx': 0xF5, 'abs': 0xED, 'abx': 0xFD, 'aby': 0xF9, 'izx': 0xE1, 'izy': 0xF1},
    'SEC': {'imp': 0x38}, 'SED': {'imp': 0xF8}, 'SEI': {'imp': 0x78},
    'STA': {'zp': 0x85, 'zpx': 0x95, 'abs': 0x8D, 'abx': 0x9D, 'aby': 0x99, 'izx': 0x81, 'izy': 0x91},
    'STX': {'zp': 0x86, 'zpy': 0x96, 'abs': 0x8E},
    'STY': {'zp': 0x84, 'zpx': 0x94, 'abs': 0x8C},
    'TAX': {'imp': 0xAA}, 'TAY': {'imp': 0xA8}, 'TSX': {'imp': 0xBA}, 'TXA': {'imp': 0x8A},
    'TXS': {'imp': 0x9A}, 'TYA': {'imp': 0x98},
}
SIZE = {'imp': 1, 'acc': 1, 'imm': 2, 'zp': 2, 'zpx': 2, 'zpy': 2, 'izx': 2, 'izy': 2, 'rel': 2,
        'abs': 3, 'abx': 3, 'aby': 3, 'ind': 3}
ZP_OF = {'abs': 'zp', 'abx': 'zpx', 'aby': 'zpy'}


class AsmError(Exception):
    pass


class Segment:
    def __init__(self, org, expect=None, line=0):
        self.org, self.expect, self.line = org, expect, line
        self.data = bytearray()


def _split_args(s):
    out, depth, cur, q = [], 0, '', False
    for ch in s:
        if ch == '"':
            q = not q
        if ch == '(' and not q:
            depth += 1
        if ch == ')' and not q:
            depth -= 1
        if ch == ',' and depth == 0 and not q:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


class Assembler:
    def __init__(self, symbols=None):
        self.symbols = dict(symbols or {})
        self.labels = set()

    def eval(self, expr, final):
        e = expr.strip()
        if e.startswith('<'):
            return self.eval(e[1:], final) & 0xFF
        if e.startswith('>'):
            return (self.eval(e[1:], final) >> 8) & 0xFF
        e = re.sub(r'\$([0-9A-Fa-f]+)', lambda m: str(int(m.group(1), 16)), e)
        e = re.sub(r'%([01]+)', lambda m: str(int(m.group(1), 2)), e)

        def sym(m):
            name = m.group(0)
            if name in self.symbols:
                return str(self.symbols[name])
            if final:
                raise AsmError(f'undefined symbol {name}')
            return '0x10000'  # unknown in pass 1: assume absolute width
        e = re.sub(r'[A-Za-z_@][A-Za-z0-9_@]*', sym, e)
        if not re.fullmatch(r'[0-9x\s+\-*/&|^<>()]*', e):
            raise AsmError(f'bad expression {expr!r}')
        return int(eval(e.replace('/', '//'), {'__builtins__': {}}))

    def _known(self, expr):
        try:
            self.eval(expr, True)
            return True
        except AsmError:
            return False

    def parse_operand(self, mn, op):
        op = op.strip()
        modes = OPCODES[mn]
        if not op:
            return ('acc' if 'acc' in modes and 'imp' not in modes else 'imp'), None
        if op.upper() == 'A' and 'acc' in modes:
            return 'acc', None
        if 'rel' in modes:
            return 'rel', op
        if op.startswith('#'):
            return 'imm', op[1:]
        m = re.fullmatch(r'\((.*)\)\s*,\s*[Yy]', op)
        if m:
            return 'izy', m.group(1)
        m = re.fullmatch(r'\((.*)\s*,\s*[Xx]\s*\)', op)
        if m:
            return 'izx', m.group(1)
        if mn == 'JMP' and op.startswith('(') and op.endswith(')'):
            return 'ind', op[1:-1]
        force_abs = op.startswith('a:')
        if force_abs:
            op = op[2:]
        mode = 'abs'
        m = re.fullmatch(r'(.*?)\s*,\s*([XxYy])', op)
        if m:
            op, mode = m.group(1), 'abx' if m.group(2) in 'Xx' else 'aby'
        if force_abs:
            return mode, op
        return mode, op  # zp narrowing decided by caller

    def assemble(self, text):
        lines = text.splitlines()
        sizes = {}
        for final in (False, True):
            segs, seg, pc = [], None, None
            seen_labels = set()
            for ln, raw in enumerate(lines, 1):
                line = raw.split(';', 1)[0].rstrip()
                if not line.strip():
                    continue
                try:
                    m = re.match(r'\s*([A-Za-z_@][A-Za-z0-9_@]*)\s*=\s*(.+)$', line)
                    if m:
                        if final or self._known(m.group(2)):
                            self.symbols[m.group(1)] = self.eval(m.group(2), final)
                        continue
                    m = re.match(r'\s*([A-Za-z_@][A-Za-z0-9_@]*):\s*(.*)$', line)
                    if m:
                        if pc is None:
                            raise AsmError('label before .org')
                        if m.group(1) in seen_labels or (not final and m.group(1) in self.symbols):
                            raise AsmError(f'duplicate symbol {m.group(1)}')
                        seen_labels.add(m.group(1))
                        self.labels.add(m.group(1))
                        self.symbols[m.group(1)] = pc
                        line = m.group(2)
                        if not line.strip():
                            continue
                    parts = line.strip().split(None, 1)
                    word, rest = parts[0], (parts[1] if len(parts) > 1 else '')
                    w = word.lower()
                    if w in ('.org', '.patch'):
                        args = _split_args(rest)
                        pc = self.eval(args[0], True)
                        expect = None
                        if w == '.patch':
                            expect = bytes.fromhex(args[1].strip('"'))
                        seg = Segment(pc, expect, ln)
                        segs.append(seg)
                        continue
                    if seg is None:
                        raise AsmError('code before .org')
                    if w in ('.byte', '.db'):
                        for a in _split_args(rest):
                            if a.startswith('"'):
                                seg.data += a.strip('"').encode('ascii')
                            else:
                                seg.data.append(self.eval(a, final) & 0xFF)
                    elif w in ('.word', '.dw'):
                        for a in _split_args(rest):
                            v = self.eval(a, final) & 0xFFFF
                            seg.data += bytes([v & 0xFF, v >> 8])
                    elif w == '.res':
                        a = _split_args(rest)
                        fill = self.eval(a[1], final) if len(a) > 1 else 0xFF
                        seg.data += bytes([fill]) * self.eval(a[0], final)
                    else:
                        mn = word.upper()
                        if mn not in OPCODES:
                            raise AsmError(f'unknown mnemonic {word}')
                        mode, expr = self.parse_operand(mn, rest)
                        if mode in ZP_OF and not rest.strip().startswith('a:'):
                            if not final:
                                small = self._known(expr) and self.eval(expr, True) < 0x100
                                sizes[ln] = small
                            if sizes.get(ln) and ZP_OF[mode] in OPCODES[mn]:
                                mode = ZP_OF[mode]
                        opc = OPCODES[mn].get(mode)
                        if opc is None:
                            raise AsmError(f'{mn} does not support mode {mode}')
                        seg.data.append(opc)
                        n = SIZE[mode]
                        if mode == 'rel':
                            t = self.eval(expr, final)
                            off = t - (seg.org + len(seg.data) + 1)
                            if final and not -128 <= off <= 127:
                                raise AsmError(f'branch out of range ({off})')
                            seg.data.append(off & 0xFF)
                        elif n == 2:
                            v = self.eval(expr, final)
                            if final and not 0 <= v <= 0xFF and mode != 'imm':
                                raise AsmError(f'zero-page operand out of range: {v:#x}')
                            if final and mode == 'imm' and not -128 <= v <= 0xFF:
                                raise AsmError(f'immediate out of range: {v}')
                            seg.data.append(v & 0xFF)
                        elif n == 3:
                            v = self.eval(expr, final) & 0xFFFF
                            seg.data += bytes([v & 0xFF, v >> 8])
                    pc = seg.org + len(seg.data)
                except AsmError as e:
                    raise AsmError(f'line {ln}: {e}\n  {raw}') from None
                except Exception as e:  # noqa: BLE001 - report the offending line
                    raise AsmError(f'line {ln}: {e!r}\n  {raw}') from None
        for s in segs:
            if s.expect is not None and len(s.data) != len(s.expect):
                raise AsmError(f'.patch at ${s.org:04X} (line {s.line}) is {len(s.data)} bytes, '
                               f'original span is {len(s.expect)} bytes')
        return segs
