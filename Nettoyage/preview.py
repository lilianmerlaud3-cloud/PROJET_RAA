import markdown
from pathlib import Path

md = Path("README.md").read_text(encoding="utf-8")

html = markdown.markdown(md)

Path("preview.html").write_text(html, encoding="utf-8")