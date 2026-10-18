# Testing – Super Mario Bros. Two Players Hack build

## Automatic (last run 2026-10-20)

```bash
pip install -r games/super-mario-coop/tests/requirements.txt   # optional: emulator tests
python3 games/super-mario-coop/tests/test_build.py -v
```

Result: **16/16 OK** (Linux, Python 3.14, stable-retro 1.0.1 with the FCEUmm core, xdelta3 3.1.0). Built
ROM: SHA-256 `e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4` – the unmodified Two
Players Hack. Without stable-retro the 2 emulator tests are skipped; without the `xdelta3` program
`test_xdelta3_binary_matches` is skipped; without the original ROM and the hack's patch in `private/`
all ROM tests are skipped (the 4 file tests still run). The patch is not in the repository: the tests
use a local copy of the authors' release (SHA-256 `d38048c3…`), like the build.

| Test | Checks |
|---|---|
| `test_no_rom_or_third_party_patch_in_repository` | no ROM and no `.xdelta` file is tracked by git in this folder |
| `test_patch_location_is_ignored_by_git` | `private/` and any `.xdelta` (also in `patches/`) are ignored by git |
| `test_missing_patch_is_reported`, `test_wrong_patch_is_rejected` | a missing patch: message with the authors' release URL, the expected SHA-256 and `--patch`; a patch with another SHA-256 is refused |
| `test_original`, `test_inputs_untouched` | SHA-256 and header of the original; the build changes neither the ROM nor the patch |
| `test_xdelta_file` | SHA-256 of the patch |
| `test_xdelta_python_decoder` | `tools/vcdiff.py` gives the ROM `e962eee2…` |
| `test_xdelta3_binary_matches` | `xdelta3` gives the same bytes |
| `test_output_is_the_unmodified_hack` | `build.py` writes exactly the patch's result – nothing is added |
| `test_hack_header` | iNES 1.0, mapper 24, 64 KiB PRG, 8 KiB CHR, size |
| `test_title_text` | the title string reads `©2018 CORPSE GRINDER & TI` |
| `test_rejects_wrong_original`, `test_reproducible` | a wrong original is refused; two builds are identical |
| `test_title_shows_the_hack_authors` (emulator) | the title screen draws the hack's credit line; compared with the original game, only that line, Luigi's HUD line and the 2-player menu text differ |
| `test_two_controllers_move_two_players` (emulator) | 2 PLAYERS GAME: pad 1 RIGHT moves only object `$8B`, pad 2 only `$8C`, both together move both |

Also checked: the built ROM is identical to the result of `xdelta3 -d` on the same inputs and to a
copy of the hack ROM patched independently. The README commands were run and gave the documented
hashes.

The screenshots in `assets/screenshots/` are frames of the built ROM in the same FCEUmm core, driven by
two virtual controllers (title with 2 PLAYERS GAME selected; level 1-1 at the start; Mario and Luigi
apart after moving separately). The title screen shows the hack's original credit
`©2018 CORPSE GRINDER & TI`.

**Not tested**: RetroArch itself, Mesen 2, other emulators and real hardware; sound; collisions between
the players, death and level restart, later levels. stable-retro ships its own FCEUmm build – other cores
are not confirmed.

## Manual test checklist (any emulator with mapper 24)

1. Build the ROM (`python3 games/super-mario-coop/src/build.py`) and load
   `build/Super Mario Bros. (Two Players Hack).nes`.
2. Core: the ROM needs mapper 24 (VRC6) – FCEUmm or Mesen recommended; Nestopia supports it too. Check the
   active core in RetroArch → Quick Menu → Information. If the game does not start or the graphics are
   wrong, change the core.
3. Controllers: RetroArch → Settings → Input → Port 1 Controls / Port 2 Controls – two different pads.
4. Title screen: `©2018 CORPSE GRINDER & TI` under `©1985 NINTENDO`, letters complete.
5. **2 PLAYERS GAME** (SELECT, START on pad 1): Mario (pad 1) and Luigi (pad 2) on screen together, each
   controlled separately; jumping, running (B), fire flower, pipes; enemy contact and lives of each player,
   level restart; scrolling when the players separate; pause, Game Over.
6. **1 PLAYER GAME**: normal Mario.
7. Note the core and RetroArch version, what worked, screenshots of problems.
