# Changelog – Super Mario Bros. Two Players Hack build

Co-op mechanics: "Super Mario Bros. Two Players Hack" by Corpse Grinder and Ti. This is not a new co-op
engine; this folder only builds the unmodified hack.

## 2026-10-18 – build kit

- Project in `games/super-mario-coop/` on branch `game/super-mario-coop`.
- `tools/vcdiff.py`: VCDIFF decoder in Python (same result as `xdelta3`).
- `src/build.py`: one-command build with a SHA-256 check of the original, the patch and the result;
  inputs in `private/`, output in `build/`; clear errors with exit code 1; never overwrites an input.
- Tests: file/build tests and two emulator tests (FCEUmm via stable-retro).
- The built ROM's header says mapper 24 (VRC6a), as written by the hack.
