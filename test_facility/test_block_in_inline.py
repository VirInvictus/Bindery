#!/usr/bin/env python3
import re
import sys
import zipfile
import shutil
import tempfile
import os
from pathlib import Path
import subprocess

def fix_block_in_inline(content: str) -> str:
    # A very common calibre conversion bug is wrapping a pagebreak div in a span:
    # <span class="calibre8"><div class="calibre6" id="calibre_pb_122"></div></span>
    # We will safely unwrap the span if the ONLY content of the span is an empty div or p.
    
    def repl(m):
        # We just drop the span and keep the div
        return m.group(2)
        
    return re.sub(r'<span[^>]*>\s*(<(div|p|blockquote)[^>]*>\s*</\2>)\s*</span>', repl, content, flags=re.IGNORECASE)

def test_fix():
    src = Path("last_man_out.epub")
    dst = Path("last_man_out_fixed.epub")
    
    shutil.copy(src, dst)
    modified = False
    
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    
    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(temp_path, 'w') as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith(('.html', '.xhtml', '.xml')):
                try:
                    text = content.decode('utf-8')
                    fixed = fix_block_in_inline(text)
                    if fixed != text:
                        content = fixed.encode('utf-8')
                        modified = True
                except UnicodeDecodeError:
                    pass
            zout.writestr(item, content)
            
    if modified:
        shutil.move(temp_path, dst)
        print("Modified files, running epubcheck...")
        res = subprocess.run(["epubcheck", str(dst)], capture_output=True, text=True)
        if "element \"span\" not allowed here" not in res.stderr and "element \"div\" not allowed here" not in res.stderr:
            print("SUCCESS! Block in inline resolved!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")

if __name__ == "__main__":
    test_fix()
