#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def fix_invalid_value(content: str) -> str:
    # Remove value="X" from elements that shouldn't have it
    def repl(m):
        tag = m.group(1)
        before = m.group(2)
        after = m.group(4)
        return f"<{tag} {before}{after}>"

    return re.sub(
        r'<(div|span|p|a|img|h[1-6]|ul|table|tr|td|th)\s+([^>]*\b)?value\s*=\s*(["\'][^"\']*["\'])([^>]*)>',
        repl,
        content,
        flags=re.IGNORECASE,
    )


def test_fix():
    src = Path("leaves_of_grass.epub")
    dst = Path("leaves_of_grass_fixed.epub")

    shutil.copy(src, dst)
    modified = False

    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith((".html", ".xhtml", ".xml")):
                try:
                    text = content.decode("utf-8")
                    fixed = fix_invalid_value(text)
                    if fixed != text:
                        content = fixed.encode("utf-8")
                        modified = True
                except UnicodeDecodeError:
                    pass
            zout.writestr(item, content)

    if modified:
        shutil.move(temp_path, dst)
        print("Modified files, running epubcheck...")
        res = subprocess.run(["epubcheck", str(dst)], capture_output=True, text=True)
        if 'attribute "value" not allowed here' not in res.stderr:
            print("SUCCESS! Invalid value attribute resolved!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")


if __name__ == "__main__":
    test_fix()
