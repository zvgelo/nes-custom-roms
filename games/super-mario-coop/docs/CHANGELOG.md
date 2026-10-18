# Changelog – Super Mario Bros. Two Players Hack build

Co-op mechanics: "Super Mario Bros. Two Players Hack" by Corpse Grinder and Ti. This is not a new co-op
engine; this folder only builds the unmodified hack.

## 2026-10-20 – documentation, credits and local patch

- README in English and Polish (`README_PL.md`) with an "Original Hack Credits & Copyright" section;
  copyright concerns can be raised through GitHub.
- MIT License for the project's own files; `THIRD_PARTY_NOTICES.md` for everything else.
- The hack's `.xdelta` is not distributed: users download it from the authors' release (Emu-Land
  thread, attachment `Super Mario Bros. (Two Players Hack).7z`) and put it in `private/`, or pass
  `--patch PATH`. The build checks its SHA-256
  (`d38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd`) and explains where to get it when it
  is missing. `*.xdelta` is ignored by git.
- Screenshots in `assets/screenshots/` (FCEUmm via stable-retro, ×3, no filtering).
- Tests: 14 file/build tests + 2 emulator tests. Built ROM: the unmodified Two Players Hack,
  SHA-256 `e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4`.

## 2026-10-18 – build kit

- Project in `games/super-mario-coop/` on branch `game/super-mario-coop`.
- `tools/vcdiff.py`: VCDIFF decoder in Python (same result as `xdelta3`).
- `src/build.py`: one-command build with a SHA-256 check of the original, the patch and the result;
  inputs in `private/`, output in `build/`; clear errors with exit code 1; never overwrites an input.
- Tests: file/build tests and two emulator tests (FCEUmm via stable-retro).
- The built ROM's header says mapper 24 (VRC6a), as written by the hack.
