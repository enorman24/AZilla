#!/usr/bin/env python3
"""
elf2vmem.py -- Convert a RISC-V ELF to a $readmemh-compatible vmem file.

Replaces the DPI-based ELF loader (tb/dpi/elfloader.cc + ara_tb.sv dram_init) for
the VCS/Questa simulation path. The vmem is loaded by tc_sram.sv via
$readmemh(init_file, init_val) and carried into the live array by the existing
`sram <= init_val` reset copy.

Dependency-free on purpose: parses the ELF program headers directly with `struct`
so it runs under any python3 (no pyelftools, which is not installed and cannot be
fetched offline on this host). Use a conda/.venv python (e.g. the tvm-dev env).

Usage:
    python3 elf2vmem.py <input.elf> <output.vmem> \
        [--dram-base 0x80000000] \
        [--dram-length 0x40000000] \
        [--bytes-per-word 32]

Output uses @word_address directives where
    word_address = (segment_paddr - dram_base) // bytes_per_word
Bytes within each word are REVERSED so the byte at the lowest address becomes the
rightmost (LSB) hex chars -- matching $readmemh's big-endian hex-string reading on
a little-endian (RISC-V) AXI system where byte lane 0 is bits[7:0]. This reproduces
the exact image the old `dram_init` wrote (mem_row[8*b +: 8] = buffer[b]).
"""

import sys
import struct
import argparse

PT_LOAD = 1


def read_segments(elf_path):
    """Return (paddr, data) for each PT_LOAD segment, data zero-padded to memsz."""
    with open(elf_path, "rb") as f:
        blob = f.read()

    if blob[:4] != b"\x7fELF":
        sys.exit("ERROR: not an ELF file (bad magic)")
    ei_class = blob[4]   # 1 = ELF32, 2 = ELF64
    ei_data = blob[5]     # 1 = little-endian, 2 = big-endian
    if ei_data != 1:
        print("WARNING: ELF is big-endian; byte ordering may be wrong", file=sys.stderr)
    endian = "<" if ei_data == 1 else ">"

    if ei_class == 2:  # ELF64
        e_phoff = struct.unpack_from(endian + "Q", blob, 0x20)[0]
        e_phentsize = struct.unpack_from(endian + "H", blob, 0x36)[0]
        e_phnum = struct.unpack_from(endian + "H", blob, 0x38)[0]
        # Elf64_Phdr: type(4) flags(4) offset(8) vaddr(8) paddr(8) filesz(8) memsz(8) align(8)
        ph_fmt = endian + "IIQQQQQQ"
        idx_off, idx_paddr, idx_filesz, idx_memsz = 2, 4, 5, 6
    elif ei_class == 1:  # ELF32
        e_phoff = struct.unpack_from(endian + "I", blob, 0x1C)[0]
        e_phentsize = struct.unpack_from(endian + "H", blob, 0x2A)[0]
        e_phnum = struct.unpack_from(endian + "H", blob, 0x2C)[0]
        # Elf32_Phdr: type(4) offset(4) vaddr(4) paddr(4) filesz(4) memsz(4) flags(4) align(4)
        ph_fmt = endian + "IIIIIIII"
        idx_off, idx_paddr, idx_filesz, idx_memsz = 1, 3, 4, 5
    else:
        sys.exit("ERROR: unknown ELF class %d" % ei_class)

    segments = []
    for i in range(e_phnum):
        ph = struct.unpack_from(ph_fmt, blob, e_phoff + i * e_phentsize)
        if ph[0] != PT_LOAD:
            continue
        memsz = ph[idx_memsz]
        if memsz == 0:
            continue
        paddr = ph[idx_paddr]
        offset = ph[idx_off]
        filesz = ph[idx_filesz]
        data = blob[offset:offset + filesz].ljust(memsz, b"\x00")  # zero-pad BSS
        segments.append((paddr, data))
    return segments


def elf2vmem(elf_path, vmem_path, dram_base, dram_length, bytes_per_word):
    all_segs = read_segments(elf_path)

    segments = []
    for paddr, data in all_segs:
        memsz = len(data)
        if paddr + memsz <= dram_base or paddr >= dram_base + dram_length:
            print("WARNING: segment at 0x%016x (size 0x%x) outside DRAM window -- skipped"
                  % (paddr, memsz), file=sys.stderr)
            continue
        segments.append((paddr, data))
        print("Loading segment: 0x%016x (%d bytes)" % (paddr, memsz), file=sys.stderr)

    if not segments:
        sys.exit("ERROR: No loadable segments found in DRAM window")

    total_bytes = sum(len(d) for _, d in segments)
    if total_bytes > dram_length:
        print("WARNING: total program size (%d bytes) exceeds --dram-length (0x%x)"
              % (total_bytes, dram_length), file=sys.stderr)

    with open(vmem_path, "w") as out:
        for paddr, data in sorted(segments):
            byte_offset = paddr - dram_base
            front_pad = byte_offset % bytes_per_word
            if front_pad:
                byte_offset -= front_pad
                data = b"\x00" * front_pad + data

            word_addr = byte_offset // bytes_per_word
            out.write("@%08x\n" % word_addr)

            for i in range(0, len(data), bytes_per_word):
                chunk = data[i:i + bytes_per_word].ljust(bytes_per_word, b"\x00")
                # byte[0] (lowest address) -> rightmost hex chars (LSB)
                out.write(chunk[::-1].hex().upper() + "\n")


def main():
    p = argparse.ArgumentParser(description="Convert ELF to $readmemh vmem")
    p.add_argument("elf", help="Input ELF file")
    p.add_argument("vmem", help="Output vmem file")
    p.add_argument("--dram-base", type=lambda x: int(x, 0), default=0x80000000,
                   help="DRAM base address (default: 0x80000000)")
    p.add_argument("--dram-length", type=lambda x: int(x, 0), default=0x40000000,
                   help="DRAM size in bytes (default: 0x40000000 = 1 GB address window)")
    p.add_argument("--bytes-per-word", type=int, default=32,
                   help="Memory word width in bytes (default: 32 = 256-bit)")
    args = p.parse_args()
    elf2vmem(args.elf, args.vmem, args.dram_base, args.dram_length, args.bytes_per_word)
    print("Written: %s" % args.vmem, file=sys.stderr)


if __name__ == "__main__":
    main()
