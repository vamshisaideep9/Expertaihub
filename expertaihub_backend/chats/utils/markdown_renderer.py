import markdown
from bs4 import BeautifulSoup

# configure Python-Markdown with GFM-style extensions
MD = markdown.Markdown(
    extensions=[
        "extra",      # tables, fenced code blocks, footnotes, etc.
        "sane_lists", # better list handling
        "smarty",     # typographic replacements
    ],
    output_format="html5",
)

# mapping of tag → list of Tailwind classes (tighter vertical rhythm)
CLASS_MAP = {
    "h3":   ["text-xl", "font-base", "leading-tight", "font-cormorant", "mt-4", "mb-2"],
    "strong": ["font-semibold"],
    "p":    ["mt-2", "text-lg", "font-base", "whitespace-pre-wrap", "font-cormorant"],
    "ul":   ["list-disc", "ml-6", "space-y-1"],
    "ol":   ["list-decimal", "ml-6", "space-y-1"],
    "li":   ["mt-1", "marker:font-semibold"],
}

def render_markdown_to_html(markdown_text: str) -> str:
    # 1) Convert MD → raw HTML
    html = MD.reset().convert(markdown_text)

    # 2) Parse & inject classes
    soup = BeautifulSoup(html, "html.parser")
    for tag_name, classes in CLASS_MAP.items():
        for tag in soup.find_all(tag_name):
            existing = tag.get("class", [])
            tag["class"] = existing + classes

    return str(soup)
