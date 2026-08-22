#!/usr/bin/env python3
import re
import sys
import zipfile
import shutil
from pathlib import Path
import subprocess

def fix_ncx(content: str) -> str:
    counter = [0]
    def repl(match):
        counter[0] += 1
        return f'playOrder="{counter[0]}"'
    
    return re.sub(r'\bplayOrder\s*=\s*["\'].*?["\']', repl, content, flags=re.IGNORECASE)

def test_fix():
    src = Path("poor_mans_fight.epub")
    dst = Path("poor_mans_fight_fixed.epub")
    if not src.exists():
        print("source not found")
        return
    
    shutil.copy(src, dst)
    ncx_path = None
    
    with zipfile.ZipFile(src, 'r') as zin:
        for name in zin.namelist():
            if name.endswith('.ncx'):
                ncx_path = name
                content = zin.read(name).decode("utf-8")
                break
                
    if not ncx_path:
        print("no ncx found")
        return
        
    fixed_content = fix_ncx(content)
    
    # write to fixed epub
    with zipfile.ZipFile(dst, 'a') as zout:
        zout.writestr(ncx_path, fixed_content.encode("utf-8"))
        
    print(f"Fixed {ncx_path}")
    
    # Verify with epubcheck
    res = subprocess.run(["epubcheck", str(dst)], capture_output=True, text=True)
    if "identical playOrder values" not in res.stderr and "playOrder sequence has gaps" not in res.stderr:
        print("SUCCESS! No playOrder duplicate or gap errors found by epubcheck!")
    else:
        print("FAILED!")
        print(res.stderr)

if __name__ == "__main__":
    test_fix()
