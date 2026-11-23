"""Render final_research_report.md to PDF (Markdown -> HTML with Mermaid/MathJax -> Qt WebEngine)."""
import re, sys
from pathlib import Path
import markdown
from PySide6.QtCore import QUrl, QTimer, QMarginsF
from PySide6.QtGui import QPageLayout, QPageSize
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView

HERE = Path(__file__).resolve().parent
src = (HERE / "final_research_report.md").read_text()
src = re.sub(r"^---\n.*?\n---\n", "", src, flags=re.S)          # drop YAML front matter
# protect math from markdown
maths = []
def keep(m): maths.append(m.group(0)); return f"@@MATH{len(maths)-1}@@"
src = re.sub(r"\$\$.+?\$\$|\$[^$\n]+?\$", keep, src, flags=re.S)
body = markdown.markdown(src, extensions=["tables", "fenced_code", "toc"])
body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
              lambda m: '<div class="mermaid">' + m.group(1) + '</div>', body, flags=re.S)
for i, mth in enumerate(maths):
    body = body.replace(f"@@MATH{i}@@", mth)
html = f"""<!doctype html><html><head><meta charset="utf-8">
<script>window.MathJax={{tex:{{inlineMath:[['$','$']]}}}};</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
 body{{font-family:Georgia,serif;font-size:10.5pt;line-height:1.45;max-width:780px;margin:auto;color:#111}}
 h1{{font-size:20pt;color:#2f3d0a;margin-bottom:2px}} h2{{font-size:14pt;border-bottom:1px solid #90AF13;padding-bottom:2px;margin-top:22px}}
 h3{{font-size:12pt}} table{{border-collapse:collapse;width:100%;font-size:9pt;margin:8px 0}}
 th,td{{border:1px solid #bbb;padding:3px 5px;vertical-align:top}} th{{background:#eef3dc}}
 code{{font-size:8.5pt;background:#f4f4f4}} pre{{background:#f4f4f4;padding:6px;font-size:8.5pt;white-space:pre-wrap}}
 img{{max-width:100%;display:block;margin:6px auto;border:1px solid #ddd}} .mermaid{{text-align:center;margin:8px 0}}
 h2,h3{{page-break-after:avoid}} img,table,.mermaid{{page-break-inside:avoid}}
</style></head><body>{body}
<script>mermaid.initialize({{startOnLoad:true,theme:'neutral'}});</script></body></html>"""
(HERE / "final_research_report.html").write_text(html)

app = QApplication(sys.argv)
view = QWebEngineView()
from PySide6.QtWebEngineCore import QWebEngineSettings
view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
def done(path):
    print("PDF written:", path); app.quit()
def printpdf(ok):
    layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait, QMarginsF(15, 15, 15, 15))
    QTimer.singleShot(6000, lambda: view.page().printToPdf(str(HERE / "final_research_report.pdf"), layout))
view.page().pdfPrintingFinished.connect(lambda p, ok: done(p))
view.loadFinished.connect(printpdf)
view.load(QUrl.fromLocalFile(str(HERE / "final_research_report.html")))
QTimer.singleShot(60000, app.quit)
app.exec()
