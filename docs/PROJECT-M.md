# Project M and other Gecko OS mods

Project M, Project+ and the BrawlEX mods start through **Gecko OS** (the `boot.elf` loader), which
can't run inside the emulator. This fork does its job itself, and serves the mod's files as part of
Brawl's disc, so the game finds them in its own file system. Nothing of the mod is changed, and its
`boot.elf`, `APPS` folders and `private` exploit files are not needed.

## Setup (two steps)

1. Copy the mod's files to `/data/DolphinPS4/User/Load/ProjectM/`:
   ```
   ProjectM/
     codes/RSBE01.gct
     gameconfig.txt
     pf/            (the mod's pf folder: stages, character select screen, music...)
   ```
   Names can be in any letter case (`rsbe01.gct`, `PF`, `GameConfig.TXT`).
2. Start your Brawl (NTSC-U, `RSBE01`) from the library.

That's all: no SD card, no *Wii Disc*, no settings. The screen shows *Gecko OS mod: ...* when the
mod's code list is installed, and `dolphin.log` says what was found and where.

## What it does

- Reads `codes/<GAME ID>.gct` (`RSBE01.gct`, then `RSB.gct`, `RSBE.gct`) and runs it as a Gecko
  code named *GCT: RSBE01.gct*. It appears in the Cheats menu, on by default.
- Reads `gameconfig.txt`: `codeliststart` / `codelistend` (where the code list lives; Project M uses
  64 KB or more, far beyond Dolphin's own 3 KB), and the `poke` / `pokeifequal` lines, applied once
  with the game in memory and before it runs. `searchandpoke` and `hook` lines are not supported.
- Adds the mod's `pf` folder to the disc, as the Riivolution version of Project M does: its files
  replace the ones of Brawl's `/pf` and the new ones (new stages, music, BrawlEX files) are created.
  It is looked for in `User/Load/ProjectM/pf`, then `User/Load/WiiSDSync/projectm/pf`, then
  `User/Load/Riivolution/projectm/pf`.
- The codes and `gameconfig.txt` are looked for in the same folders and, last, in the SD card image
  (`User/Load/WiiSD.raw`), so a mod that already sits on a card image works too.

## Using an SD card as well

The mod's codes may also read the SD card. If you keep one (`User/Load/WiiSD.raw`, FAT32, with
*SD Card Folder* off and *SD Card Writes* on), a card over 2 GB works too: see below. The files are
served from the disc as soon as `pf` is in one of the folders above, whatever the card holds.

## Why an SD card over 2 GB needs IOS 58

An SDHC card (over 2 GB) is only initialised by the IOS versions that know it (48, 56-62, 70, 80).
A game normally runs on the IOS its disc asks for (Brawl: IOS 36), which doesn't, so the game sees a
card that was never initialised: nothing can be read from it. On a real Wii Project M's loader
reloads IOS 58 before it starts Brawl; this fork does the same: when the SD card is over 2 GB and the
game's own IOS can't use it, the game starts on IOS 58. The boot log says *SDHC card: the game
starts on IOS 58*. Not needed with a card of 2 GB or less, or if you set *Override Boot IOS* yourself.

## If it doesn't work

- `dolphin.log`: lines starting with *GCT ...* (the code list and where it came from) and
  *gameconfig.txt ...* (the code list region and the pokes). No *GCT* line means the file was not
  found (check the name and the folder); *bigger than the code space* means `gameconfig.txt` has no
  `codeliststart` / `codelistend`.
- The boot log says *projectm: the pf folder is served as part of the disc* when `pf` was found.
- Other regions need their own list (`RSBP01.gct` for PAL).
