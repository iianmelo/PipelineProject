#!/usr/bin/env python3
"""Render pipeline figures from the Icarus VCD dumps.

Outputs, all derived from the simulated traces:
  docs/diagrams/pipeline_timing.svg
  docs/diagrams/pipeline_timing.png
  docs/waveforms/pipeline_original.svg
  docs/waveforms/pipeline_original.png
  docs/waveforms/pipeline_forward_branch.svg
  docs/waveforms/pipeline_forward_branch.png
"""

from __future__ import annotations

import html
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
DIAG = ROOT / "docs" / "diagrams"
WAVE = ROOT / "docs" / "waveforms"

for font in (
    "/usr/share/fonts/truetype/macos/Inter-Regular.ttf",
    "/usr/share/fonts/truetype/macos/Inter-Medium.ttf",
    "/usr/share/fonts/truetype/macos/Inter-SemiBold.ttf",
    "/usr/share/fonts/truetype/macos/Inter-Bold.ttf",
):
    font_manager.fontManager.addfont(font)

plt.rcParams["font.family"] = "Inter"
plt.rcParams["svg.fonttype"] = "none"

INK = "#1C2430"
MUTED = "#5E6A75"
PAPER = "#F7F5F2"
GRID = "#E4DDD2"
RULE = "#D5CBBC"

STAGE_INK = {
    "IF": "#1D4E89",
    "ID": "#0E7C66",
    "EX": "#8A5A00",
    "MEM": "#6C3B8A",
    "WB": "#8C2F39",
}
STAGE_FILL = {
    "IF": "#D9E7F6",
    "ID": "#D5F0E8",
    "EX": "#F8E7C4",
    "MEM": "#EADCF4",
    "WB": "#F6D9D6",
}


def parse_vcd(path):
    names = {}
    current = {}
    series = []
    in_defs = True
    time_ps = 0
    with open(path) as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("$var"):
                parts = line.split()
                names[parts[3]] = parts[4]
                continue
            if line.startswith("$enddefinitions"):
                in_defs = False
                continue
            if in_defs or line.startswith("$"):
                continue
            if line.startswith("#"):
                series.append((time_ps, dict(current)))
                time_ps = int(line[1:])
                continue
            if line[0] in "bB":
                payload, ident = line[1:].rsplit(None, 1)
                current[names[ident]] = payload
            elif line[0] in "01xXzZ":
                current[names[line[1:]]] = line[0]
    series.append((time_ps, dict(current)))
    return series


class Trace:
    def __init__(self, series):
        self.times = [t for t, _ in series]
        self.snaps = []
        last = {}
        for _, change in series:
            last = dict(last)
            last.update(change)
            self.snaps.append(last)

    def at(self, name, time_ns):
        target = int(round(time_ns * 1000))
        chosen = self.snaps[0]
        for time_ps, snap in zip(self.times, self.snaps):
            if time_ps <= target:
                chosen = snap
            else:
                break
        return chosen.get(name)

    def posedges(self, until_ns):
        edges = []
        prev = "0"
        for time_ps, snap in zip(self.times, self.snaps):
            clk = snap.get("tb_clk", prev)
            if prev != "1" and clk == "1" and time_ps / 1000 <= until_ns:
                edges.append(time_ps / 1000)
            prev = clk
        return edges


def as_int(value):
    if value is None or any(ch in value for ch in "xXzZ"):
        return None
    return int(value, 2)


def decode(word):
    if word is None:
        return "x"
    if word == 0:
        return "—"
    op = word & 0x7F
    rd = (word >> 7) & 0x1F
    funct3 = (word >> 12) & 0x7
    rs1 = (word >> 15) & 0x1F
    rs2 = (word >> 20) & 0x1F
    funct7 = (word >> 25) & 0x7F
    if op == 0b0110011:
        name = {
            (0, 0): "add",
            (0, 0b0100000): "sub",
            (1, 0): "sll",
            (2, 0): "slt",
            (3, 0): "sltu",
            (4, 0): "xor",
            (5, 0): "srl",
            (5, 0b0100000): "sra",
            (6, 0): "or",
            (7, 0): "and",
        }.get((funct3, funct7), "r?")
        return f"{name} x{rd}, x{rs1}, x{rs2}"
    if op == 0b0000011:
        imm = (word >> 20) & 0xFFF
        if imm & 0x800:
            imm -= 0x1000
        name = {2: "lw"}.get(funct3, "load")
        return f"{name} x{rd}, {imm}(x{rs1})"
    if op == 0b0100011:
        imm = ((word >> 25) << 5) | ((word >> 7) & 0x1F)
        if imm & 0x800:
            imm -= 0x1000
        return f"sw x{rs2}, {imm}(x{rs1})"
    if op == 0b1100011:
        imm = (
            (((word >> 31) & 1) << 12)
            | (((word >> 7) & 1) << 11)
            | (((word >> 25) & 0x3F) << 5)
            | (((word >> 8) & 0xF) << 1)
        )
        if imm & 0x1000:
            imm -= 0x2000
        name = {0: "beq", 1: "bne"}.get(funct3, "br")
        return f"{name} x{rs1}, x{rs2}, {imm:+d}"
    if op == 0b0010011 and funct3 == 0:
        imm = (word >> 20) & 0xFFF
        if imm & 0x800:
            imm -= 0x1000
        return f"addi x{rd}, x{rs1}, {imm}"
    return f"{word:08x}"


