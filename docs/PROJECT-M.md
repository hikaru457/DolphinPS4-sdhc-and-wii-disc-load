# Project M and other Gecko OS mods

Project M, Project+ and the BrawlEX mods start through **Gecko OS** (the `boot.elf` loader). Gecko OS
can't run inside the emulator, so this fork does its job itself: it reads the files Gecko OS would
read and applies them when Brawl starts. Nothing of the mod is changed, and its `boot.elf`,
`APPS` folders and `private` exploit files are not needed.

## Setup

1. Put your Brawl (NTSC-U, `RSBE01`) in the games folder.
2. Give the emulator the mod's SD card, in either form:
   - **A card image:** copy your `WiiSD.raw` (FAT32, 8 GB or more) to
     `/data/DolphinPS4/User/Load/WiiSD.raw`. Settings -> System: *SD Card Folder* off,
     *SD Card Writes* on.
   - **A folder:** the card's files under `/data/DolphinPS4/User/Load/WiiSDSync/`. With *SD Card
     Folder* on, Dolphin packs it into a card at every start, which is slow for a mod of several GB.
3. The card needs `codes/RSBE01.gct`, `gameconfig.txt` and the mod's own folder (`PROJECTM/pf`...).
4. Start Brawl from the library. The screen shows *Gecko OS mod: gameconfig.txt read from the SD
   image (N startup pokes)* when the mod was found.

File names can be in any letter case (`rsbe01.gct`, `GameConfig.TXT`). The folder is looked at
first, then the image, so a small folder with just `codes` and `gameconfig.txt` also works next to
a big image.

## What it does

- Reads `codes/<GAME ID>.gct` (`RSBE01.gct`, then `RSB.gct`, `RSBE.gct`) and runs it as a Gecko
  code named *GCT: RSBE01.gct*. It appears in the Cheats menu, on by default.
- Reads `gameconfig.txt`: `codeliststart` / `codelistend` (where the code list lives; Project M uses
  64 KB, far more than Dolphin's own 3 KB), and the `poke` / `pokeifequal` lines, applied once with
  the game in memory and before it runs.
- Not supported: `searchandpoke`, `hook` lines. `hooktype` is only logged.

## If it doesn't work

`dolphin.log` says what happened: lines starting with *GCT ...* (the code list and where it came
from) and *gameconfig.txt ...* (the code list region and the pokes). No *GCT* line means the file was
not found on the card (check the name and the folder); *bigger than the code space* means
`gameconfig.txt` has no `codeliststart` / `codelistend`.

Other regions need their own list (`RSBP01.gct` for PAL).
