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
| *Super Mario Bros. – Two Players Hack* (2018), including its `.xdelta` patch and all of its co-op mechanics | Corpse Grinder and Ti | **Included unmodified** as `games/super-mario-coop/patches/Super Mario Bros. (Two Players Hack).xdelta` (SHA-256 `d38048c3…`), attributed to its creators and provided separately from this repository's MIT-licensed work. **Not covered by the MIT License.** No license or redistribution permission from the creators was found in the [Emu-Land release thread](https://www.emu-land.net/forum/index.php?topic=81090.0) or the [ROMhack Plaza entry](https://www.romhackplaza.org/romhacks/super-mario-bros-two-players-hack-nes) (checked 2026-10-20; the [romhacking.net entry](https://www.romhacking.net/hacks/4180/) could not be checked), and none is implied. The original release can also be downloaded from the creators' thread. |
| Short byte sequences of the original Galaxian program quoted in `games/galaxian-coop/src/asm/coop.asm` and `src/build.py` (the expected bytes at each hook, checked before patching), and descriptions of the original program in `docs/REVERSE_ENGINEERING.md`, `docs/MEMORY_MAP.md` and `src/original_ram.txt` | Namco / Bandai Namco Entertainment (the original program) | Quoted only to locate and verify the patch points; the original program is not licensed by this project. |
| Screenshots in `games/*/assets/screenshots/` | They show the original games' graphics (Namco, Nintendo) and, for Mario, the Two Players Hack | Frames captured from emulators for illustration. Only the project's own additions in them are the author's; the MIT License does not cover the original graphics shown. |

Trademarks (Galaxian, Namco, Super Mario Bros., Nintendo, NES, Famicom) belong to their owners and are
used only to identify the games.

## Copyright concerns

Copyright holders with concerns regarding included material may contact the repository maintainer
through GitHub, for example by opening an issue in this repository. Justified requests – including a
request to remove the Two Players Hack patch – will be reviewed.
