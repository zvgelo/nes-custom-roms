# Commit map – cleaned-up development history

Before the first publication the history of `game/galaxian-coop` was cleaned up in three steps, without
changing `main` or the history shared with it:

1. **First squash** (2026-10-20): 65 Galaxian-only development commits → 19 commits.
2. **Second squash** (2026-10-20): short commits of one stage combined again.
3. **Branch separation** (2026-10-20): the merge of the Mario documentation commit (`Merge Mario docs`,
   `c67826a`, second parent `da68d18`) and a later copy of the Mario folder were removed from this branch.
   `games/super-mario-coop/` here is exactly what the branch inherits from `main`; Mario is developed only
   on `game/super-mario-coop`.

Older documents (CHANGELOG, IMPLEMENTATION_REPORT, history/TESTING_HISTORY) quote commit IDs from before
these steps; they are not part of the published history. This table maps them to the published commits.
Apart from the Mario folder and the root README (which the Mario merge had changed), every published
commit has the tree of the last commit of its group; the only other content changes, made in step 1, were
references to a private test setup replaced by neutral wording.

## game/galaxian-coop

| Published commit | Message | After step 2 | After step 1 | Original development commits (oldest first) |
|---|---|---|---|---|
| `e09f2be` | Add Galaxian co-op ROM hack | `e09f2be` | `576a44b`, `46ec512`, `90b0eb8` | `ccf390b` Add Galaxian stage 1, `067eff8` Rename mod to Galaxian Coop, `7310245` Add 6502 assembler; `c6140d1` Add player 2 ship and movement, `5267eef` Add P2 combat, lives and HUD; `8a35d3b` Add BPS patch output, `bce9287` Add stage 2 BPS patch, `2b5d3d9` Add emulator tests, `16dff0e` Rename folder to galaxian-coop, `32680b7` Add Mesen label export, `3080e8d` Add Galaxian Coop docs |
| `20a671d` | Merge main into Galaxian | `9228f1f` | `08806b0` | `2bbabd3` Merge main into Galaxian |
| `58b8c56` | Move private inputs out of the tree | `564d837` | `d93fde0` | `dd9cb11` Move Galaxian input to private, `0ae3387` Update Galaxian docs |
| `1f9ee01` | Merge main into Galaxian | `6cd5509` | `eb85998` | `2998015` Merge main into Galaxian |
| `e48bcf4` | Add lives HUD, life sharing and weapon progression | `9b55184` | `a6af1e2`, `7700f60`, `45f8ade` | `740ef8f` Fix top screen artifacts, `06a98ca` Improve lives HUD; `efe3eb2` Add life sharing, `660389e` Add title credits, `c1e87f7` Add coop tests, `03ed0bd` Fix stray HUD tile, `1a6a7fd` Unify lives display; `3ba7a0a` Add weapon boost, `7823b63` Add W4, banners, spawns, badge, `3a9415c` Add boost and banner tests, `72c31f7` Rename outputs, update BPS, `4f6281c` Add Galaxian build guide |
| `39d0474` | Add respawn shield and stabilize weapons and CPU use | `9050cd3` | `0f40098`, `0f2cc03`, `79eba26` | `0e079ae` Update tools list, `f77d5ad` Check W4 lag frames, `fb94d58` Add implementation report; `ee68486` Fix fire input, `53a8266` Fix death weapon reset, `3545da4` Fix stage one boost, `e676f90` Add respawn shield, `2a140a2` Add shield blinking, `d26e470` Fix fire after respawn, `daa49bb` Add weapon regression tests, `b67e532` Test respawn protection, `dfce5a9` Update RC2 docs; `0bc21ef` Fix P1 ghost shooting, `d817e59` Verify weapon parity, `49d6981` Optimize frame budget, `60268b2` Add RC3 tests, `1073733` Add FCEUmm checks, `ae7f469` Update RC3 docs |
| `f7979ff` | Add overdrive and distinct player visuals | `e7e550f` | `0b7c8db`, `5447a5f` | `309bdfc` Fix score HUD corruption, `d925e73` Add overdrive power-up, `bf500a8` Add RC4 regression tests, `3b9d13e` Update RC4 docs, `1e73f0c` Give free W2 to waiting pilots; `b3cfe91` Improve player colors, `48a8cba` Differentiate coop ships, `5281576` Add visual regression tests, `02b59b7` Update RC5 docs |
| `005dfc8` | Unify solo and co-op rules and rework overdrive | `23902d3` | `c26798f`, `e4d0a17` | `8f30ee0` Unify player progression, `4776844` Enable solo respawn shield, `5cdd24c` Enable solo stage HUD, `54e0d94` Restore demo firing, `aa44399` Add solo parity tests; `5fe537d` Strengthen overdrive aggression, `4577b68` Start overdrive with next stage, `ece6f71` Fix solo HUD after co-op, `69d58d9` Add overdrive and HUD tests, `f9fa8b6` Update RC6 docs |
| (following commits) | Prepare public documentation; Add MIT license and third-party notices | `0c31b5e`, `21c58ab`, `5b0d2f6` | `2f7f29a` and later | written after step 1 |

The merges with `main` keep their second parents `694580d` and `bdb84e6`.

## game/super-mario-coop

Mario's own history is described in its branch. Its earlier commits (`db728c4` … `bcc3b93`,
2026-10-18 02:48–02:57) belong to `main` (merged in `694580d`) and were not changed.
