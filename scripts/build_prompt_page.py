"""Build an offline prompt reader from the maintained skill sources."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
GROUPS = [
    ("论文视频", "paper-video", "guided"),
    ("配音与双语字幕", "local-narration", "gpt"),
    ("文献综述与 HTML", "literature-review-html", "guided"),
    ("单篇论文 HTML", "paper-reading-html", "guided"),
]


def main():
    cards = []
    for title, skill, detailed in GROUPS:
        parts = []
        for label, relative in [
            ("本机 skill", "SKILL.md"),
            ("通用精炼版", "prompts/concise.md"),
            ("精细指导版", f"prompts/{detailed}.md"),
        ]:
            source = ROOT / "skills" / skill / relative
            parts.append(
                f'<details><summary>{label}</summary><div class="actions">'
                f'<button type="button">复制全文</button><a href="../skills/{skill}/{relative}">源文件</a>'
                f'</div><pre tabindex="0">{escape(source.read_text(encoding="utf-8"))}</pre></details>'
            )
        cards.append(f'<section id="{skill}"><h2>{title}</h2>{"".join(parts)}</section>')
    page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>论文制作 · 可复用 prompts</title><style>
:root{font-family:system-ui,-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:#26302f;background:#f7f6f2}
body{margin:0;line-height:1.7}main{max-width:1040px;margin:auto;padding:36px 24px 70px}h1{line-height:1.25;font-size:clamp(27px,4vw,40px)}h2{font-size:24px;margin-bottom:14px}a{color:#246d70}nav{display:flex;gap:18px;flex-wrap:wrap}section{margin:40px 0}details{background:#fff;border:1px solid #dce0da;border-radius:8px;margin:12px 0;padding:14px 18px}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:15px;line-height:1.8;margin-bottom:8px}.actions{display:flex;align-items:center;gap:16px;margin:18px 0}button{font:inherit;cursor:pointer;background:#246d70;color:white;border:0;border-radius:5px;padding:7px 18px}button:focus-visible,a:focus-visible,summary:focus-visible{outline:3px solid #e5ab49;outline-offset:4px}.note{color:#556560;max-width:900px}#copy-status{min-height:1.7em;color:#246d70}
</style></head><body><main><nav><a href="index.html">预览与风格样片</a><a href="https://github.com/lizihan25/Paper-Explainer-Skills">GitHub 仓库</a></nav>
<h1>论文制作 · 可复用 prompts</h1>
<p class="note">2026-10-26 更新。选择用途，再展开所需版本。通用版和指导版可独立复制；本机 skill 需连同对应目录内的资源一起安装。配音默认固定 F、1.1 倍、中上英下字幕；视频依次优先机制动画、论文证据导览、纸面自由画布、原图显微镜，当前人类要求优先。<a href="index.html#style-index">看封面和视频选风格</a>。</p>
<nav><a href="#paper-video">视频</a><a href="#local-narration">配音与字幕</a><a href="#literature-review-html">文献综述</a><a href="#paper-reading-html">单篇阅读</a></nav>
<p id="copy-status" role="status" aria-live="polite"></p>
""" + "".join(cards) + """
</main><script>
for(const button of document.querySelectorAll('button')) button.addEventListener('click',async()=>{
  const text=button.closest('details').querySelector('pre').textContent;
  const status=document.getElementById('copy-status');
  try{await navigator.clipboard.writeText(text);status.textContent='已复制，可粘贴到模型对话或指令中。';}
  catch{const range=document.createRange();range.selectNodeContents(button.closest('details').querySelector('pre'));const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);status.textContent='全文已选中，请按 Ctrl+C 或 Command+C 复制。';}
});
</script></body></html>"""
    target = ROOT / "examples/prompts.html"
    target.write_text(page, encoding="utf-8")
    print(f"Built {target.relative_to(ROOT)} from {len(GROUPS) * 3} source files")


if __name__ == "__main__":
    main()
