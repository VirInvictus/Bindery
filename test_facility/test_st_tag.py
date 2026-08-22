#!/usr/bin/env python3
import re
import zipfile
import shutil
import tempfile
import os
from pathlib import Path
import subprocess

def fix_st_tag(content: str) -> str:
    content = re.sub(r'<st\b[^>]*>', '', content, flags=re.IGNORECASE)
    content = re.sub(r'</st\s*>', '', content, flags=re.IGNORECASE)
    return content

def test_fix():
    src = Path("leaves_of_grass.epub")
    dst = Path("leaves_of_grass_st_fixed.epub")
    
    shutil.copy(src, dst)
    modified = False
    
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    
    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(temp_path, 'w') as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith(('.html', '.xhtml', '.xml', '.htm')):
                try:
                    text = content.decode('utf-8', errors='ignore')
                    fixed = fix_st_tag(text)
                    if fixed != text:
                        content = fixed.encode('utf-8')
                        modified = True
                except Exception:
                    pass
            zout.writestr(item, content)
            
    if modified:
        shutil.move(temp_path, dst)
        print("Modified files, running epubcheck...")
        res = subprocess.run(["epubcheck", str(dst)], capture_output=True, text=True)
        if "element \"st\" not allowed anywhere" not in res.stderr:
            print("SUCCESS! All <st> tags removed!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")

if __name__ == "__main__":
    test_fix()
