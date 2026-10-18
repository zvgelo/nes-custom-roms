"""Super Mario Bros. Two Players Hack build tests.

    python3 games/super-mario-coop/tests/test_build.py -v      (or pytest)

Tests that need the original ROM or the hack's patch read them from private/
($SMB_ORIGINAL and $SMB_XDELTA override them) and are skipped when they are
missing; the patch is not part of the repository.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GAME = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(GAME.parents[1] / "tools"), str(GAME / "src")]
import build  # noqa: E402
import vcdiff  # noqa: E402

ORIGINAL = Path(os.environ.get("SMB_ORIGINAL", build.DEFAULT_ROM))
XDELTA = Path(os.environ.get("SMB_XDELTA", build.DEFAULT_PATCH))

# SMB text tiles: 0-9 = $00-$09, A-Z = $0A-$23, space = $24, (c) = $CF; the hack uses $FF for "&"
FONT = {**{i: str(i) for i in range(10)}, **{0x0A + i: chr(65 + i) for i in range(26)},
        0x24: " ", 0xCF: "©", 0xFF: "&"}
TITLE_TEXT = slice(3553, 3578)   # 25 tiles after the $2303 VRAM header (22 03 19)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def text(data):
    return "".join(FONT.get(b, "?") for b in data[TITLE_TEXT])


def test_no_rom_or_third_party_patch_in_repository():
    tracked = subprocess.run(["git", "ls-files", str(GAME)], capture_output=True, text=True, cwd=GAME)
    if tracked.returncode != 0:
        raise unittest.SkipTest("not a git checkout")
    assert not [f for f in tracked.stdout.splitlines() if f.lower().endswith((".nes", ".fds", ".unf", ".xdelta"))]


def test_patch_location_is_ignored_by_git():
    check = subprocess.run(["git", "check-ignore", "-q", str(build.DEFAULT_PATCH)], cwd=GAME)
    if check.returncode == 128:
        raise unittest.SkipTest("not a git checkout")
    assert check.returncode == 0, "private/ patch location is not ignored"
    other = GAME / "patches" / build.XDELTA_NAME
    assert subprocess.run(["git", "check-ignore", "-q", str(other)], cwd=GAME).returncode == 0


def test_missing_patch_is_reported():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            build.read_patch(Path(tmp) / build.XDELTA_NAME)
        except SystemExit as e:
            msg = str(e)
            assert "patch not found" in msg and "not included in this repository" in msg
            assert build.RELEASE_URL in msg and build.XDELTA_SHA in msg and "--patch" in msg
            return
    raise AssertionError("missing patch accepted")


def test_wrong_patch_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / build.XDELTA_NAME
        bad.write_bytes(b"\xd6\xc3\xc4\x00" + bytes(64))
        try:
            build.read_patch(bad)
        except SystemExit as e:
            assert "unexpected SHA-256" in str(e) and build.XDELTA_SHA in str(e)
            return
    raise AssertionError("wrong patch accepted")


@unittest.skipUnless(ORIGINAL.exists() and XDELTA.exists(), f"needs {ORIGINAL} and {XDELTA}")
class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.original = ORIGINAL.read_bytes()
        cls.hack = vcdiff.decode(cls.original, XDELTA.read_bytes())
        cls.built = build.build(ORIGINAL, Path(cls.tmp.name) / "hack.nes", patch_path=XDELTA)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_original(self):
        self.assertEqual(sha(self.original), build.ORIGINAL_SHA)
        h = self.original[:16]
        self.assertEqual((h[4], h[5], (h[6] >> 4) | (h[7] & 0xF0)), (2, 1, 0))  # NROM, 32K+8K

    def test_xdelta_file(self):
        self.assertEqual(sha(XDELTA.read_bytes()), build.XDELTA_SHA)

    def test_xdelta_python_decoder(self):
        self.assertEqual(sha(self.hack), build.HACK_SHA)

    @unittest.skipUnless(shutil.which("xdelta3"), "xdelta3 not installed")
    def test_xdelta3_binary_matches(self):
        self.assertEqual(build.apply_xdelta(self.original, XDELTA, use_binary=True), self.hack)

    def test_output_is_the_unmodified_hack(self):
        self.assertEqual(self.built, self.hack)
        self.assertEqual(sha(self.built), build.HACK_SHA)

    def test_hack_header(self):
        h = self.hack[:16]
        self.assertEqual(h[:4], b"NES\x1a")
        self.assertEqual(h[7] & 0x0C, 0, "iNES 1.0")
        self.assertEqual((h[6] >> 4) | (h[7] & 0xF0), 24, "mapper 24 (VRC6) as written by the hack")
        self.assertEqual((h[4] * 0x4000, h[5] * 0x2000), (0x10000, 0x2000))
        self.assertEqual(len(self.hack), 16 + 0x10000 + 0x2000)

    def test_title_text(self):
        self.assertEqual(self.built[3550:3553], bytes.fromhex("22 03 19"))
        self.assertEqual(text(self.built), "©2018 CORPSE GRINDER & TI")

    def test_rejects_wrong_original(self):
        bad = Path(self.tmp.name) / "wrong.nes"
        bad.write_bytes(self.original[:-1] + b"\x00")
        with self.assertRaises(SystemExit):
            build.build(bad, Path(self.tmp.name) / "out.nes", patch_path=XDELTA)

    def test_reproducible(self):
        again = build.build(ORIGINAL, Path(self.tmp.name) / "again.nes", patch_path=XDELTA)
        self.assertEqual(again, self.built)

    def test_inputs_untouched(self):
        self.assertEqual(sha(ORIGINAL.read_bytes()), build.ORIGINAL_SHA)
        self.assertEqual(sha(XDELTA.read_bytes()), build.XDELTA_SHA)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn))
    suite.addTests(loader.loadTestsFromTestCase(TestBuild))
    if "test_emulator" not in sys.modules:
        try:
            import test_emulator  # noqa: F401
            suite.addTests(loader.loadTestsFromModule(test_emulator))
        except ImportError:
            pass
    verbosity = 2 if "-v" in sys.argv else 1
    sys.exit(not unittest.TextTestRunner(verbosity=verbosity).run(suite).wasSuccessful())
