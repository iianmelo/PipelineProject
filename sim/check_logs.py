#!/usr/bin/env python3
"""Check simulation logs against the values derived from the RTL."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

WRITE_RE = re.compile(
    r"Register\s+\[\s*(\d+)\]\s+written with value:\s+\[([0-9A-Fa-f]+)\]"
)
MEM_WRITE_RE = re.compile(
    r"Memory\s+\[\s*(\d+)\]\s+written with value:\s+\[([0-9A-Fa-f]+)\]"
)


def writes(path):
    text = path.read_text(errors="replace")
    regs = {}
    seen = set()
    for reg, value in WRITE_RE.findall(text):
        regs[int(reg)] = int(value, 16)
        seen.add(int(reg))
    mems = {}
    for addr, value in MEM_WRITE_RE.findall(text):
        mems[int(addr)] = int(value, 16)
    return text, regs, seen, mems


def expect_regs(name, regs, seen, expected, absent):
    ok = True
    for reg, value in expected.items():
        if reg not in seen or regs.get(reg) != value:
            print(f"FAIL {name}: x{reg} expected {value}, log has {regs.get(reg)!r}")
            ok = False
    for reg in absent:
        if reg in seen:
            print(f"FAIL {name}: x{reg} was written with {regs.get(reg)}")
            ok = False
    return ok


def main():
    ok = True

    text, regs, seen, mems = writes(BUILD / "original.log")
    ok &= expect_regs("original", regs, seen, {7: 1, 8: 2, 2: 3}, [])
    for needle in (
        "45: Register [ 7] written with value: [00000001]",
        "55: Register [ 8] written with value: [00000002]",
        "75: Register [ 2] written with value: [00000003]",
        "35: Memory [  0] read with value: [00000001]",
        "50: Memory [  4] read with value: [00000002]",
    ):
        if needle not in text:
            print(f"FAIL original: missing line {needle!r}")
            ok = False
    if mems:
        print(f"FAIL original: unexpected memory writes {mems}")
        ok = False

    _, regs, seen, mems = writes(BUILD / "forward_branch.log")
    ok &= expect_regs(
        "forward_branch",
        regs,
        seen,
        {1: 5, 2: 3, 3: 8, 4: 5, 5: 1, 6: 7, 7: 6, 9: 8},
        [8],
    )
    if mems.get(8) != 8:
        print(f"FAIL forward_branch: mem[8] = {mems.get(8)!r}")
        ok = False

    _, regs, seen, mems = writes(BUILD / "lacunas.log")
    ok &= expect_regs(
        "lacunas",
        regs,
        seen,
        {1: 5, 2: 3, 3: 0, 4: 6, 5: 1, 7: 5, 9: 10},
        [6, 8, 10],
    )
    if mems:
        print(f"FAIL lacunas: unexpected memory writes {mems}")
        ok = False

    if not ok:
        sys.exit(1)
    print("simulation logs match the expected architectural results")


if __name__ == "__main__":
    main()
