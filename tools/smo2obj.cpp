#include "elf.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <string>
#include <vector>
#include <unordered_map>

enum SmoRelocationKind
{
    SmoRelocationNull              = 0,
    SmoRelocationAbsolute8         = 1,
    SmoRelocationAbsolute16        = 2,
    SmoRelocationAbsolute32        = 3,
    SmoRelocationAbsolute64        = 4,
    SmoRelocationRelative8         = 5,
    SmoRelocationRelative16        = 6,
    SmoRelocationRelative32        = 7,
    SmoRelocationRelative32AtGot   = 8,
    SmoRelocationRelative32AtPlt   = 9,
    SmoRelocationRelative64        = 10,
    SmoRelocationSectionRelative32 = 11,
};

uint32_t mapRelocationKindToX86(uint32_t kind)
{
    switch(kind)
    {
    case SmoRelocationAbsolute8:         return R_X86_64_8;
    case SmoRelocationAbsolute16:        return R_X86_64_16;
    case SmoRelocationAbsolute32:        return R_X86_64_32;
    case SmoRelocationAbsolute64:        return R_X86_64_64;
    case SmoRelocationRelative32:        return R_X86_64_PC32;
    case SmoRelocationRelative32AtGot:   return R_X86_64_GOTPCREL;
    case SmoRelocationRelative32AtPlt:   return R_X86_64_PLT32;
    case SmoRelocationRelative64:        return R_X86_64_PC64;
    case SmoRelocationSectionRelative32: return R_X86_64_32;
    }
    abort();
}

class ByteWriteStream
{
public:
    void push_byte(uint8_t byte)
    {
        if(position < data.size())
            data[position] = byte;
        else
            data.push_back(byte);
        ++position;
    }

    void push_bytes(const uint8_t *bytes, size_t bytesSize)
    {
        for(size_t i = 0; i < bytesSize; ++i)
            push_byte(bytes[i]);
    }

    void push_bytes(const std::vector<uint8_t> &bytes)
    {
        push_bytes(bytes.data(), bytes.size());
    }

    template<typename T>
    void push_struct(T&& s)
    {
        const uint8_t *structData = reinterpret_cast<const uint8_t*> (&s);
        size_t structDataSize = sizeof(T);
        push_bytes(structData, structDataSize);
    }

    void reset()
    {
        position = 0;
    }

    size_t position = 0;
    std::vector<uint8_t> data;
};

struct SmoHeader
{
    static const uint32_t MagicNumber = ('S') | ('M' << 8)| ('O' << 16) | (' ' << 24);

    uint32_t magic;
    uint32_t headerSize;
    uint32_t nameStringOffset;
    uint32_t functionEntryPoint;
    uint32_t sectionTableOffset;
    uint32_t sectionTableSize;
    uint32_t stringTableOffset;
    uint32_t stringTableSize;
    uint32_t symbolTableOffset;
    uint32_t symbolTableSize;

};

struct SmoSectionHeader
{
    uint32_t nameIndex;
    uint32_t offset;
    uint32_t size;
    uint32_t alignment;
    uint32_t flags;
    uint32_t type;
    uint32_t relocationTableOffset;
    uint32_t relocationTableSize;
};

struct SmoRelocationEntry
{
    uint32_t kind;
    uint32_t symbolIndex;
    uint64_t offset;
    int64_t addend;
};

struct SmoSymbolEntry
{
    uint64_t value;
    uint64_t size;
    uint32_t nameIndex;
    uint32_t sectionIndex;
    uint32_t binding;
    uint32_t type;
};

struct SmoSymbol
{
    uint64_t value;
    uint64_t size;
    std::string name;
    uint32_t sectionIndex;
    uint32_t binding;
    uint32_t type;
};

std::vector<uint8_t> readWholeFile(const std::string &filename);


