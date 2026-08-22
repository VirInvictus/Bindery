#!/usr/bin/env python3
import re
import sys
import zipfile
import shutil
from pathlib import Path
import subprocess
import tempfile
import os

def fix_invalid_ids(content: str) -> str:
    # Fix id="foo:bar"
    def repl_id(m):
        quote = m.group(1)
        val = m.group(2)
        # replace colon with underscore
        new_val = val.replace(":", "_")
        return f'id={quote}{new_val}{quote}'
        
    content = re.sub(r'\bid\s*=\s*(["\'])([^"\']*:[^"\']*)\1', repl_id, content, flags=re.IGNORECASE)
    
    # Fix href="something#foo:bar"
    def repl_href(m):
        quote = m.group(1)
        val = m.group(2)
        if '#' in val:
            path, frag = val.split('#', 1)
            new_frag = frag.replace(":", "_")
            new_val = f"{path}#{new_frag}"
            return f'href={quote}{new_val}{quote}'
        return m.group(0)
        
    content = re.sub(r'\bhref\s*=\s*(["\'])([^"\']+)\1', repl_href, content, flags=re.IGNORECASE)
    return content

def test_fix():
    src = Path("agda.epub")
    dst = Path("agda_fixed.epub")
    
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
                    fixed = fix_invalid_ids(text)
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
        if "value of attribute \"id\" is invalid" not in res.stderr:
            print("SUCCESS! Invalid ID colons resolved!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")

if __name__ == "__main__":
    test_fix()