WIDTHS = {"A": 41, "B": 170, "C": 211, "D": 199}


def pad_bits(value, width):
    """Right-align a VCD vector. A lone x/z means the whole bus is unknown."""
    if value is None:
        return None
    value = value.lower()
    if value in ("x", "z"):
        return value * width
    if len(value) < width:
        value = value.rjust(width, "0")
    return value[-width:]


def bit_at(value, width, index):
    bits = pad_bits(value, width)
    if bits is None:
        return "x"
    return bits[width - 1 - index]


def stage_text(raw, kind):
    if kind == "A":
        bits = pad_bits(raw, 41)
        if bits is None or any(ch in bits[-32:] for ch in "xz"):
            return "—" if bits is not None else "x"
        return decode(int(bits[-32:], 2))

    width = WIDTHS[kind]
    bits = pad_bits(raw, width)
    if bits is None:
        return "x"
    if kind == "B":
        flags = [bit_at(raw, width, i) for i in (167, 166, 165, 162)]
    elif kind == "C":
        flags = [bit_at(raw, width, i) for i in (210, 208, 207)]
    else:
        flags = [bit_at(raw, width, 198)]
    if any(flag == "x" for flag in flags):
        return "x"
    word_bits = bits[-32:]
    if not any(flag == "1" for flag in flags):
        if any(ch in word_bits for ch in "xz") or set(word_bits) <= {"0"}:
            return "—"
        return "bolha"
    if any(ch in word_bits for ch in "xz"):
        return "x"
    return decode(int(word_bits, 2))


def compact(text):
    if text in ("—", "bolha", "x", None):
        return text
    return text.split(",")[0]


def kind_of(text):
    if text in ("—", "bolha", "x"):
        return "empty"
    if text.startswith(("lw", "sw")):
        return "mem"
    if text.startswith(("beq", "bne")):
        return "branch"
    return "alu"


def collect_cycles(trace, until_ns):
    cycles = []
    for time_ns in trace.posedges(until_ns):
        after = time_ns + 1
        mid = time_ns + 6
        reg_write = as_int(trace.at("reg_write_sig", after))
        cycles.append(
            {
                "t": time_ns,
                "IF": decode(as_int(trace.at("Instr", mid))),
                "ID": stage_text(trace.at("A", after), "A"),
                "EX": stage_text(trace.at("B", after), "B"),
                "MEM": stage_text(trace.at("C", after), "C"),
                "WB": stage_text(trace.at("D", after), "D"),
                "stall": as_int(trace.at("Reg_Stall", after)) or 0,
                "pcsel": as_int(trace.at("PcSel", after)) or 0,
                "fa": as_int(trace.at("FAmuxSel", after)),
                "fb": as_int(trace.at("FBmuxSel", after)),
                "alu": as_int(trace.at("ALUResult", after)),
                "reg_write": reg_write or 0,
                "reg_num": as_int(trace.at("reg_num", after)),
                "reg_data": as_int(trace.at("reg_data", after)),
            }
        )
    return cycles


def cell_colors(text):
    kind = kind_of(text)
    if kind == "mem":
        return "#D9E7F6", "#1D4E89"
    if kind == "branch":
        return "#F6D9D6", "#8C2F39"
    if kind == "alu":
        return "#F8E7C4", "#8A5A00"
    if text == "bolha":
        return "#E7E1D6", "#6B645B"
    return "#F3EFE8", "#A39A8C"


