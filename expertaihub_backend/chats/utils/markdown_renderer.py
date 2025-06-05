# chats/utils/renderers.py

import markdown
from bs4 import BeautifulSoup

# 1) Configure Python-Markdown with GFM-style extensions
MD = markdown.Markdown(
    extensions=[
        "extra",      # tables, fenced code blocks, footnotes, etc.
        "sane_lists", # better list handling
        "smarty",     # typographic replacements
    ],
    output_format="html5",
)

# 2) Tailwind classes for each HTML tag you care about:
CLASS_MAP = {
    "h3":   ["text-xl", "font-base", "leading-tight", "font-cormorant", "mt-4", "mb-2"],
    "strong": ["font-semibold"],
    "p":    ["mt-2", "text-lg", "font-base", "whitespace-pre-wrap", "font-cormorant"],
    "ul":   ["list-disc", "ml-6", "space-y-1"],
    "ol":   ["list-decimal", "ml-6", "space-y-1"],
    "li":   ["mt-1", "marker:font-semibold"],
}


def render_markdown_to_html(markdown_text: str) -> str:
    """
    Convert a Markdown string to HTML with Tailwind 'prose'-style classes injected
    on certain tags. Returns the final <html> snippet as a string.
    """
    # 1) Convert MD → raw HTML
    html = MD.reset().convert(markdown_text)

    # 2) Parse & inject classes into specific tags
    soup = BeautifulSoup(html, "html.parser")
    for tag_name, tw_classes in CLASS_MAP.items():
        for tag in soup.find_all(tag_name):
            existing = tag.get("class", [])
            tag["class"] = existing + tw_classes

    # 3) Return the modified HTML (as a string). You will wrap it in
    #    <div class="prose dark:prose-invert"> on the frontend.
    return str(soup)
