# Super Mario Bros. Two Players Hack – build kit

Mario and Luigi on screen at the same time, each controlled from their own controller. The game is the
**Super Mario Bros. Two Players Hack by Corpse Grinder and Ti (2018)**. This folder only builds the
unmodified hack reproducibly from your own *Super Mario Bros.* ROM and the hack's original patch.

## Inputs (not in the repository)

| Input | |
|---|---|
| Your own ROM | `Super Mario Bros. (World).nes`, SHA-256 `f61548fdf1670cffefcc4f0b7bdcdd9eaba0c226e3b74f8666071496988248de` |
| The hack's patch | `Super Mario Bros. (Two Players Hack).xdelta` from the authors' release ([Emu-Land thread](https://www.emu-land.net/forum/index.php?topic=81090.0)), SHA-256 `d38048c3ea96aabf2d4162d446ced3268681e2f0915a0c828d9363934371cffd` |

## Build

```bash
mkdir -p games/super-mario-coop/private
cp "Super Mario Bros. (World).nes" games/super-mario-coop/private/original.nes
cp "Super Mario Bros. (Two Players Hack).xdelta" games/super-mario-coop/private/
python3 games/super-mario-coop/src/build.py
# build/Super Mario Bros. (Two Players Hack).nes, SHA-256
# e962eee2c23449070ebd599357570cfc9da9586e21f142596f49b1eb8c691dd4
```

The result is a mapper 24 (Konami VRC6a) ROM. Player 1 is Mario, player 2 is Luigi; choose
**2 PLAYERS GAME** on the title screen. Tests: `python3 games/super-mario-coop/tests/test_build.py -v`
([docs/TESTING.md](docs/TESTING.md)).

## Credits

*Super Mario Bros. – Two Players Hack*: Corpse Grinder and Ti (2018) – the hack, its co-op mechanics and
its patch. *Super Mario Bros.* © Nintendo. Unofficial fan project; no ROM is included.
