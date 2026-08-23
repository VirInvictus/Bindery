#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def fix_body(content: str) -> str:
    return re.sub(
        r"(<body[^>]*>)\s*(</body>)",
        r"\1\n  <div></div>\n\2",
        content,
        flags=re.IGNORECASE,
    )


def test_fix():
    src = Path("unworthy_gods.epub")
    dst = Path("unworthy_gods_fixed.epub")
    if not src.exists():
        print("source not found")
        return

    modified = False
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith((".html", ".xhtml", ".xml")):
                try:
                    text = content.decode("utf-8")
                    fixed = fix_body(text)
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
        if 'element "body" incomplete' not in res.stderr:
            print("SUCCESS! Empty body errors resolved!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")


if __name__ == "__main__":
    test_fix()
