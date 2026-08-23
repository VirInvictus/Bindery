#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def fix_illegal_tags(content: str) -> str:
    # A list of fake/deprecated tags that cause massive epubcheck failures.
    # We will safely unwrap them (remove the tags, keep the text inside).
    # Note: We do NOT include <image> or MathML tags here because they might be valid SVG/MathML.
    illegal_tags = ["st", "font", "sentence", "o", "w", "pagebreak"]

    for tag in illegal_tags:
        # Strip the opening tag (and its attributes)
        content = re.sub(rf"<{tag}\b[^>]*>", "", content, flags=re.IGNORECASE)
        # Strip the closing tag
        content = re.sub(rf"</{tag}\s*>", "", content, flags=re.IGNORECASE)

    return content


def test_fix():
    src = Path("leaves_of_grass.epub")
    dst = Path("leaves_of_grass_tags_fixed.epub")

    shutil.copy(src, dst)
    modified = False

    fd, temp_path = tempfile.mkstemp()
    os.close(fd)

    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(temp_path, "w") as zout:
        for item in zin.infolist():
            content = zin.read(item.filename)
            if item.filename.endswith((".html", ".xhtml", ".xml", ".htm")):
                try:
                    text = content.decode("utf-8", errors="ignore")
                    fixed = fix_illegal_tags(text)
                    if fixed != text:
                        content = fixed.encode("utf-8")
                        modified = True
                except Exception:
                    pass
            zout.writestr(item, content)

    if modified:
        shutil.move(temp_path, dst)
        print("Modified files, running epubcheck...")
        res = subprocess.run(["epubcheck", str(dst)], capture_output=True, text=True)
        if 'element "st" not allowed anywhere' not in res.stderr:
            print("SUCCESS! Illegal tags removed safely!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")


if __name__ == "__main__":
    test_fix()
