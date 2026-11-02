"""Record newly scored Kaggle submissions into the paper's records, once per day, unattended.

From 2026-10-17 the LLM-harness draws are made by the bot in ~/Projects/arc-agi-3 (paired
level-memory variants and their no-memory twins, two draws each). Each draw is scored about nine
hours later, and the paper needs every score written down with the variant that produced it. Doing
that by hand needs a session open every morning for two weeks, so this does it instead.

Reads `kaggle competitions submissions --csv`, finds COMPLETE rows with a public score whose
submission id is not yet in `submission/SUBMISSIONS.md`, and appends one row per record file. It
never edits an existing row, so re-running is safe and a row corrected by hand stays corrected.

    uv run python -m arc_prize_2026.arc3.record_scores --dry-run     # print what would be written
    uv run python -m arc_prize_2026.arc3.record_scores --commit      # write, commit and push

The variant name is read from the submission's own description, which the bot writes as
`arc3-auto variant=<name> kernel=<slug> version=<n>`; an explorer submission from this workspace
carries its kernel slug instead.
"""
from __future__ import annotations

import csv
import io
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
COMP = "arc-prize-2026-arc-agi-3"
IST = ZoneInfo("Asia/Kolkata")
SUBMISSIONS = ROOT / "submission" / "SUBMISSIONS.md"
LOG = ROOT / "RESEARCH_LOG.md"
CSV_LOG = ROOT / "EXPERIMENT_LOG.csv"
VARIANT_RE = re.compile(r"variant=(?P<variant>[\w.-]+)")
KERNEL_RE = re.compile(r"kernel=(?P<kernel>[\w/-]+)(?:\s+version=(?P<version>\d+))?")
#: level memory is the paper's treatment; its twin is the control. Everything else is context.
MEMORY_ON = {"v2-level-memory", "v6-swift-level-memory", "v7-drain-memory"}
MEMORY_OFF = {"v1-franzen-faithful", "v3-swift", "v4-effort-medium"}


def kaggle(*args: str) -> str:
    """The Kaggle CLI, from this repo's venv or the PATH."""
    for exe in (ROOT / ".venv/bin/kaggle", Path.home() / "Projects/gemma-swe-agent/.venv/bin/kaggle", Path("kaggle")):
        if exe == Path("kaggle") or exe.exists():
            try:
                return subprocess.run([str(exe), *args], capture_output=True, text=True, check=True, timeout=120).stdout
            except FileNotFoundError:
                continue
    raise RuntimeError("no kaggle CLI found")


def fetch() -> list[dict]:
    out = kaggle("competitions", "submissions", "-c", COMP, "--csv")
    start = out.find("ref,")                      # the CLI prints a banner before the CSV
    rows = list(csv.DictReader(io.StringIO(out[start:] if start >= 0 else out)))
    return [r for r in rows if r.get("ref")]


def recorded_ids(text: str) -> set[str]:
    return set(re.findall(r"\b(\d{8})\b", text))


def pending_ids(text: str) -> set[str]:
    """Ids whose row was written before the score existed: status PENDING and an empty score cell.

    A submission made by the scheduler is recorded the moment it is accepted, hours before Kaggle scores
    it. Treating any id already in the file as finished meant those rows kept their PENDING status for
    good (57248168 sat at PENDING with a blank score until this was fixed). Completing such a row is not
    editing a result, so a row that already carries a score is still never touched.
    """
    out = set()
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        ids = [c for c in cells if re.fullmatch(r"\d{8}", c)]
        if ids and "PENDING" in line and any(c == "" for c in cells[-3:]):
            out.add(ids[0])
    return out


