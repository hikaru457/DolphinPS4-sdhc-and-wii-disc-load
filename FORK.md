# This fork

Based on Dolphin for PS4 **v04.13** (iHaiDeeZ/DolphinPS4). The original patch is untouched
(`patches/dolphin-ps4.patch`); everything this fork adds is one patch on top, `patches/fork-mods.patch`,
so a new upstream version only needs that patch checked again.

## What it adds

| | |
|---|---|
| **SD cards up to 32 GB** | Settings -> System -> *SD Card Size*: 4, 8, 16 and 32 GB (SDHC). Dolphin already emulates SDHC for cards over 2 GB. A ready-made `WiiSD.raw` of any size also works. |
| **Wii Disc** | Settings -> System -> *Wii Disc*: the disc in the Wii's drive for the Wii Menu, `.wad` files and Wii `.dol` / `.elf` programs. The list is the disc images of the games folder, read when the app starts. A `launch.txt` `disc=` line still wins. |
| **Project M, native** | See [PROJECT-M.md](PROJECT-M.md): the mod's `codes/*.gct` and `gameconfig.txt` are read from the SD folder or the card image, in any letter case. |

## Building

`.github/workflows/build-pkg.yml` builds the package on GitHub (Actions -> Run workflow). The scripts
of this repository are set up for the author's experimental "Dolphin Lab" copy (`DLPH00011`,
version 01.00); the workflow sets `PS4_TITLE_ID=DLPH00010`, `PS4_APP_NAME=Dolphin`,
`PS4_CONTENT_LABEL=DOLPHIN` and the `VERSION` file's number, so the package is the regular app and
installs over it. Leave the version box empty to use `VERSION`.

## Updates

The app checks iHaiDeeZ/DolphinPS4's releases. When upstream publishes a version newer than this
one, accepting the update replaces this build with the original (no SDHC sizes, Wii Disc or native
Project M). Decline it, or rebuild this fork on the new version.
