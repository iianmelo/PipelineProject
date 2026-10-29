#!/usr/bin/env python3
"""Assemble the documentation programs into Altera MIF files."""

from pathlib import Path

from asm import (
    add,
    addi,
    and_,
    beq,
    bne,
    lw,
    or_,
    sll,
    sltu,
    srl,
    sub,
    sw,
    write_data_mif,
    write_mif,
    xor,
)

ROOT = Path(__file__).resolve().parent / "programs"


def emit(name, program, data, note):
    directory = ROOT / name
    directory.mkdir(parents=True, exist_ok=True)
    words = [enc for _, enc in program]
    comments = [text for text, _ in program]
    write_mif(directory / "instruction.mif", words, comments)
    write_data_mif(directory / "data.mif", data)
    listing = [note, ""]
    for index, (text, enc) in enumerate(program):
        listing.append(f"{index * 4:04d}: {enc:08x}  {text}")
    listing.append("")
    listing.append("data memory:")
    for addr in sorted(data):
        listing.append(f"  [{addr}] = 0x{data[addr]:02x}")
    (directory / "listing.txt").write_text("\n".join(listing) + "\n")
    print(f"wrote {directory}")


def main():
    emit(
        "forward_branch",
        [
            ("lw x1, 0(x0)", lw(1, 0, 0)),
            ("lw x2, 4(x0)", lw(2, 4, 0)),
            ("beq x1, x2, 8", beq(1, 2, 8)),
            ("add x3, x1, x2", add(3, 1, 2)),
            ("sub x4, x3, x2", sub(4, 3, 2)),
            ("and x5, x1, x2", and_(5, 1, 2)),
            ("or x6, x1, x2", or_(6, 1, 2)),
            ("xor x7, x1, x2", xor(7, 1, 2)),
            ("sw x3, 8(x0)", sw(3, 8, 0)),
            ("beq x4, x1, 8", beq(4, 1, 8)),
            ("add x8, x1, x1", add(8, 1, 1)),
            ("add x9, x1, x2", add(9, 1, 2)),
        ],
        {0: 0x05, 1: 0x00, 2: 0x00, 3: 0x00, 4: 0x03, 5: 0x00, 6: 0x00, 7: 0x00},
        "Programa de demonstração (não é o instruction.mif original).\n"
        "Memória: [0]=5, [4]=3. Exercita stall de load-use, forwarding,\n"
        "store, beq não tomado e beq tomado.",
    )
    emit(
        "lacunas",
        [
            ("lw x1, 0(x0)", lw(1, 0, 0)),
            ("lw x2, 4(x0)", lw(2, 4, 0)),
            ("sll x3, x1, x2", sll(3, 1, 2)),
            ("srl x4, x1, x2", srl(4, 1, 2)),
            ("sltu x5, x1, x2", sltu(5, 1, 2)),
            ("addi x6, x0, 21", addi(6, 0, 21)),
            ("beq x1, x1, 8", beq(1, 1, 8)),
            ("add x10, x1, x2", add(10, 1, 2)),
            ("add x7, x1, x0", add(7, 1, 0)),
            ("bne x1, x1, 8", bne(1, 1, 8)),
            ("add x8, x2, x2", add(8, 2, 2)),
            ("add x9, x1, x1", add(9, 1, 1)),
        ],
        {0: 0x05, 1: 0x00, 2: 0x00, 3: 0x00, 4: 0x03, 5: 0x00, 6: 0x00, 7: 0x00},
        "Programa para observar opcodes que o assembler aceita e o RTL não fecha.\n"
        "Memória: [0]=5, [4]=3.",
    )


if __name__ == "__main__":
    main()
