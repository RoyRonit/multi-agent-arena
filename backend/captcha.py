"""ASCII-art captcha that doubles as a shared-password gate.

The access phrase is rendered as a block-letter banner (never sent as plaintext). A human
reads the banner and types the phrase to enter; casual bots and drive-by URL visitors can't.
The art is deterministic for a given phrase, with light stable noise so it reads as a captcha.
"""
from __future__ import annotations

FONT: dict[str, list[str]] = {
    "A": ["###", "# #", "###", "# #", "# #"],
    "B": ["###", "# #", "###", "# #", "###"],
    "C": ["###", "#  ", "#  ", "#  ", "###"],
    "D": ["## ", "# #", "# #", "# #", "## "],
    "E": ["###", "#  ", "###", "#  ", "###"],
    "F": ["###", "#  ", "###", "#  ", "#  "],
    "G": ["###", "#  ", "# #", "# #", "###"],
    "H": ["# #", "# #", "###", "# #", "# #"],
    "I": ["###", " # ", " # ", " # ", "###"],
    "J": ["###", "  #", "  #", "# #", "###"],
    "K": ["#  #", "# # ", "##  ", "# # ", "#  #"],
    "L": ["#  ", "#  ", "#  ", "#  ", "###"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#  #", "## #", "# ##", "#  #", "#  #"],
    "O": ["###", "# #", "# #", "# #", "###"],
    "P": ["###", "# #", "###", "#  ", "#  "],
    "Q": ["### ", "#  #", "#  #", "## #", "####"],
    "R": ["###", "# #", "###", "## ", "# #"],
    "S": ["###", "#  ", "###", "  #", "###"],
    "T": ["###", " # ", " # ", " # ", " # "],
    "U": ["# #", "# #", "# #", "# #", "###"],
    "V": ["# #", "# #", "# #", "# #", " # "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["# #", "# #", " # ", "# #", "# #"],
    "Y": ["# #", "# #", " # ", " # ", " # "],
    "Z": ["###", "  #", " # ", "#  ", "###"],
    "0": ["###", "# #", "# #", "# #", "###"],
    "1": [" # ", "## ", " # ", " # ", "###"],
    "2": ["###", "  #", "###", "#  ", "###"],
    "3": ["###", "  #", "###", "  #", "###"],
    "4": ["# #", "# #", "###", "  #", "  #"],
    "5": ["###", "#  ", "###", "  #", "###"],
    "6": ["###", "#  ", "###", "# #", "###"],
    "7": ["###", "  #", " # ", " # ", " # "],
    "8": ["###", "# #", "###", "# #", "###"],
    "9": ["###", "# #", "###", "  #", "###"],
    " ": ["   ", "   ", "   ", "   ", "   "],
    "-": ["   ", "   ", "###", "   ", "   "],
}

_ROWS = 5
_BLOCK = "█"
_NOISE = "·"


def normalize(phrase: str) -> str:
    return "".join(ch for ch in phrase.strip().upper() if ch in FONT)


def render(phrase: str) -> str:
    """Return the multi-line ASCII banner for `phrase`."""
    chars = [ch for ch in normalize(phrase)] or [" "]
    lines: list[str] = []
    for r in range(_ROWS):
        row_parts = []
        for ch in chars:
            glyph = FONT.get(ch, FONT[" "])
            row_parts.append(glyph[r])
        line = "  ".join(row_parts)  # 2-space gutter between letters
        lines.append(_decorate(line, r))
    # light top/bottom noise band for captcha texture
    width = max(len(l) for l in lines)
    return "\n".join(l.ljust(width) for l in lines)


def _decorate(line: str, row: int) -> str:
    """Render blocks, and drop stable low-density noise into empty cells."""
    out = []
    for col, cell in enumerate(line):
        if cell == "#":
            out.append(_BLOCK)
        elif cell == " " and ((col * 7 + row * 13) % 17 == 0):
            out.append(_NOISE)
        else:
            out.append(" ")
    return "".join(out)
