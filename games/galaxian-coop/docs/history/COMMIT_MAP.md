# Commit map – published history

The development history was cleaned up before the first publication: short commits of one stage were
combined, an accidental copy of the Mario project was removed from this branch (Mario is developed only
on `game/super-mario-coop`; `games/super-mario-coop/` here is what the branch inherits from `main`), the
author of every commit was set to the project's public name, and the Super Mario Bros. Two Players Hack
patch – a third-party file – was removed from every commit. Commit IDs of the development history are
therefore not published; older documents (IMPLEMENTATION_REPORT, history/TESTING_HISTORY) refer to
development commits by their messages, which are listed here next to the published commit that contains
them.

## game/galaxian-coop

| Published commit | Message | Development commits combined in it (oldest first) |
|---|---|---|
| `b054f37` | Add Galaxian co-op ROM hack | Add Galaxian stage 1, Rename mod to Galaxian Coop, Add 6502 assembler; Add player 2 ship and movement, Add P2 combat, lives and HUD; Add BPS patch output, Add stage 2 BPS patch, Add emulator tests, Rename folder to galaxian-coop, Add Mesen label export, Add Galaxian Coop docs |
| `4563b11` | Merge main into Galaxian | Merge main into Galaxian |
| `5233eab` | Move private inputs out of the tree | Move Galaxian input to private, Update Galaxian docs |
| `5e09935` | Merge main into Galaxian | Merge main into Galaxian |
| `35ebd40` | Add lives HUD, life sharing and weapon progression | Fix top screen artifacts, Improve lives HUD; Add life sharing, Add title credits, Add coop tests, Fix stray HUD tile, Unify lives display; Add weapon boost, Add W4, banners, spawns, badge, Add boost and banner tests, Rename outputs, update BPS, Add Galaxian build guide |
| `097c530` | Add respawn shield and stabilize weapons and CPU use | Update tools list, Check W4 lag frames, Add implementation report; Fix fire input, Fix death weapon reset, Fix stage one boost, Add respawn shield, Add shield blinking, Fix fire after respawn, Add weapon regression tests, Test respawn protection, Update RC2 docs; Fix P1 ghost shooting, Verify weapon parity, Optimize frame budget, Add RC3 tests, Add FCEUmm checks, Update RC3 docs |
| `88845f0` | Add overdrive and distinct player visuals | Fix score HUD corruption, Add overdrive power-up, Add RC4 regression tests, Update RC4 docs, Give free W2 to waiting pilots; Improve player colors, Differentiate coop ships, Add visual regression tests, Update RC5 docs |
| `711af5c` | Unify solo and co-op rules and rework overdrive | Unify player progression, Enable solo respawn shield, Enable solo stage HUD, Restore demo firing, Add solo parity tests; Strengthen overdrive aggression, Start overdrive with next stage, Fix solo HUD after co-op, Add overdrive and HUD tests, Update RC6 docs |
| `e4cd410` | Prepare public documentation | written after the first clean-up step |
| `a9f7d5e` | Add MIT license and third-party notices | written after the first clean-up step |

Later commits are ordinary commits made after the clean-up. The merges with `main` have the second
parents `e3dfa1f` and `54803ff`.

## game/super-mario-coop

Mario's own history is described in its branch. Its earlier commits (`63d1e85` … `77a5b4e` and the merge
`59d1bae`, 2026-10-18 02:48–02:56) are part of `main` (merged in `e3dfa1f`).
