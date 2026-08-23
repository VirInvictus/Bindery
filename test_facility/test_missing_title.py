#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


def fix_title(content: str) -> str:
    # First, replace empty self-closing or empty open-close titles
    # <title/> or <title></title> or <title  />
    content = re.sub(
        r"<title[^>]*/>", r"<title>Unknown</title>", content, flags=re.IGNORECASE
    )
    content = re.sub(
        r"<title[^>]*>\s*</title>",
        r"<title>Unknown</title>",
        content,
        flags=re.IGNORECASE,
    )

    # Now check if it's completely missing
    head_m = re.search(r"<head[^>]*>(.*?)</head>", content, re.IGNORECASE | re.DOTALL)
    if head_m:
        if not re.search(
            r"<title[^>]*>.*?</title>", head_m.group(1), re.IGNORECASE | re.DOTALL
        ):
            content = re.sub(
                r"(</head>)",
                r"<title>Unknown</title>\n\1",
                content,
                flags=re.IGNORECASE,
            )
    return content


def test_fix():
    src = Path("muse_of_nightmares.epub")
    dst = Path("muse_of_nightmares_fixed.epub")

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
                    fixed = fix_title(text)
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
        if (
            'Element "title" must not be empty' not in res.stderr
            and 'The "head" element should have a "title"' not in res.stderr
        ):
            print("SUCCESS! Missing title errors resolved!")
        else:
            print("FAILED!")
            print(res.stderr)
    else:
        print("No files modified.")


if __name__ == "__main__":
    test_fix()
