# nes-custom-roms

Local workspace for NES/Famicom ROM hacks.

- `games/<game>/` – code, patches, docs and tests for a single game.
- `tools/` – shared tooling: `asm6502.py` (assembler), `bps.py` (BPS patches),
  `nestest.py` (headless emulator helpers for tests).

| Game | Folder | Branch |
|---|---|---|
| Galaxian Coop | `games/galaxian-coop/` | `game/galaxian-coop` |

ROM images are not stored in this repository. Each game's README says where
to put your own dump of the original ROM and how to build the modified one.

Branching: one game = one working branch (`game/<name>`). `main` holds only
finished, verified work.
