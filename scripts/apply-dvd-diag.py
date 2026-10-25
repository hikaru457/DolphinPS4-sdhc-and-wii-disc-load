#!/usr/bin/env python3
"""Diagnostic only: when the game asks the DVD for a position past the end of the disc (the read
that ends in "An error has occurred. Press the Eject Button..."), write to dolphin.log which file of
the game's own file table that position belongs to.

usage: apply-dvd-diag.py <path of the Dolphin source tree>
"""
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(__doc__)
path = Path(sys.argv[1]) / "Source" / "Core" / "Core" / "IOS" / "DI" / "DI.cpp"
if not path.is_file():
    sys.exit(f"apply-dvd-diag: ERROR: {path} not found")
s = path.read_text(encoding="utf-8")
if "fork diagnostic: DVD read past the end" in s:
    print("apply-dvd-diag: already applied")
    sys.exit(0)

m = re.search(r'INFO_LOG_FMT\(\s*IOS_DI,\s*"DVDLowRead: offset', s)
if not m:
    sys.exit('apply-dvd-diag: ERROR: the "DVDLowRead" log line was not found in DI.cpp')
end = s.find(";", m.end())
if end < 0:
    sys.exit("apply-dvd-diag: ERROR: statement end not found")
nl = s.find("\n", end) + 1

BLOCK = r'''    // fork diagnostic: DVD read past the end of the disc. Say which file the game was after.
    if ((static_cast<u64>(position) << 2) >= 0x1FB500000ULL)
    {
      static int s_oob_reports = 0;
      if (s_oob_reports++ < 8)
      {
        const u32 fst_phys = memory.Read_U32(0x38) & 0x3FFFFFFF;
        const u32 entries = fst_phys != 0 && fst_phys < 0x01800000 ? memory.Read_U32(fst_phys + 8) : 0;
        bool found = false;
        if (entries > 1 && entries < 100000 && fst_phys + entries * 12 < 0x01800000)
        {
          const u32 names = fst_phys + entries * 12;
          for (u32 i = 1; i < entries && !found; ++i)
          {
            const u32 e = fst_phys + i * 12;
            const u32 w0 = memory.Read_U32(e);
            if ((w0 >> 24) != 0)  // a directory
              continue;
            const u32 off = memory.Read_U32(e + 4);
            const u32 size = memory.Read_U32(e + 8);
            if (position < off || static_cast<u64>(position - off) * 4 >= size)
              continue;
            std::string name;
            for (u32 k = 0; k < 96 && names + (w0 & 0xFFFFFF) + k < 0x01800000; ++k)
            {
              const char c = static_cast<char>(memory.Read_U8(names + (w0 & 0xFFFFFF) + k));
              if (c == 0)
                break;
              name += c;
            }
            NOTICE_LOG_FMT(IOS_DI,
                           "DVD read past the end: FST entry {} \"{}\" (offset field {:#x}, size "
                           "{:#x}), read at +{:#x} bytes",
                           i, name, off, size, static_cast<u64>(position - off) * 4);
            found = true;
          }
        }
        if (!found)
        {
          NOTICE_LOG_FMT(IOS_DI,
                         "DVD read past the end: no file of the game's FST (at {:#x}, {} entries) "
                         "contains offset field {:#x}",
                         fst_phys, entries, position);
        }
      }
    }
'''
s = s[:nl] + BLOCK + s[nl:]
if "#include <string>" not in s:
    s = s.replace("#include <memory>\n", "#include <memory>\n#include <string>\n", 1)
path.write_text(s, encoding="utf-8", newline="")
print("apply-dvd-diag: DI.cpp ok")
