#!/usr/bin/env python3
"""Adds this fork's settings to the DolphinNoGUI files of the port (SD sizes up to 32 GB, the
"Wii Disc" setting and its use at boot).

These three files change often upstream, so the edits are anchored on the text they touch (not on
line numbers, as a patch would be) and re-running the script is harmless. If something it needs is
no longer there, it stops and says what.

usage: apply-fork-settings.py <path of the Dolphin source tree>
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1]) / "Source" / "Core" / "DolphinNoGUI"


def fail(message):
    sys.exit(f"apply-fork-settings: ERROR: {message}")


def read(name):
    path = ROOT / name
    if not path.is_file():
        fail(f"{path} not found")
    return path.read_text(encoding="utf-8")


def write(name, text):
    (ROOT / name).write_text(text, encoding="utf-8", newline="")


def match_brace(text, open_index):
    """Index of the '}' that closes the '{' at open_index (strings and comments are skipped)."""
    depth, i, n = 0, open_index, len(text)
    while i < n:
        c = text[i]
        if text.startswith("//", i):
            i = text.find("\n", i)
            if i < 0:
                break
        elif text.startswith("/*", i):
            i = text.find("*/", i)
            if i < 0:
                break
            i += 1
        elif c in "\"'":
            quote = c
            i += 1
            while i < n and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    fail("unbalanced braces")


def split_top_level(inner):
    """Splits the inside of a braced list on its top-level commas."""
    parts, depth, start, i, n = [], 0, 0, 0, len(inner)
    while i < n:
        c = inner[i]
        if c in "\"'":
            quote = c
            i += 1
            while i < n and inner[i] != quote:
                i += 2 if inner[i] == "\\" else 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append(inner[start:i])
            start = i + 1
        i += 1
    if inner[start:].strip():
        parts.append(inner[start:])
    return parts


def add_include(text, line, after_regex=None):
    if line in text:
        return text
    if after_regex:
        m = re.search(after_regex, text, re.M)
        if m:
            return text[: m.end()] + "\n" + line + text[m.end():]
    last = None
    for m in re.finditer(r"^#include .*$", text[:6000], re.M):
        last = m
    if not last:
        fail(f"no #include to anchor {line}")
    return text[: last.end()] + "\n" + line + text[last.end():]


# ======================================================================== PS4Settings.cpp
HELPER = r'''namespace
{
// The discs a Wii program can find "inserted" in the drive (Settings -> System -> Wii Disc): the
// disc images of the games folder. Choice holds plain pointers, so the strings live here (filled
// once, in Load).
std::deque<std::string> s_disc_strings;

void FillDiscChoices(const std::string& data_dir)
{
  static const char* const EXTENSIONS[] = {".iso", ".gcm", ".ciso", ".gcz",
                                           ".wbfs", ".wia", ".rvz"};
  const std::string games_dir = PS4XMB::GamesDir(data_dir);
  std::vector<std::string> names;
  std::error_code error;
  std::filesystem::directory_iterator it(games_dir, error);
  const std::filesystem::directory_iterator end;
  for (; !error && it != end; it.increment(error))
  {
    std::error_code file_error;
    if (!it->is_regular_file(file_error))
      continue;
    const std::string name = it->path().filename().string();
    std::string lower = name;
    std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
    for (const char* extension : EXTENSIONS)
    {
      const std::string ext = extension;
      if (lower.size() > ext.size() &&
          lower.compare(lower.size() - ext.size(), ext.size(), ext) == 0)
      {
        names.push_back(name);
        break;
      }
    }
  }
  std::sort(names.begin(), names.end());
  for (Setting& setting : SETTINGS)
  {
    if (std::string(setting.key) != "wii_disc")
      continue;
    setting.choices = {{"none", "None"}};
    s_disc_strings.clear();
    for (const std::string& name : names)
    {
      s_disc_strings.push_back(games_dir + "/" + name);  // the stored value
      const char* value = s_disc_strings.back().c_str();
      s_disc_strings.push_back(name);  // the label
      setting.choices.push_back({value, s_disc_strings.back().c_str()});
    }
  }
}
}  // namespace

'''

WII_DISC_ENTRY = (
    '{"wii_disc", "Wii Disc", "System", {{"none", "None"}}, "none", false,\n'
    '     "The disc in the Wii\'s drive for the Wii Menu, .wad files and Wii homebrew (.dol / .elf, '
    'such "\n'
    '     "as the Project M loader). The list is read when the app starts."}'
)


def patch_settings():
    s = read("PS4Settings.cpp")
    s = add_include(s, "#include <deque>", r"^#include <cstdlib>$")
    s = add_include(s, '#include "DolphinNoGUI/PS4XMB.h"', r'^#include "Core/Config/MainSettings.h"$')

    # The list of settings must be writable: the Wii Disc choices are filled at start-up.
    m = re.search(r"\bconst\s+std::vector<Setting>\s+SETTINGS\b", s)
    if m:
        s = s[: m.start()] + "std::vector<Setting> SETTINGS" + s[m.end():]
    elif not re.search(r"(?<!const )std::vector<Setting>\s+SETTINGS\b", s):
        fail("PS4Settings.cpp: the SETTINGS list was not found")

    # --- SD card sizes up to 32 GB
    m = re.search(r'\{\s*"sd_size"', s)
    if not m:
        fail('PS4Settings.cpp: the "sd_size" setting was not found')
    end = match_brace(s, m.start())
    entry = s[m.start(): end + 1]
    if '"4096"' not in entry:
        m2 = re.search(r'\{\s*"2048"\s*,\s*"2 GB"\s*\}', entry)
        if not m2:
            fail('PS4Settings.cpp: the "2 GB" option of "sd_size" was not found')
        extra = (', {"4096", "4 GB (SDHC)"}, {"8192", "8 GB (SDHC)"},\n'
                 '      {"16384", "16 GB (SDHC)"}, {"32768", "32 GB (SDHC)"}')
        entry = entry[: m2.end()] + extra + entry[m2.end():]
        s = s[: m.start()] + entry + s[end + 1:]
        end = m.start() + len(entry) - 1

    # --- the Wii Disc setting, right after "sd_size"
    if not re.search(r'\{\s*"wii_disc"\s*,', s):
        fields = split_top_level(entry[1:-1])
        if len(fields) != 7:
            fail(f'PS4Settings.cpp: a setting has {len(fields)} fields here, this script knows 7 '
                 "(key, label, category, choices, fallback, live, help)")
        j = end + 1
        while j < len(s) and s[j] in " \t":
            j += 1
        if j < len(s) and s[j] == ",":
            s = s[: j + 1] + "\n    " + WII_DISC_ENTRY + "," + s[j + 1:]
        else:
            s = s[: end + 1] + ",\n    " + WII_DISC_ENTRY + s[end + 1:]

    # --- fill the choices when the settings are loaded
    if "FillDiscChoices" not in s:
        m = re.search(r"^void\s+Load\s*\(\s*const\s+std::string&\s*(\w+)\s*\)\s*\n?\s*\{", s, re.M)
        if not m:
            fail("PS4Settings.cpp: PS4Settings::Load(const std::string&) was not found")
        param = m.group(1)
        body_open = s.index("{", m.start())
        body_close = match_brace(s, body_open)
        s = s[:body_close] + f"  FillDiscChoices({param});\n" + s[body_close:]
        s = s[: m.start()] + HELPER + s[m.start():]
    write("PS4Settings.cpp", s)
    print("apply-fork-settings: PS4Settings.cpp ok (SD sizes, Wii Disc)")


# ======================================================================== PS4XMB.cpp
def patch_xmb():
    s = read("PS4XMB.cpp")
    m = re.search(r"WII_ONLY\s*=\s*\{", s)
    if not m:
        fail("PS4XMB.cpp: the WII_ONLY list was not found")
    end = match_brace(s, m.end() - 1)
    block = s[m.end() - 1: end + 1]
    if '"wii_disc"' not in block:
        if '"sd_size"' not in block:
            fail('PS4XMB.cpp: "sd_size" is not in the WII_ONLY list any more')
        block = block.replace('"sd_size"', '"sd_size", "wii_disc"', 1)
        s = s[: m.end() - 1] + block + s[end + 1:]
    write("PS4XMB.cpp", s)
    print("apply-fork-settings: PS4XMB.cpp ok (Wii Disc only for Wii games)")


# ======================================================================== MainNoGUI.cpp
WII_DISC_BOOT = (
    "    // Settings -> System -> Wii Disc: the disc for the Wii Menu, .wad files and Wii programs\n"
    "    // (Dolphin's default ISO). A disc chosen some other way for this run (launch.txt's disc=)\n"
    "    // is not replaced.\n"
    "    {\n"
    '      const std::string wii_disc = Platform::GetPS4Option("wii_disc", "none");\n'
    '      if (wii_disc != "none" && File::Exists(wii_disc) &&\n'
    "          Config::Get(Config::MAIN_DEFAULT_ISO).empty())\n"
    "        Config::SetCurrent(Config::MAIN_DEFAULT_ISO, wii_disc);\n"
    "    }\n"
)


def statement_end(text, pos):
    """Index just after the ';' that ends the statement `pos` is inside (parentheses balanced)."""
    depth, i, n = 0, pos, len(text)
    while i < n:
        c = text[i]
        if c in "\"'":
            quote = c
            i += 1
            while i < n and text[i] != quote:
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == ";" and depth <= 0:
            return i + 1
        i += 1
    fail("MainNoGUI.cpp: statement without end")


def patch_main():
    s = read("MainNoGUI.cpp")
    if "GetPS4Option(\"wii_disc\"" not in s:
        # The place where the port applies the SD card settings is the most stable anchor: the same
        # run, before the game boots. (Dolphin's default ISO is only read when a program or the
        # Wii Menu boots, and a launch_disc set elsewhere is respected: see WII_DISC_BOOT.)
        for anchor in (r'GetPS4Option\(\s*"sd_size"', r"MAIN_ALLOW_SD_WRITES", r"MAIN_WII_SD_CARD_FILESIZE"):
            m = re.search(anchor, s)
            if m:
                end = statement_end(s, m.start())
                nl = s.find("\n", end)
                nl = len(s) if nl < 0 else nl + 1
                s = s[:nl] + WII_DISC_BOOT + s[nl:]
                break
        else:
            m = re.search(r'^([ \t]*).*GetPS4Option\(\s*"launch_disc"', s, re.M)
            if not m:
                fail("MainNoGUI.cpp: neither the SD card settings nor the launch_disc handling "
                     "were found")
            s = s[: m.start()] + WII_DISC_BOOT + s[m.start():]
    write("MainNoGUI.cpp", s)
    print("apply-fork-settings: MainNoGUI.cpp ok (Wii Disc at boot)")


patch_settings()
patch_xmb()
patch_main()
