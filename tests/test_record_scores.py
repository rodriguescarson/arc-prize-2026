"""The unattended score recorder: it must catch a new draw, name its variant and its memory arm,
skip what is already recorded or not yet scored, and never touch an existing row.
Run: uv run python tests/test_record_scores.py"""
import re

from arc_prize_2026.arc3 import record_scores as rs

BOT = ("arc3-auto variant=v6-swift-level-memory kernel=carsonrodrigues/arc3-duck-v6-swift-lm "
       "version=2 rev=abc1234")
CONTROL = "arc3-auto variant=v3-swift kernel=carsonrodrigues/arc3-duck-v3-swift version=1 rev=def5678"


def row(ref, desc, status="SubmissionStatus.COMPLETE", score="26.4", date="2026-10-19 00:12:00"):
    return {"ref": ref, "description": desc, "status": status, "publicScore": score, "date": date}


def test_describe_reads_variant_and_memory_arm():
    d = rs.describe(row("57300001", BOT))
    assert d["variant"] == "v6-swift-level-memory"
    assert d["kernel"] == "carsonrodrigues/arc3-duck-v6-swift-lm" and d["version"] == "2"
    assert d["memory"] == "ON"
    assert rs.describe(row("57300002", CONTROL))["memory"] == "OFF"
    # an explorer submission from this workspace has no variant= field; fall back to the kernel
    plain = rs.describe(row("57300003", "E16 noise draw: v7 agent memory OFF (kernel mem0 v9)"))
    assert plain["memory"] == "n/a" and plain["variant"] != ""


def test_new_rows_filters(monkeypatch=None):
    known = sorted(rs.recorded_ids(rs.SUBMISSIONS.read_text()))
    assert "57199354" in known and "57123503" in known, known[:5]
    rows = [
        row("57199354", BOT),                                  # already recorded -> skip
        row("57300001", BOT),                                  # new and scored    -> keep
        row("57300002", CONTROL, status="SubmissionStatus.PENDING", score=""),   # pending -> skip
        row("57300003", CONTROL, score=""),                    # complete, no score -> skip
    ]
    out = rs.new_rows(rows)
    assert [r["ref"] for r, _, _ in out] == ["57300001"], out


def test_render_is_a_complete_table_row():
    r = rs.render(row("57300001", BOT), rs.describe(row("57300001", BOT)), 26.4, 9)
    assert r["md"].startswith("| 9 | 57300001 |") and r["md"].endswith("|")
    assert r["md"].count("|") == 11, r["md"]          # same column count as the table
    assert "**26.4**" in r["md"] and "level memory ON" in r["md"]
    assert r["csv"].count(",") >= 12 and "57300001" in r["csv"]
    assert "26.4" in r["log"]


def test_ids_are_read_from_the_real_table():
    text = rs.SUBMISSIONS.read_text()
    assert len(rs.recorded_ids(text)) >= 4
    assert rs.next_index() == len(re.findall(r"^\| \d+ \|", text, re.M)) + 1


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
