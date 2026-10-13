"""Helpers for editing paper/draft.md and regenerating paper/writeup_clean.md (tag-stripped Kaggle writeup)."""
import re
from pathlib import Path
P = Path("paper/draft.md")
def rep_ws(s, old, new):
    """Replace `old` in `s`, matching any whitespace run (line wraps differ); fail loudly if absent."""
    pat = r"\s+".join(re.escape(w) for w in old.split()); m = re.search(pat, s)
    assert m, "NOT FOUND: " + old[:70]
    return s[:m.start()] + new + s[m.end():]
def regen(s):
    """Write writeup_clean.md; return (words excluding pure-punctuation tokens such as table pipes, prose words without table rows)."""
    clean = re.sub(r"\s?\[measured:[^\]]*\]", "", s, flags=re.S)
    clean = re.sub(r"\s?\[pending:[^\]]*\]", "", clean, flags=re.S)
    clean = re.sub(r"\n\*Working draft[^*]*\*\n", "\n", clean, flags=re.S)
    clean = clean.replace("## Abstract (draft)", "## Abstract")
    Path("paper/writeup_clean.md").write_text(clean)
    words = [w for w in clean.split() if re.search(r"[A-Za-z0-9]", w)]
    prose = re.sub(r"^\|.*$", "", clean, flags=re.M)
    return len(words), len(prose.split())
