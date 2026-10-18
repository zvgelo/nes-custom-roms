# Testing – Super Mario Bros. Two Players Hack build

```bash
pip install -r games/super-mario-coop/tests/requirements.txt   # optional: emulator tests
python3 games/super-mario-coop/tests/test_build.py -v
```

The ROM tests need the original ROM and the hack's patch in `private/` (or their paths in `SMB_ORIGINAL`
and `SMB_XDELTA`); without them only the file tests run. The emulator tests use the FCEUmm core through
`stable-retro`: the title screen shows the hack's credit `©2018 CORPSE GRINDER & TI`, and pad 1 / pad 2
move Mario and Luigi independently.
