"""Lightweight Markdown-to-HTML renderer — zero external dependencies.

Extracted from AiAssistantPanel so coding_practice_view and other
components can use it without importing the AI panel module.
"""

import re

_PLACEHOLDER_PREFIX = "<!--PDP_MD_BLOCK_"
_PLACEHOLDER_SUFFIX = "-->"


def render_markdown(text: str) -> str:
    """Convert common markdown patterns to HTML suitable for QTextBrowser.

    Supported: fenced code blocks, inline code, bold, italic,
               h2/h3/h4 headings, unordered/ordered lists,
               horizontal rules, blockquotes.
    """
    # 1. escape HTML entities first
    out = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 2. protect fenced code blocks from later regex mangling
    blocks: list[str] = []

    def _store_code(m: re.Match) -> str:
        code = m.group(2).strip()
        blocks.append(
            f"<pre style='background:#e8e3da; border-radius:6px; padding:10px; "
            f"margin:8px 0; overflow-x:auto;'>"
            f"<code>{code}</code></pre>"
        )
        return f"{_PLACEHOLDER_PREFIX}{len(blocks) - 1}{_PLACEHOLDER_SUFFIX}"

    out = re.sub(r"```(\w*)\n?(.*?)```", _store_code, out, flags=re.DOTALL)

    # 3. inline code `...`
    out = re.sub(
        r"`([^`]+?)`",
        r"<code style='background:#e8e3da; padding:1px 5px; "
        r"border-radius:3px; font-family:monospace;'>\1</code>",
        out,
    )

    # 4. bold **...**
    out = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", out)

    # 5. italic *...* (single asterisk)
    out = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", out)

    # 6. headings
    out = re.sub(r"^#### (.+)$", r"<h4 style='margin:8px 0 4px;'>\1</h4>", out, flags=re.MULTILINE)
    out = re.sub(r"^### (.+)$", r"<h3 style='margin:10px 0 4px;'>\1</h3>", out, flags=re.MULTILINE)
    out = re.sub(r"^## (.+)$", r"<h2 style='margin:12px 0 4px;'>\1</h2>", out, flags=re.MULTILINE)

    # 7. unordered lists — wrap each `- ` / `* ` line, merge neighbours
    out = _wrap_list_blocks(out, r"^[ \t]*[-*] ", "ul")

    # 8. numbered lists — same treatment
    out = _wrap_list_blocks(out, r"^[ \t]*\d+\. ", "ol")

    # 9. horizontal rule
    out = re.sub(
        r"^---+$",
        r"<hr style='border:none; border-top:1px solid #e0d5c8; margin:10px 0;'>",
        out, flags=re.MULTILINE,
    )

    # 10. blockquote  (allow leading whitespace)
    out = re.sub(
        r"^[ \t]*&gt; (.+)$",
        r"<blockquote style='border-left:3px solid #6f9f98; margin:6px 0; "
        r"padding:4px 12px; color:#5b6470;'>\1</blockquote>",
        out, flags=re.MULTILINE,
    )

    # 11. remaining line breaks (won't affect placeholders)
    out = out.replace("\n", "<br>")

    # 12. restore protected code blocks
    for i, block in enumerate(blocks):
        out = out.replace(
            f"{_PLACEHOLDER_PREFIX}{i}{_PLACEHOLDER_SUFFIX}", block
        )

    return out


def _wrap_list_blocks(text: str, marker_re: str, tag: str) -> str:
    """Wrap consecutive lines matching *marker_re* in <ul> or <ol>."""
    lines = text.split("\n")
    result: list[str] = []
    buf: list[str] = []  # buffered list-item lines as <li>...</li>

    def _flush():
        if buf:
            result.append(
                f"<{tag} style='margin:4px 0; padding-left:20px;'>"
                + "".join(buf)
                + f"</{tag}>"
            )
            buf.clear()

    for line in lines:
        m = re.match(marker_re + r"(.+)$", line)
        if m:
            buf.append(f"<li style='margin:1px 0;'>{m.group(1)}</li>")
        else:
            _flush()
            result.append(line)

    _flush()
    return "\n".join(result)