def fill_pending(text: str, ref: str, score: float, status: str = "COMPLETE") -> tuple[str, bool]:
    """Put the score into that submission's PENDING row. Returns the new text and whether it changed."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("|") and ref in line and "PENDING" in line:
            cells = line.split("|")
            for j, c in enumerate(cells):
                if c.strip() == "PENDING":
                    cells[j] = f" {status} "
                    for k in range(j + 1, len(cells)):
                        if cells[k].strip() == "":
                            cells[k] = f" **{score:g}** "
                            break
                    break
            lines[i] = "|".join(cells)
            return "\n".join(lines) + ("\n" if text.endswith("\n") else ""), True
    return text, False


def describe(row: dict) -> dict:
    d = row.get("description", "") or ""
    variant = (VARIANT_RE.search(d) or {}).group("variant") if VARIANT_RE.search(d) else None
    km = KERNEL_RE.search(d)
    kernel = km.group("kernel") if km else ""
    version = km.group("version") if km and km.group("version") else ""
    memory = "ON" if variant in MEMORY_ON else "OFF" if variant in MEMORY_OFF else "n/a"
    return {"variant": variant or kernel or "unknown", "kernel": kernel, "version": version, "memory": memory}


def score_of(row: dict) -> float | None:
    v = (row.get("publicScore") or "").strip()
    try:
        return float(v)
    except ValueError:
        return None


def new_rows(rows: list[dict]) -> list[tuple[dict, dict, float]]:
    text = SUBMISSIONS.read_text()
    known, pending = recorded_ids(text), pending_ids(text)
    out = []
    for r in rows:
        score = score_of(r)
        if score is None or "COMPLETE" not in (r.get("status") or ""):
            continue
        if r["ref"] in known and r["ref"] not in pending:
            continue
        out.append((r, describe(r), score))
    return sorted(out, key=lambda t: t[0].get("date", ""))


def render(row: dict, info: dict, score: float, index: int) -> dict[str, str]:
    when = (row.get("date") or "")[:16]
    ist = ""
    try:
        ist = datetime.fromisoformat(when).replace(tzinfo=timezone.utc).astimezone(IST).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        ist = when
    mem = f", level memory {info['memory']}" if info["memory"] != "n/a" else ""
    return {
        "md": (f"| {index} | {row['ref']} | {info['kernel'] or 'see description'}"
               f"{' v' + info['version'] if info['version'] else ''} | {info['variant']}{mem} | — | — | {ist} | COMPLETE | "
               f"**{score:g}** | recorded automatically from the Kaggle submission list |"),
        "log": (f"- {ist.split()[-1]} **Draw scored: {row['ref']} ({info['variant']}{mem}) = {score:g}** "
                f"on the 55 hidden games. Recorded automatically; the paired comparison is read only when both "
                f"arms of a pair have their draws (see NEXT_ACTIONS and the pre-registered 11-point rule)."),
        "csv": (f"kaggle_{row['ref']}_{info['variant'].replace('-', '_')},{ist},daily draw recorded automatically,"
                f"{info['variant']},n/a,\"{{\"\"submission_id\"\": {row['ref']}, \"\"level_memory\"\": \"\"{info['memory']}\"\"}}\","
                f"ARC-AGI-3/hidden-public-55,55,{score:f},-1,-1.0,evaluation,automatic record; variant from the submission description"),
    }


def next_index() -> int:
    nums = [int(m) for m in re.findall(r"^\| (\d+) \|", SUBMISSIONS.read_text(), re.M)]
    return (max(nums) + 1) if nums else 1


def apply(items: list[tuple[dict, dict, float]]) -> list[str]:
    lines, idx = [], next_index()
    md = SUBMISSIONS.read_text()
    log_add, csv_add = [], []
    pending = pending_ids(md)
    for row, info, score in items:
        r = render(row, info, score, idx)
        if row["ref"] in pending:                       # complete the row the scheduler left PENDING
            md, done = fill_pending(md, row["ref"], score)
            if done:
                log_add.append(r["log"])
                csv_add.append(r["csv"])
                lines.append(f"filled PENDING row for {row['ref']} with {score:g}")
                continue
        anchor = "\nRules: 1 submission per day"
        md = md.replace(anchor, "\n" + r["md"] + anchor, 1) if anchor in md else md + "\n" + r["md"] + "\n"
        log_add.append(r["log"])
        csv_add.append(r["csv"])
        lines.append(r["md"])
        idx += 1
    SUBMISSIONS.write_text(md)
    today = datetime.now(IST).strftime("## %Y-%m-%d")
    log = LOG.read_text()
    LOG.write_text(log + ("" if today in log else f"\n{today}\n") + "\n".join(log_add) + "\n")
    with CSV_LOG.open("a") as f:
        f.write("\n".join(csv_add) + "\n")
    return lines


def main(argv: list[str]) -> int:
    items = new_rows(fetch())
    if not items:
        print("no newly scored submissions")
        return 0
    if "--dry-run" in argv:
        for row, info, score in items:
            print(render(row, info, score, next_index())["md"])
        return 0
    written = apply(items)
    print("\n".join(written))
    if "--commit" in argv:
        refs = ", ".join(r["ref"] for r, _, _ in items)
        # Only the three record files: `git add -A` once swept two stray untracked files into a record commit.
        paths = [str(p.relative_to(ROOT)) for p in (SUBMISSIONS, LOG, CSV_LOG)]
        subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)
        message = f"Daily draw scores recorded: {refs}"
        subprocess.run(["git", "commit", "-m", message, "--", *paths], cwd=ROOT, check=True)
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