class SmoSection
{
public:
    std::string name;
    uint32_t alignment;
    uint32_t flags;
    uint32_t type;
    std::vector<uint8_t> data;
    std::vector<SmoRelocationEntry> relocations;
};

class SmoStringTable
{
public:
    std::string getStringWithIndex(size_t index)
    {
        std::string result;
        auto currentIndex = index;
        while(data[currentIndex] != 0)
        {
            result.push_back(data[currentIndex]);
            ++currentIndex;
        }

        return result;
    }
    std::vector<uint8_t> data;
};

class ElfStringTable
{
public:
    ElfStringTable()
    {
        strings.push_back(0);
        stringsMap[""] = 0;
    }

    size_t getOrCreateString(const std::string &s)
    {
        auto it = stringsMap.find(s);
        if(it != stringsMap.end())
            return it->second;
        
        size_t offset = strings.size();
        for(auto c : s)
            strings.push_back(c);
        strings.push_back(0);
        stringsMap[s] = offset;
        return offset;
    }

    std::vector<uint8_t> strings;
    std::unordered_map<std::string, size_t> stringsMap;
};

class SmoModule
{
public:
    bool readFromFileNamed(const std::string &filename)
    {
        return readFromBytes(readWholeFile(filename));
    }

    bool readFromBytes(const std::vector<uint8_t> &bytes)
    {
        if(bytes.size() < sizeof(SmoHeader))
            return false;
        
        // Read and verify the header
        SmoHeader header;
        memcpy(&header, bytes.data(), sizeof(header));
        if(header.magic != SmoHeader::MagicNumber || header.headerSize != sizeof(SmoHeader))
            return false;

        // Read the string table.
        stringTable.data.resize(header.stringTableSize);
        memcpy(stringTable.data.data(), bytes.data() + header.stringTableOffset, header.stringTableSize);

        // Read the module name.
        name = stringTable.getStringWithIndex(header.nameStringOffset);

        // Read the section headers
        std::vector<SmoSectionHeader> sectionHeaders;
        sectionHeaders.resize(header.sectionTableSize);
        memcpy(sectionHeaders.data(), bytes.data() + header.sectionTableOffset, sizeof(SmoSectionHeader) * header.sectionTableSize);

        // Read the sections.
        for(auto &sectionHeader : sectionHeaders)
        {
            SmoSection section = {};
            section.name = stringTable.getStringWithIndex(sectionHeader.nameIndex);
            section.alignment = sectionHeader.alignment;
            section.flags = sectionHeader.flags;
            section.type = sectionHeader.type;
            section.data.resize(sectionHeader.size);
            memcpy(section.data.data(), bytes.data() + sectionHeader.offset, sectionHeader.size);

            section.relocations.resize(sectionHeader.relocationTableSize);
            memcpy(section.relocations.data(), bytes.data() + sectionHeader.relocationTableOffset, sizeof(SmoRelocationEntry)*sectionHeader.relocationTableSize);

            sections.push_back(section);
        }

        // Read the symbols.
        std::vector<SmoSymbolEntry> symbolEntries;
        symbolEntries.resize(header.symbolTableSize);
        memcpy(symbolEntries.data(), bytes.data() + header.symbolTableOffset, sizeof(SmoSymbolEntry)*header.symbolTableSize);

        symbols.reserve(symbolEntries.size());

        for(auto &symbolEntry : symbolEntries)
        {
            SmoSymbol symbol = {};
            symbol.value = symbolEntry.value;
            symbol.size = symbolEntry.size;
            symbol.name = stringTable.getStringWithIndex(symbolEntry.nameIndex);
            symbol.sectionIndex = symbolEntry.sectionIndex;
            symbol.binding = symbolEntry.binding;
            symbol.type = symbolEntry.type;

            symbols.push_back(symbol);
            if(symbol.binding == STB_LOCAL)
                localSymbolCount = symbols.size();
        }

        return true;
    }