def draw_timing(cycles, title, subtitle, notes, svg_path, png_path):
    stages = ["IF", "ID", "EX", "MEM", "WB"]
    margin_l, margin_r, margin_t = 86, 36, 118
    col_w, row_h = 168, 58
    width = margin_l + col_w * len(cycles) + margin_r
    note_h = 28 + 22 * len(notes)
    height = margin_t + row_h * len(stages) + note_h + 28
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text { font-family: Inter, 'Noto Sans', sans-serif; }</style>",
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        f'<text x="36" y="42" fill="{INK}" font-size="26" font-weight="700">{html.escape(title)}</text>',
        f'<text x="36" y="70" fill="{MUTED}" font-size="14">{html.escape(subtitle)}</text>',
    ]
    for index, stage in enumerate(stages):
        y = margin_t + index * row_h
        parts.append(
            f'<text x="28" y="{y + 34}" fill="{STAGE_INK[stage]}" font-size="15" font-weight="700">{stage}</text>'
        )
        if index % 2 == 0:
            parts.append(
                f'<rect x="{margin_l}" y="{y}" width="{col_w * len(cycles)}" height="{row_h}" fill="#FBF9F6"/>'
            )
    for col, cycle in enumerate(cycles):
        x = margin_l + col * col_w
        parts.append(
            f'<text x="{x + col_w / 2}" y="{margin_t - 28}" text-anchor="middle" fill="{INK}" font-size="14" font-weight="700">{col}</text>'
        )
        parts.append(
            f'<text x="{x + col_w / 2}" y="{margin_t - 10}" text-anchor="middle" fill="{MUTED}" font-size="12">{cycle["t"]:.0f} ns</text>'
        )
        for row, stage in enumerate(stages):
            text = cycle[stage]
            fill, color = cell_colors(text)
            y = margin_t + row * row_h + 8
            parts.append(
                f'<rect x="{x + 8}" y="{y}" width="{col_w - 16}" height="{row_h - 16}" rx="8" fill="{fill}"/>'
            )
            cx = x + col_w / 2
            if stage == "WB" and cycle["reg_write"] and cycle["reg_num"] not in (None, 0):
                parts.append(
                    f'<text x="{cx}" y="{y + 20}" text-anchor="middle" fill="{color}" font-size="13" font-weight="600">{html.escape(text)}</text>'
                )
                parts.append(
                    f'<text x="{cx}" y="{y + 36}" text-anchor="middle" fill="{color}" font-size="11">x{cycle["reg_num"]} ← {cycle["reg_data"]}</text>'
                )
            else:
                parts.append(
                    f'<text x="{cx}" y="{y + 28}" text-anchor="middle" fill="{color}" font-size="13" font-weight="600">{html.escape(text)}</text>'
                )
        mark = []
        if cycle["stall"]:
            mark.append("stall")
        if cycle["pcsel"]:
            mark.append("branch")
        if cycle["EX"] not in ("—", "bolha", "x") and cycle["fa"] == 2:
            mark.append("fwd A")
        if cycle["EX"] not in ("—", "bolha", "x") and cycle["fb"] == 2:
            mark.append("fwd B·EX")
        if cycle["EX"] not in ("—", "bolha", "x") and (cycle["fa"] == 1 or cycle["fb"] == 1):
            which = []
            if cycle["fa"] == 1:
                which.append("A")
            if cycle["fb"] == 1:
                which.append("B")
            mark.append("fwd " + "/".join(which) + "·WB")
        if mark:
            parts.append(
                f'<text x="{x + col_w / 2}" y="{margin_t + len(stages) * row_h + 18}" text-anchor="middle" fill="#9A3412" font-size="11" font-weight="650">{html.escape(" · ".join(mark))}</text>'
            )
    note_y = margin_t + len(stages) * row_h + 48
    for index, note in enumerate(notes):
        parts.append(
            f'<text x="36" y="{note_y + index * 22}" fill="{MUTED}" font-size="13">{html.escape(note)}</text>'
        )
    parts.append("</svg>")
    svg_path.write_text("\n".join(parts))
    png_path.parent.mkdir(parents=True, exist_ok=True)


def segments(trace, name, t_end, transform):
    edges = [0.0]
    values = [transform(trace.at(name, 0))]
    for time_ps, snap in zip(trace.times, trace.snaps):
        time_ns = time_ps / 1000
        if time_ns > t_end:
            break
        value = transform(snap.get(name))
        if value != values[-1]:
            edges.append(time_ns)
            values.append(value)
    edges.append(t_end)
    return list(zip(edges, values))


