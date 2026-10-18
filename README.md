# nes-custom-roms

Local workspace for NES/Famicom ROM hacks.

- `games/<game>/` – code, patches, docs and tests for a single game.
- `tools/` – shared tooling: `vcdiff.py` (xdelta/VCDIFF decoder).

| Game | Folder | Branch |
|---|---|---|
| Super Mario Bros. Co-op | `games/super-mario-coop/` | `game/super-mario-coop` |

ROM images are not stored in this repository. Each game's README says where
to put your own dump of the original ROM and how to build the modified one.

Branching: one game = one working branch (`game/<name>`). `main` holds only
finished, verified work.