    std::vector<uint8_t> encodeAsElf64()
    {
        ByteWriteStream out;
        ElfStringTable symbolStringTable;
        ElfStringTable sectionStringTable;

        elf64_header_t header = {};
        header.ident[EI_MAG0] = 0x7f;
        header.ident[EI_MAG1] = 'E';
        header.ident[EI_MAG2] = 'L';
        header.ident[EI_MAG3] = 'F';
        header.ident[EI_CLASS] = ELFCLASS64;
        header.ident[EI_DATA] = ELFDATA2LSB;
        header.ident[EI_VERSION] = ELFCURRENT_VERSION;
        header.type = ET_REL;
        header.machine = EM_X86_64; // TODO: Support more machines
        header.elfHeaderSize = sizeof(elf64_header_t);
        header.version = ELFCURRENT_VERSION;
        header.sectionHeaderEntrySize = sizeof(elf64_sectionHeader_t);
        out.push_struct(header);

        // Write the sections
        std::vector<elf64_sectionHeader_t> sectionHeaders;
        {
            elf64_sectionHeader_t nullSection = {};
            sectionHeaders.push_back(nullSection);
        }

        for(size_t i = 1; i < sections.size(); ++i)
        {
            auto &section = sections[i];
            elf64_sectionHeader_t sectionHeader = {};
            sectionHeader.offset = out.position;
            sectionHeader.size = section.data.size();
            sectionHeader.addressAlignment = section.alignment;
            sectionHeader.flags = section.flags;
            sectionHeader.type = section.type;
            sectionHeader.name = sectionStringTable.getOrCreateString(section.name);

            out.push_bytes(section.data);
            sectionHeaders.push_back(sectionHeader);
        }

        // Symbol table section
        size_t symbolTableSectionIndex = sectionHeaders.size();
        {
            elf64_sectionHeader_t sectionHeader = {};
            sectionHeader.type = SHT_SYMTAB;
            sectionHeader.offset = out.position;
            sectionHeader.link = sectionHeaders.size() + 1;
            sectionHeader.name = sectionStringTable.getOrCreateString(".symtab");
            sectionHeader.entrySize = sizeof(elf64_symbol_t);

            // Null entry
            {
                elf64_symbol_t nullEntry = {};
                out.push_struct(nullEntry);
            }
            for(size_t i = 1; i < symbols.size(); ++i)
            {
                auto &symbol = symbols[i];
                elf64_symbol_t elfSymbolEntry = {};
                
                elfSymbolEntry.value = symbol.value;
                elfSymbolEntry.size = symbol.size;
                elfSymbolEntry.name = symbolStringTable.getOrCreateString(symbol.name);
                elfSymbolEntry.info = ELF64_SYM_INFO(symbol.type, symbol.binding);
                elfSymbolEntry.sectionHeaderIndex = symbol.sectionIndex;
                out.push_struct(elfSymbolEntry);
            }

            sectionHeader.info = localSymbolCount;
            sectionHeader.size = out.position - sectionHeader.offset;
            sectionHeaders.push_back(sectionHeader);
        }
        
        // Strings section.
        {
            elf64_sectionHeader_t sectionHeader = {};
            sectionHeader.type = SHT_STRTAB;
            sectionHeader.name = sectionStringTable.getOrCreateString(".strtab");
            sectionHeader.offset = out.position;
            sectionHeader.size = symbolStringTable.strings.size();
            sectionHeader.addressAlignment = 1;

            sectionHeaders.push_back(sectionHeader);
            out.push_bytes(symbolStringTable.strings);
        }

        // Relocation sections
        for(size_t i = 1; i < sections.size(); ++i)
        {
            auto &section = sections[i];
            if(section.relocations.empty())
                continue;

            elf64_sectionHeader_t sectionHeader = {};
            sectionHeader.offset = out.position;
            sectionHeader.addressAlignment = section.alignment;
            sectionHeader.type = SHT_RELA;
            sectionHeader.name = sectionStringTable.getOrCreateString(section.name + ".rela");
            sectionHeader.link = symbolTableSectionIndex;
            sectionHeader.info = i;
            sectionHeader.entrySize = sizeof(elf64_rela_t);

            for(auto &reloc : section.relocations)
            {
                elf64_rela_t rela = {};
                rela.offset = reloc.offset;
                rela.addend = reloc.addend;
                rela.info = ELF64_R_INFO(reloc.symbolIndex, mapRelocationKindToX86(reloc.kind));
                out.push_struct(rela);
            }

            sectionHeader.size = out.position - sectionHeader.offset;
            sectionHeaders.push_back(sectionHeader);
        }


        // Section header strings
        {
            elf64_sectionHeader_t sectionHeader = {};
            sectionHeader.type = SHT_STRTAB;
            sectionHeader.name = sectionStringTable.getOrCreateString(".shstrtab");
            sectionHeader.offset = out.position;
            sectionHeader.size = sectionStringTable.strings.size();
            sectionHeader.addressAlignment = 1;

            sectionHeaders.push_back(sectionHeader);
            out.push_bytes(sectionStringTable.strings);
        }

        // Section headers.
        header.sectionHeaderNum = elf64_half_t(sectionHeaders.size());
        header.sectionHeadersOffset = out.position;
        header.sectionHeaderNameStringTableIndex = elf64_half_t(sectionHeaders.size() - 1);
        for(auto &sectionHeader: sectionHeaders)
            out.push_struct(sectionHeader);
        
        // Rewrite the header
        out.position = 0;
        out.push_struct(header);

        return out.data;
    }

