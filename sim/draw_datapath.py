#!/usr/bin/env python3
"""Draw the datapath figure committed under docs/diagrams/."""

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "diagrams" / "datapath.svg"

W, H = 1640, 1080
PAPER = "#F6F3EE"
INK = "#1C2430"
MUTED = "#5C6974"
LANE = ["#E7F0FA", "#E5F6F0", "#FBF4E6", "#F3EAF8", "#FBECEA"]
ACCENT = ["#1D4E89", "#0E7C66", "#A56B00", "#6C3B8A", "#9A3B3B"]


def box(x, y, w, h, title, lines, accent):
    body = "\n".join(
        f'<text x="{x + 14}" y="{y + 46 + i * 16}" fill="{MUTED}" font-size="12">{line}</text>'
        for i, line in enumerate(lines)
    )
    return f'''
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#FFFcf8" stroke="{accent}" stroke-width="1.4"/>
    <rect x="{x}" y="{y}" width="6" height="{h}" rx="3" fill="{accent}"/>
    <text x="{x + 16}" y="{y + 24}" fill="{INK}" font-size="14" font-weight="700">{title}</text>
    {body}'''


def main():
    lanes = [
        (36, "IF", "Busca"),
        (360, "ID", "Decodificação"),
        (700, "EX", "Execução"),
        (1148, "MEM", "Memória"),
        (1388, "WB", "Escrita"),
    ]
    bars = [
        (308, "IF/ID", "A"),
        (648, "ID/EX", "B"),
        (1096, "EX/MEM", "C"),
        (1336, "MEM/WB", "D"),
    ]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<style>text { font-family: Inter, "Noto Sans", sans-serif; }</style>',
        """<defs>
      <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1.2 L 9 5 L 0 8.8 z" fill="#334155"/>
      </marker>
      <marker id="arrG" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1.2 L 9 5 L 0 8.8 z" fill="#0E7C66"/>
      </marker>
      <marker id="arrO" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1.2 L 9 5 L 0 8.8 z" fill="#C2410C"/>
      </marker>
      <marker id="arrR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M 0 1.2 L 9 5 L 0 8.8 z" fill="#9A3B3B"/>
      </marker>
    </defs>""",
        f'<rect width="{W}" height="{H}" fill="{PAPER}"/>',
        f'<text x="40" y="46" fill="{INK}" font-size="28" font-weight="700" font-family="Inter, sans-serif">Caminho de dados do pipeline</text>',
        f'<text x="40" y="74" fill="{MUTED}" font-size="15" font-family="Inter, sans-serif">Cinco estágios, quatro registradores de pipeline e os dois blocos que resolvem dependência de dados. Fonte: design/Datapath.sv, design/RegPack.sv.</text>',
    ]
    for (x, tag, name), fill, accent in zip(lanes, LANE, ACCENT):
        width = 250 if tag != "EX" else 370
        if tag == "MEM":
            width = 168
        if tag == "WB":
            width = 210
        if tag == "ID":
            width = 268
        parts.append(
            f'<rect x="{x}" y="108" width="{width}" height="760" rx="16" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{x + 16}" y="134" fill="{accent}" font-size="12" font-weight="700">{tag}</text>'
        )
        parts.append(
            f'<text x="{x + 16}" y="152" fill="{INK}" font-size="13" font-weight="600">{name}</text>'
        )

    parts.append(
        box(56, 168, 210, 92, "PC", ["9 bits, registrador com stall", "segura o endereço na load-use"], ACCENT[0])
    )
    parts.append(box(56, 286, 210, 78, "Somador +4", ["próximo endereço sequencial"], ACCENT[0]))
    parts.append(
        box(56, 390, 210, 96, "MUX do PC", ["0 · PC+4", "1 · alvo do branch (BrPC)"], ACCENT[0])
    )
    parts.append(
        box(
            56,
            620,
            210,
            150,
            "Memória de instruções",
            ["quatro altsyncram de 64 KiB × 8", "inicialização: instruction.mif", "endereço de leitura = PC", "clock invertido"],
            ACCENT[0],
        )
    )

    parts.append(
        box(
            380,
            168,
            228,
            132,
            "Unidade de controle",
            ["opcode vindo de IF/ID", "gera ALUSrc, MemtoReg,", "RegWrite, MemRead, MemWrite,", "ALUOp e Branch"],
            ACCENT[1],
        )
    )
    parts.append(
        box(
            380,
            324,
            228,
            124,
            "Banco de registradores",
            ["32 × 32 bits", "duas leituras combinacionais", "escrita na descida do clock"],
            ACCENT[1],
        )
    )
    parts.append(
        box(
            380,
            472,
            228,
            100,
            "Gerador de imediato",
            ["load I, store S e branch B", "demais formatos caem em zero"],
            ACCENT[1],
        )
    )
    parts.append(
        box(
            380,
            640,
            228,
            128,
            "Detecção de hazard",
            ["olha o load que está em EX", "compara rd com rs1 e rs2", "de quem está em ID", "produz Reg_Stall"],
            ACCENT[1],
        )
    )

    parts.append(
        box(
            720,
            168,
            168,
            128,
            "Forwarding",
            ["EX/MEM tem prioridade", "sobre MEM/WB", "não encaminha rd = 0"],
            ACCENT[2],
        )
    )
    parts.append(
        box(
            908,
            168,
            142,
            128,
            "MUX A / MUX B",
            ["00 · banco", "01 · write-back", "10 · ALU anterior"],
            ACCENT[2],
        )
    )
    parts.append(
        box(720, 322, 330, 72, "MUX ALUSrc", ["segundo operando: registrador encaminhado ou imediato"], ACCENT[2])
    )
    parts.append(
        box(720, 420, 168, 118, "ALU", ["AND, OR, XOR", "ADD, SUB", "igualdade para beq"], ACCENT[2])
    )
    parts.append(
        box(908, 420, 142, 118, "Controle da ALU", ["ALUOp + funct3", "+ funct7", "código de 4 bits"], ACCENT[2])
    )
    parts.append(
        box(
            720,
            566,
            330,
            132,
            "Unidade de branch",
            ["decisão no estágio EX", "tomado se Branch e ALU[0]", "alvo = PC da instrução + imediato", "PcSel descarta IF e ID"],
            ACCENT[2],
        )
    )

    parts.append(
        box(
            1164,
            360,
            140,
            168,
            "Memória de dados",
            ["quatro bancos", "64 KiB × 8", "data.mif", "addr = ALU[8:0]", "lw / sw de palavra"],
            ACCENT[3],
        )
    )
    parts.append(
        box(
            1408,
            360,
            176,
            150,
            "MUX MemtoReg",
            ["0 · resultado da ALU", "1 · dado lido", "esse é o WB_Data"],
            ACCENT[4],
        )
    )

    for x, name, letter in bars:
        parts.append(f'<rect x="{x}" y="178" width="34" height="640" rx="8" fill="#243044"/>')
        parts.append(
            f'<text x="{x + 17}" y="470" fill="#F7F5F2" font-size="13" font-weight="700" font-family="Inter, sans-serif" transform="rotate(-90 {x + 17} 470)" text-anchor="middle">{name}</text>'
        )
        parts.append(
            f'<text x="{x + 17}" y="860" fill="#243044" font-size="13" font-weight="700" font-family="Inter, sans-serif" text-anchor="middle">{letter}</text>'
        )

    # Writeback loop, kept under the lanes.
    parts.append(
        '<path d="M 1496 510 L 1496 960 L 494 960 L 494 448" fill="none" stroke="#0E7C66" stroke-width="1.7" marker-end="url(#arrG)"/>'
    )
    parts.append(
        '<text x="720" y="984" fill="#0E7C66" font-size="12">dado de escrita, também usado no forwarding de write-back</text>'
    )

    # ALU result from EX/MEM back to the forwarding muxes, in the gap beside EX.
    parts.append(
        '<path d="M 1096 500 L 1056 500 L 1056 232 L 1050 232" fill="none" stroke="#0E7C66" stroke-width="1.7" stroke-dasharray="5 4" marker-end="url(#arrG)"/>'
    )
    parts.append(
        '<text x="1072" y="640" fill="#0E7C66" font-size="11" transform="rotate(-90 1072 640)">ALU de EX/MEM</text>'
    )

    # Stall stays in the gap between IF and the IF/ID register, then enters the PC.
    parts.append(
        '<path d="M 380 704 L 296 704 L 296 214 L 266 214" fill="none" stroke="#C2410C" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#arrO)"/>'
    )
    # PcSel travels above the blocks, in the gap under the stage titles.
    parts.append(
        '<path d="M 720 566 L 708 566 L 708 164 L 22 164 L 22 438 L 56 438" fill="none" stroke="#9A3B3B" stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#arrR)"/>'
    )
    parts.append('<text x="70" y="380" fill="#9A3B3B" font-size="12">PcSel</text>')

    # PC+4 local loop
    parts.append(
        f'<path d="M 161 364 L 161 390" fill="none" stroke="#334155" stroke-width="1.6" marker-end="url(#arr)"/>'
    )
    parts.append(
        f'<path d="M 161 260 L 161 286" fill="none" stroke="#334155" stroke-width="1.6" marker-end="url(#arr)"/>'
    )

    parts.append(
        f'''<g font-family="Inter, sans-serif" font-size="12" fill="{MUTED}">
      <text x="40" y="1050">Registradores de pipeline em RegPack.sv: A = IF/ID, B = ID/EX, C = EX/MEM, D = MEM/WB. O controle nasce em ID e viaja dentro de B, C e D. A decisão de branch é no EX, com penalidade de dois ciclos quando o desvio é tomado.</text>
    </g>'''
    )
    parts.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts))
    print(OUT)


if __name__ == "__main__":
    main()
