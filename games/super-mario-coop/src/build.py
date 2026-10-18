#!/usr/bin/env python3
"""Build the Super Mario Bros. Two Players Hack ROM from the original ROM.

    python3 games/super-mario-coop/src/build.py [original.nes] [--patch PATCH.xdelta] [-o out.nes] [--xdelta3]

The hack and its .xdelta patch are by Corpse Grinder and Ti (2018) and are
not part of this repository: download the patch from the authors' release
(RELEASE_URL) and put it in private/, or pass its path with --patch.
Steps: check the original (SHA-256) ->
check the patch (SHA-256) -> apply it (pure-Python VCDIFF decoder, or the
xdelta3 binary with --xdelta3) -> check the result. Nothing is added to the
hack. The original and the patch are only read; output goes to build/.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
REPO = GAME.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
import vcdiff  # noqa: E402

ORIGINAL_SHA = 'f61548fdf1670cffefcc4f0b7bdcdd9eaba0c226e3b74f8666071496988248de'
XDELTA_NAME = 'Super Mario Bros. (Two Players Hack).xdelta'
XDELTA_SHA = 'd38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd'
RELEASE_URL = 'https://www.emu-land.net/forum/index.php?topic=81090.0'
HACK_SHA = 'e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4'
DEFAULT_ROM = GAME / 'private' / 'original.nes'
DEFAULT_PATCH = GAME / 'private' / XDELTA_NAME
DEFAULT_OUT = GAME / 'build' / 'Super Mario Bros. (Two Players Hack).nes'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_patch(patch_path=DEFAULT_PATCH):
    patch_path = Path(patch_path)
    if not patch_path.is_file():
        raise SystemExit(f'patch not found: {patch_path}\n'
                         f'The Two Players Hack patch by Corpse Grinder and Ti is not included in this '
                         f'repository.\nDownload the authors\' release from {RELEASE_URL}\n'
                         f'(attachment "Super Mario Bros. (Two Players Hack).7z"), extract "{XDELTA_NAME}"\n'
                         f'and put it in {DEFAULT_PATCH.parent}/ or pass --patch PATH. '
                         f'Expected SHA-256: {XDELTA_SHA}')
    patch = patch_path.read_bytes()
    actual = sha256(patch)
    if actual != XDELTA_SHA:
        raise SystemExit(f'{patch_path.name}: unexpected SHA-256 (not the expected Two Players Hack release)\n'
                         f'  found:    {actual}\n  expected: {XDELTA_SHA}\n'
                         f'Use the unmodified patch from {RELEASE_URL}')
    return patch


def apply_xdelta(original, patch_path=DEFAULT_PATCH, use_binary=False):
    patch = read_patch(patch_path)
    if not use_binary:
        return vcdiff.decode(original, patch)
    exe = shutil.which('xdelta3')
    if not exe:
        raise SystemExit('xdelta3 not found')
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp) / 'src.nes', Path(tmp) / 'out.nes'
        src.write_bytes(original)
        subprocess.run([exe, '-d', '-f', '-s', str(src), str(patch_path), str(out)], check=True)
        return out.read_bytes()


def build(rom_path=DEFAULT_ROM, out_path=DEFAULT_OUT, use_binary=False, patch_path=DEFAULT_PATCH):
    rom_path = Path(rom_path)
    if not rom_path.is_file():
        raise SystemExit(f'original ROM not found: {rom_path}\n'
                         f'copy your Super Mario Bros. (World).nes there (see README)')
    original = rom_path.read_bytes()
    if sha256(original) != ORIGINAL_SHA:
        raise SystemExit('input is not Super Mario Bros. (World) [SHA-256 mismatch]')
    try:
        hack = apply_xdelta(original, patch_path, use_binary)
    except (vcdiff.Unsupported, ValueError, subprocess.CalledProcessError) as e:
        raise SystemExit(f'xdelta failed: {e}')
    if sha256(hack) != HACK_SHA:
        raise SystemExit('xdelta result has an unexpected SHA-256')
    out_path = Path(out_path)
    if out_path.resolve() in (rom_path.resolve(), Path(patch_path).resolve()):
        raise SystemExit('refusing to overwrite an input file')
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(hack)
    print(f'Saved:  {out_path}')
    print(f'SHA256: {HACK_SHA}')
    return hack


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('rom', nargs='?', default=DEFAULT_ROM)
    ap.add_argument('--patch', default=DEFAULT_PATCH, help=f'the hack\'s patch (default: private/{XDELTA_NAME})')
    ap.add_argument('-o', '--out', default=DEFAULT_OUT)
    ap.add_argument('--xdelta3', action='store_true', help='use the xdelta3 binary instead of tools/vcdiff.py')
    a = ap.parse_args()
    build(a.rom, a.out, a.xdelta3, a.patch)


if __name__ == '__main__':
    main()