    bool saveElf64ToFileNamed(const std::string &outputFileName)
    {
        auto encodedElf = encodeAsElf64();
        auto f = fopen(outputFileName.c_str(), "wb");
        if(!f)
        {
            perror("Failed to open output file.");
            abort();
        }

        if(fwrite(encodedElf.data(), encodedElf.size(), 1, f) != 1)
        {
            perror("Failed to write output file.");
            abort();
        }

        fclose(f);
        return true;
    }

    std::string name;
    SmoStringTable stringTable;
    std::vector<SmoSection> sections;
    size_t localSymbolCount = 0;
    std::vector<SmoSymbol> symbols;
};

std::vector<uint8_t> readWholeFile(const std::string &filename)
{
    std::vector<uint8_t> result;
    auto f = fopen(filename.c_str(), "rb");
    if(!f)
    {
        perror("Failed to open file");
        abort();
    }

    fseek(f, 0, SEEK_END);
    auto fileSize = ftell(f);
    fseek(f, 0, SEEK_SET);

    result.resize(fileSize);
    if(fread(result.data(), fileSize, 1, f) != 1)
    {
        perror("Failed to read file");
        abort();
    }
    
    fclose(f);

    return result;
}

void printHelp()
{
    printf("smo2obj -o <outputfile> <inputfile>\n");
}

void printVersion()
{
    printf("smo2obj version 0.1\n");
}

int main(int argc, const char **argv)
{
    std::string inputFileName;
    std::string outputFileName;

    for(int i = 1; i < argc; ++i)
    {
        std::string arg = argv[i];
        if(arg[0] == '-')
        {
            if(arg == "-h")
            {
                printHelp();
                return 0;
            }
            else if(arg == "-v")
            {
                printVersion();
                return 0;
            }
            else if(arg == "-o")
            {
                outputFileName = argv[++i];
            }
        }
        else
        {
            inputFileName = arg;
        }
    }

    if(inputFileName.empty() || outputFileName.empty())
    {
        printHelp();
        return 0;
    }

    auto smoModule = SmoModule();
    if(!smoModule.readFromFileNamed(inputFileName))
    {
        printf("Failed to read SMO module\n");
        return 1;
    }

    smoModule.saveElf64ToFileNamed(outputFileName);
    
    return 0;
}