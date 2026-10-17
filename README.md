# nes-custom-roms

Local workspace for NES/Famicom ROM hacks.

- `games/<game>/` – code, patches, docs and tests for a single game.
- `tools/` – shared tooling (disassembler, emulator test helpers).

ROM images are not stored in this repository. Each game's README says where
to put your own dump of the original ROM and how to build the modified one.

Branching: one game = one working branch (`game/<name>`). `main` holds only
finished, verified work.