def draw_waveform(trace, t_end, title, subtitle, caption, out_svg, out_png):
    rows = [
        ("clk", "bit", "tb_clk", INK),
        ("reset", "bit", "reset", "#7C4A2D"),
        ("PC", "pc", "PC", STAGE_INK["IF"]),
        ("IF  · instrução", "instr", "Instr", STAGE_INK["IF"]),
        ("ID  · IF/ID", "stageA", "A", STAGE_INK["ID"]),
        ("EX  · ID/EX", "stageB", "B", STAGE_INK["EX"]),
        ("MEM · EX/MEM", "stageC", "C", STAGE_INK["MEM"]),
        ("WB  · MEM/WB", "stageD", "D", STAGE_INK["WB"]),
        ("stall", "bit", "Reg_Stall", "#C2410C"),
        ("PcSel", "bit", "PcSel", "#8C2F39"),
        ("forward A/B", "fwd", None, "#0E7C66"),
        ("escrita", "wb", None, STAGE_INK["WB"]),
    ]

    def pc_of(value):
        number = as_int(value)
        return "x" if number is None else str(number)

    def instr_of(value):
        return decode(as_int(value))

    fig_w = 16.4 if t_end <= 100 else 18.6
    fig_h = 9.15
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    left, right = 0.0, t_end
    top = len(rows)
    ax.set_xlim(left - t_end * 0.012, right + t_end * 0.012)
    ax.set_ylim(-0.55, top + 0.15)
    for tick in range(0, int(t_end) + 1, 10):
        ax.axvline(tick, color=GRID, lw=0.6, zorder=0)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9)
    ax.set_xlabel("tempo (ns)", color=MUTED, fontsize=10, labelpad=6)
    ax.set_yticks([top - i - 0.5 for i in range(len(rows))])
    ax.set_yticklabels([name for name, *_ in rows], fontsize=10, color=INK)
    ax.tick_params(axis="y", length=0, pad=8)
    for spine in ax.spines.values():
        spine.set_color(RULE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    def y_of(index):
        return top - index - 1

    for index, (label, kind, signal, color) in enumerate(rows):
        y = y_of(index)
        if kind == "bit":
            segs = segments(trace, signal, t_end, lambda v: 0 if v in (None, "0", "x", "X") else 1)
            xs, ys = [], []
            for (start, value), (end, _) in zip(segs, segs[1:]):
                level = y + 0.18 + 0.5 * value
                xs.extend([start, end])
                ys.extend([level, level])
            # square corners
            px, py = [], []
            prev = None
            for (start, value), (end, _) in zip(segs, segs[1:]):
                level = y + 0.22 + 0.46 * value
                if prev is not None and prev != level:
                    px.append(start)
                    py.append(prev)
                px.extend([start, end])
                py.extend([level, level])
                prev = level
            ax.plot(px, py, color=color, lw=1.6, solid_capstyle="butt", zorder=3)
        elif kind in ("pc", "instr", "stageA", "stageB", "stageC", "stageD", "fwd", "wb"):
            if kind == "pc":
                segs = segments(trace, signal, t_end, pc_of)
                fill, ink = "#E7EEF6", color
            elif kind == "instr":
                segs = segments(trace, signal, t_end, instr_of)
                fill, ink = STAGE_FILL["IF"], color
            elif kind == "stageA":
                segs = segments(trace, signal, t_end, lambda v: stage_text(v, "A"))
                fill, ink = STAGE_FILL["ID"], color
            elif kind == "stageB":
                segs = segments(trace, signal, t_end, lambda v: stage_text(v, "B"))
                fill, ink = STAGE_FILL["EX"], color
            elif kind == "stageC":
                segs = segments(trace, signal, t_end, lambda v: stage_text(v, "C"))
                fill, ink = STAGE_FILL["MEM"], color
            elif kind == "stageD":
                segs = segments(trace, signal, t_end, lambda v: stage_text(v, "D"))
                fill, ink = STAGE_FILL["WB"], color
            elif kind == "fwd":
                def fwd_label(unused, t0=None):
                    return ""

                # Build from both selects, sampled on the trace times.
                edges = [0.0]
                values = ["—"]
                for time_ps in trace.times:
                    time_ns = time_ps / 1000
                    if time_ns > t_end:
                        break
                    fa = as_int(trace.at("FAmuxSel", time_ns))
                    fb = as_int(trace.at("FBmuxSel", time_ns))
                    ex = stage_text(trace.at("B", time_ns), "B")
                    names = {1: "WB", 2: "EX"}
                    parts = []
                    if ex not in ("—", "bolha", "x"):
                        if fa in names:
                            parts.append(f"A←{names[fa]}")
                        if fb in names:
                            parts.append(f"B←{names[fb]}")
                    label = " ".join(parts) if parts else "—"
                    if label != values[-1]:
                        edges.append(time_ns)
                        values.append(label)
                edges.append(t_end)
                segs = list(zip(edges, values))
                fill, ink = "#E5F4EE", "#0E7C66"
            else:
                edges = [0.0]
                values = ["—"]
                for time_ps in trace.times:
                    time_ns = time_ps / 1000
                    if time_ns > t_end:
                        break
                    enable = as_int(trace.at("reg_write_sig", time_ns))
                    if enable:
                        label = f"x{as_int(trace.at('reg_num', time_ns))} ← {as_int(trace.at('reg_data', time_ns))}"
                    else:
                        label = "—"
                    if label != values[-1]:
                        edges.append(time_ns)
                        values.append(label)
                edges.append(t_end)
                segs = list(zip(edges, values))
                fill, ink = STAGE_FILL["WB"], color

            for (start, value), (end, _) in zip(segs, segs[1:]):
                if end - start <= 0:
                    continue
                shown = value not in ("—", "x")
                ax.add_patch(
                    Rectangle(
                        (start, y + 0.14),
                        max(end - start, 0.05),
                        0.70,
                        facecolor=fill if shown else "#EFEBE4",
                        edgecolor="none",
                        zorder=2,
                    )
                )
                label = compact(value) if t_end > 100 else value
                if shown and (end - start) >= max(6.5, t_end * 0.04):
                    ax.text(
                        (start + end) / 2,
                        y + 0.49,
                        label,
                        ha="center",
                        va="center",
                        color=ink,
                        fontsize=7.6 if t_end > 100 else 8.4,
                        fontweight="medium",
                        zorder=4,
                        clip_on=True,
                    )

    fig.suptitle(title, x=0.07, ha="left", fontsize=16, color=INK, fontweight="bold")
    fig.text(0.07, 0.935, subtitle, color=MUTED, fontsize=9.5)
    fig.text(0.07, 0.02, caption, color=MUTED, fontsize=8)
    fig.subplots_adjust(left=0.145, right=0.985, top=0.88, bottom=0.09)
    fig.savefig(out_svg)
    fig.savefig(out_png)
    plt.close(fig)


def main():
    DIAG.mkdir(parents=True, exist_ok=True)
    WAVE.mkdir(parents=True, exist_ok=True)

    original = Trace(parse_vcd(BUILD / "original.vcd"))
    cycles = [c for c in collect_cycles(original, 80) if c["t"] <= 75]
    draw_timing(
        cycles,
        "Pipeline do programa em instruction.mif",
        "lw x7, 0(x0)    ·    lw x8, 4(x0)    ·    add x2, x7, x8        memória: [0] = 1, [4] = 2",
        [
            "Cada coluna é o estado depois da subida do clk. IF é a instrução que a memória apresenta no meio do ciclo, depois da descida.",
            "Ciclo em que EX contém lw x8 e ID contém add: stall de load-use. No ciclo seguinte o controle de EX é zerado (bolha) e o add permanece em ID.",
            "Quando add está em EX, B vem do write-back (o lw de x8). A ALU já mostra 3. No WB seguinte, x2 é escrito com 3.",
            "x7 ← 1 em 45 ns, x8 ← 2 em 55 ns, x2 ← 3 em 75 ns — os mesmos horários do transcript ModelSim de 10/08/2023.",
        ],
        DIAG / "pipeline_timing.svg",
        DIAG / "pipeline_timing.png",
    )
    draw_waveform(
        original,
        90,
        "Formas de onda — instruction.mif",
        "Simulação Icarus Verilog do testbench verif/tb_top.sv. Bolha = controle zerado no registrador de pipeline.",
        "VCD build/original.vcd. A instrução em IF muda na descida de clk (endereço da RAM registrado, dado não registrado).",
        WAVE / "pipeline_original.svg",
        WAVE / "pipeline_original.png",
    )

    demo = Trace(parse_vcd(BUILD / "forward_branch.vcd"))
    draw_waveform(
        demo,
        190,
        "Formas de onda — stall, forwarding e beq",
        "Programa em sim/programs/forward_branch. Não é o programa original: foi escrito para exercitar o que o RTL implementa.",
        "x1=5, x2=3, x3=8, x4=5, x5=1, x6=7, x7=6, mem[8]=8, x9=8. x8 não é escrito: o beq tomado elimina add x8.",
        WAVE / "pipeline_forward_branch.svg",
        WAVE / "pipeline_forward_branch.png",
    )
    print("figures written")


if __name__ == "__main__":
    main()
