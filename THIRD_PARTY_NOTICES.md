# Third-party notices

The [MIT License](LICENSE) of this repository covers **only the original work of the project's author
(Zvgelo)**, to the extent of the author's rights. It does not cover, and grants no rights to, the
material listed below. This repository is an unofficial fan project, not affiliated with, endorsed by or
sponsored by Bandai Namco, Nintendo or the authors of the Two Players Hack.

## Covered by the MIT License

- Source code and build scripts: `tools/*.py`, `games/*/src/` (including `src/asm/coop.asm`), except
  the quoted original data described below.
- Automatic tests: `games/*/tests/`.
- Documentation written for this project: README files, `games/*/docs/`, this file.
- README artwork: `assets/readme/hero.svg`, `games/galaxian-coop/assets/readme/hero.svg` (own pixel
  lettering; the P2 ship and the laser are sprites drawn for Galaxian Coop).
- The new code and graphics of Galaxian Coop, including the P2 ship, laser, `CO-OP` badge and title
  text tiles, as delivered in `games/galaxian-coop/patches/Galaxian_Coop.bps`.

## Not covered – third-party material

| Material | Rights holder | Status in this repository |
|---|---|---|
| *Galaxian* (arcade 1979, NES/Famicom 1984): program, graphics, sound, name | Namco / Bandai Namco Entertainment | **Not included.** The BPS patch reads the original data from the user's own ROM; a test checks that no 32-byte run of the original is stored in it. You need your own legally obtained ROM. |
| *Super Mario Bros.* (1985): program, graphics, sound, names and characters | Nintendo | **Not included.** You need your own legally obtained ROM. |
| *Super Mario Bros. – Two Players Hack* (2018), including its `.xdelta` patch and all of its co-op mechanics | Corpse Grinder and Ti | **Not included and not licensed by this project.** The patch is not distributed in this repository or its published history; users download it from the creators' own release ([Emu-Land release thread](https://www.emu-land.net/forum/index.php?topic=81090.0), attachment `Super Mario Bros. (Two Players Hack).7z`) and keep it in the ignored `private/` folder. The build only records its SHA-256 (`d38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd`) and applies it locally. The built ROM keeps the creators' credit `©2018 CORPSE GRINDER & TI`. No license or redistribution permission from the creators was found in the release thread or the [ROMhack Plaza entry](https://www.romhackplaza.org/romhacks/super-mario-bros-two-players-hack-nes) (checked 2026-10-20; the [romhacking.net entry](https://www.romhacking.net/hacks/4180/) could not be checked), and none is claimed. |
| Short byte sequences of the original Galaxian program quoted in `games/galaxian-coop/src/asm/coop.asm` and `src/build.py` (the expected bytes at each hook, checked before patching), and descriptions of the original program in `docs/REVERSE_ENGINEERING.md`, `docs/MEMORY_MAP.md` and `src/original_ram.txt` | Namco / Bandai Namco Entertainment (the original program) | Quoted only to locate and verify the patch points; the original program is not licensed by this project. |
| Screenshots in `games/*/assets/screenshots/` | They show the original games' graphics (Namco, Nintendo) and, for Mario, the Two Players Hack | Frames captured from emulators for illustration. Only the project's own additions in them are the author's; the MIT License does not cover the original graphics shown. |

Trademarks (Galaxian, Namco, Super Mario Bros., Nintendo, NES, Famicom) belong to their owners and are
used only to identify the games.

## Copyright concerns

Copyright holders with concerns regarding material in this repository may contact the maintainer
through GitHub, for example by opening an issue in this repository. Justified requests will be reviewed.
