#ifndef SMO_ELF_H
#define SMO_ELF_H

#include <stdint.h>
typedef uint64_t elf64_addr_t;
typedef uint64_t elf64_off_t;
typedef uint16_t elf64_half_t;
typedef uint32_t elf64_word_t;
typedef int32_t elf64_sword_t;
typedef uint64_t elf64_xword_t;
typedef int64_t elf64_sxword_t;

enum {
    EI_MAG0 = 0,
    EI_MAG1 = 1,
    EI_MAG2 = 2,
    EI_MAG3 = 3,
    EI_CLASS = 4,
    EI_DATA = 5,
    EI_VERSION = 6,
    EI_OSABI = 7,
    EI_ABIVERSION = 8,
    EI_PAD = 9,
    EI_NIDENT = 16,
};

enum {
    ELFCLASS32 = 1,
    ELFCLASS64 = 2,
};

enum {
    ELFDATA2LSB = 1,
    ELFDATA2MSB = 2,
};

enum {
    ELFCURRENT_VERSION = 1
};

enum {
    EM_I386 = 3,
    EM_ARM = 40,
    EM_X86_64 = 62,
    EM_AARCH64 = 183,
    EM_RISCV = 243,
};

enum {
    EF_RISCV_RVC = 0x0001,
    EF_RISCV_FLOAT_ABI_SOFT = 0x0000,
    EF_RISCV_FLOAT_ABI_SINGLE = 0x0002,
    EF_RISCV_FLOAT_ABI_DOUBLE = 0x0004,
    EF_RISCV_FLOAT_ABI_QUAD = 0x0006,
    EF_RISCV_RVE = 0x0008,
    EF_RISCV_TSO = 0x0010,
};

enum {
    ET_NONE = 0,
    ET_REL = 1,
    ET_EXEC = 2,
    ET_DYN = 3,
    ET_CORE = 4,
};

enum {
    SHF_WRITE = 1,
    SHF_ALLOC = 2,
    SHF_EXECINSTR = 4,
    SHF_MERGE = 0x10,
    SHF_STRINGS = 0x20,
    SHF_TLS = 0x400,
};

enum {
    SHN_UNDEF = 0,
    SHN_ABS = 0xFFF1,
    SHN_COMMON = 0xFFF2,
};

enum {
    SHT_NULL = 0,
    SHT_PROGBITS = 1,
    SHT_SYMTAB = 2,
    SHT_STRTAB = 3,
    SHT_RELA = 4,
    SHT_HASH = 5,
    SHT_DYNAMIC = 6,
    SHT_NOTE = 7,
    SHT_NOBITS = 8,
    SHT_REL = 9,
    SHT_SHLIB = 10,
    SHT_DYNSYM = 11,

    SHT_X86_64_UNWIND = 0x70000001,
    SHT_RISCV_ATTRIBUTES = 0x70000003
};

enum {
    STB_LOCAL = 0,
    STB_GLOBAL = 1,
    STB_WEAK = 2,
};

enum {
    STT_NOTYPE = 0,
    STT_OBJECT = 1,
    STT_FUNC = 2,
    STT_SECTION = 3,
    STT_FILE = 4,
};

enum {
    R_X86_64_64 = 1,
    R_X86_64_PC32 = 2,
    R_X86_64_GOT32 = 3,
    R_X86_64_PLT32 = 4,
    R_X86_64_GOTPCREL = 9,
    R_X86_64_32 = 10,
    R_X86_64_16 = 12,
    R_X86_64_PC16 = 13,
    R_X86_64_8 = 14,
    R_X86_64_PC8 = 15,
    R_X86_64_PC64 = 24,
};

enum {
    R_AARCH64_ABS64 = 257,
    R_AARCH64_ABS32 = 258,
    R_AARCH64_ABS16 = 259,
    R_AARCH64_PREL64 = 260,
    R_AARCH64_PREL32 = 261,

    R_AARCH64_ADR_PREL_PG_HI21 = 276,
    R_AARCH64_ADD_ABS_LO12_NC = 277,
    
    R_AARCH64_JUMP26 = 282,
    R_AARCH64_CALL26 = 283,
};

enum {
    R_RISCV_NONE = 0,
    R_RISCV_32 = 1,
    R_RISCV_64 = 2,
    R_RISCV_32_PCREL = 57,

    R_RISCV_BRANCH = 16,
    R_RISCV_JAL = 17,
    R_RISCV_CALL_PLT = 19,
    R_RISCV_PCREL_HI20 = 23,
    R_RISCV_PCREL_LO12_I = 24,
    R_RISCV_PCREL_LO12_S = 25,
    R_RISCV_HI20 = 26,
    R_RISCV_LO12_I = 27,
    R_RISCV_LO12_S = 28,
    R_RISCV_RELAX = 51,
};

#define ELF64_SYM_INFO(type, binding) (((binding) << 4) | (type))

typedef struct elf64_header_s
{
    uint8_t ident[16];
    elf64_half_t type;
    elf64_half_t machine;
    elf64_word_t version;
    elf64_addr_t entry;
    elf64_off_t programHeadersOffset;
    elf64_off_t sectionHeadersOffset;
    elf64_word_t flags;
    elf64_half_t elfHeaderSize;
    elf64_half_t programHeaderEntrySize;
    elf64_half_t programHeaderCount;
    elf64_half_t sectionHeaderEntrySize;
    elf64_half_t sectionHeaderNum;
    elf64_half_t sectionHeaderNameStringTableIndex;
} elf64_header_t;

typedef struct elf64_sectionHeader_s
{
    elf64_word_t name;
    elf64_word_t type;
    elf64_xword_t flags;
    elf64_addr_t address;
    elf64_off_t offset;
    elf64_xword_t size;
    elf64_word_t link;
    elf64_word_t info;
    elf64_xword_t addressAlignment;
    elf64_xword_t entrySize;
} elf64_sectionHeader_t;

typedef struct elf64_symbol_s
{
    elf64_word_t name;
    uint8_t info;
    uint8_t other;
    elf64_half_t sectionHeaderIndex;
    elf64_addr_t value;
    elf64_xword_t size;
} elf64_symbol_t;

typedef struct elf64_rel_s
{
    elf64_addr_t offset;
    elf64_xword_t info;
} elf64_rel_t;

typedef struct elf64_rela_s
{
    elf64_addr_t offset;
    elf64_xword_t info;
    elf64_sxword_t addend;
} elf64_rela_t;

#define ELF64_R_INFO(symbol, type) (( (elf64_xword_t)(symbol) << 32) | ((elf64_xword_t)(type) & 0xFFFFFFFF))

#endif //SMO_ELF_H