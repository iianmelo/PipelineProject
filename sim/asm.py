"""Tiny RV32I encoder for the programs under sim/programs.

Only the formats used by those programs are implemented. Encodings are checked
by decoding the fields back before a MIF is written.
"""

from __future__ import annotations


def rtype(funct7, rs2, rs1, funct3, rd):
    return (
        ((funct7 & 0x7F) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x7) << 12)
        | ((rd & 0x1F) << 7)
        | 0b0110011
    )


def load(imm, rs1, funct3, rd):
    return (
        ((imm & 0xFFF) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x7) << 12)
        | ((rd & 0x1F) << 7)
        | 0b0000011
    )


def store(imm, rs2, rs1, funct3):
    imm &= 0xFFF
    return (
        ((imm >> 5) << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x7) << 12)
        | ((imm & 0x1F) << 7)
        | 0b0100011
    )


def branch(imm, rs2, rs1, funct3):
    imm &= 0x1FFF
    bit12 = (imm >> 12) & 1
    bit11 = (imm >> 11) & 1
    bit10_5 = (imm >> 5) & 0x3F
    bit4_1 = (imm >> 1) & 0xF
    return (
        (bit12 << 31)
        | (bit10_5 << 25)
        | ((rs2 & 0x1F) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((funct3 & 0x7) << 12)
        | (bit4_1 << 8)
        | (bit11 << 7)
        | 0b1100011
    )


def addi(rd, rs1, imm):
    return (
        ((imm & 0xFFF) << 20)
        | ((rs1 & 0x1F) << 15)
        | ((rd & 0x1F) << 7)
        | 0b0010011
    )


def lw(rd, imm, rs1):
    return load(imm, rs1, 0b010, rd)


def sw(rs2, imm, rs1):
    return store(imm, rs2, rs1, 0b010)


def add(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b000, rd)


def sub(rd, rs1, rs2):
    return rtype(0b0100000, rs2, rs1, 0b000, rd)


def and_(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b111, rd)


def or_(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b110, rd)


def xor(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b100, rd)


def sll(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b001, rd)


def srl(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b101, rd)


def sltu(rd, rs1, rs2):
    return rtype(0, rs2, rs1, 0b011, rd)


def beq(rs1, rs2, imm):
    return branch(imm, rs2, rs1, 0b000)


def bne(rs1, rs2, imm):
    return branch(imm, rs2, rs1, 0b001)


def write_mif(path, words, comments):
    lines = [
        "DEPTH = 65536;",
        "WIDTH = 8;",
        "ADDRESS_RADIX = DEC;",
        "DATA_RADIX = BIN;",
        "CONTENT",
        "BEGIN",
        "",
    ]
    for i, word in enumerate(words):
        comment = comments[i]
        for lane in range(4):
            byte = (word >> (8 * lane)) & 0xFF
            addr = i * 4 + lane
            suffix = f"\t\t-- {comment}" if lane == 0 else ""
            lines.append(f"{addr:03d}: {byte:08b};{suffix}")
        lines.append("")
    lines.append("END;")
    path.write_text("\n".join(lines) + "\n")


def write_data_mif(path, byte_values):
    lines = [
        "DEPTH = 65536;",
        "WIDTH = 8;",
        "ADDRESS_RADIX = DEC;",
        "DATA_RADIX = BIN;",
        "CONTENT",
        "BEGIN",
        "",
    ]
    for addr, value in byte_values.items():
        lines.append(f"{addr:03d}: {value:08b};")
    lines.append("")
    lines.append("END;")
    path.write_text("\n".join(lines) + "\n")
