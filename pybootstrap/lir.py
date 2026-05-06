from enum import Enum
import struct

# Same values as in elf
SmoSymbolBinding = Enum('SmoSymbolBinding', [("LOCAL", 0), ("GLOBAL", 1), ("WEAK", 2)])
SmoSymbolType = Enum('SmoSymbolType', [("NOTYPE", 0), ("OBJECT", 1), ("FUNC", 2), ("SECTION", 3)])

## Same flags as in elf.
LirSectionFlagNone = 0
LirSectionFlagWrite = 0x1
LirSectionFlagAlloc = 0x2
LirSectionFlagExecInstructions = 0x4

LirSectionHeaderTypeNull = 0x0
LirSectionHeaderTypeProgbits = 0x1
LirSectionHeaderTypeNobits = 0x8

## Relocations
class LirRelocation:
    Null              = 0
    Absolute8         = 1
    Absolute16        = 2
    Absolute32        = 3
    Absolute64        = 4
    Relative8         = 5
    Relative16        = 6
    Relative32        = 7
    Relative32AtGot   = 8
    Relative32AtPlt   = 9
    Relative64        = 10
    SectionRelative32 = 11

## X86 Registers
X86_REG_HALF_MASK = 7
X86_RAX = 0
X86_RCX = 1
X86_RDX = 2
X86_RBX = 3
X86_RSP = 4
X86_RBP = 5
X86_RSI = 6
X86_RDI = 7
X86_R8  = 8
X86_R9  = 9
X86_R10 = 10
X86_R11 = 11
X86_R12 = 12
X86_R13 = 13
X86_R14 = 14
X86_R15 = 15

X86_EAX  = 0
X86_ECX  = 1
X86_EDX  = 2
X86_EBX  = 3
X86_ESP  = 4
X86_EBP  = 5
X86_ESI  = 6
X86_EDI  = 7
X86_R8D  = 8
X86_R9D  = 9
X86_R10D = 10
X86_R11D = 11
X86_R12D = 12
X86_R13D = 13
X86_R14D = 14
X86_R15D = 15

def setInt32InByteArray(ba: bytearray, offset: int, value: int):
    ba[offset    ] = value & 0xff
    ba[offset + 1] = (value >> 8) & 0xff
    ba[offset + 2] = (value >> 16) & 0xff
    ba[offset + 3] = (value >> 24) & 0xff

class SmoHeader:
    StructFormat = '<LLLLLLLLLL'
    StructSize = struct.calcsize(StructFormat)
    MagicNumber, = struct.unpack('=L', b'SMO ')

    def __init__(self):
        self.magic = self.MagicNumber
        self.headerSize = self.StructSize
        self.nameStringOffset = 0
        self.functionEntryPoint = 0
        self.sectionTableOffset = 0
        self.sectionTableSize = 0
        self.stringTableOffset = 0
        self.stringTableSize = 0
        self.symbolTableOffset = 0
        self.symbolTableSize = 0

    def encode(self):
        return struct.pack(self.StructFormat, \
                        self.magic, self.headerSize, \
                        self.nameStringOffset, self.functionEntryPoint, \
                        self.sectionTableOffset, self.sectionTableSize, \
                        self.stringTableOffset, self.stringTableSize, \
                        self.symbolTableOffset, self.symbolTableSize)

    def decode(self, encodedBytes):
        self.magic, self.headerSize, \
        self.nameStringOffset, self.functionEntryPoint, \
        self.sectionTableOffset, self.sectionTableSize, \
        self.stringTableOffset, self.stringTableSize, \
        self.symbolTableOffset, self.symbolTableSize, = struct.unpack(self.StructFormat, encodedBytes)
        return self      

class SmoSectionHeader:
    StructFormat = '<LLLLLLLL'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self):
        self.nameIndex = 0
        self.offset = 0
        self.size = 0
        self.alignment = 0
        self.flags = 0
        self.type = 0
        self.relocationTableOffset = 0
        self.relocationTableSize = 0

    def encode(self):
        return struct.pack(self.StructFormat,  self.nameIndex, self.offset, self.size, self.alignment, self.flags, self.type, self.relocationTableOffset, self.relocationTableSize)

    def decode(self, encodedBytes):
        self.nameIndex, self.offset, self.size, self.alignment, self.flags, self.type, self.relocationTableOffset, self.relocationTableSize = struct.unpack(self.StructFormat, encodedBytes)
        return self     

class SmoRelocation:
    StructFormat = '<LLQq'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self):
        self.kind = LirRelocation.Null
        self.symbolIndex = 0
        self.offset = 0
        self.addend = 0

    def encode(self):
        return struct.pack(self.StructFormat, self.kind, self.symbolIndex, self.offset, self.addend)

    def decode(self, encodedBytes):
        self.kind, self.symbolIndex, self.offset, self.addend = struct.unpack(self.StructFormat, encodedBytes)
        return self
        
class SmoSymbol:
    StructFormat = '<QQLLLL'
    StructSize = struct.calcsize(StructFormat)

    def __init__(self):
        self.value = 0
        self.size = 0
        self.nameIndex = 0
        self.sectionIndex = 0
        self.binding = 0
        self.type = 0

    def encode(self):
        return struct.pack(self.StructFormat, self.value,  self.size, \
            self.nameIndex, self.sectionIndex, \
            self.binding, self.type)

    def decode(self, encodedBytes):
        self.value, self.size, \
        self.nameIndex, self.sectionIndex, \
        self.binding, self.type = struct.unpack(self.StructFormat, encodedBytes)
        return self

class LirModule:
    def __init__(self):
        self.name = "LirModule"
        self.sections = []
        self.sectionTable = {}
        self.symbolTable = []

    def addSymbol(self, symbol):
        symbol.index = len(self.symbolTable)
        self.symbolTable.append(symbol)

    def buildStringTable(self):
        table = LirStringTable()
        table.getOrAddString(self.name)
        for eachSection in self.sections:
            table.getOrAddString(eachSection.name)
        for eachSymbol in self.symbolTable:
            table.getOrAddString(eachSymbol.name)
        return table

    def getOrCreateSectionNamed(self, sectionName, type, flags):
        if sectionName in self.sectionTable:
            return self.sectionTable[sectionName]

        sectionIndex = len(self.sections)
        isNullSection = sectionIndex == 0

        newSection = LirModuleSection()
        newSection.index = len(self.sections)
        newSection.name = sectionName
        newSection.flags = flags
        newSection.type = type
        self.sections.append(newSection)
        self.sectionTable[sectionName] = newSection

        sectionSymbol = LirSymbol()
        newSection.sectionSymbol = sectionSymbol
        if not isNullSection:
            sectionSymbol.sectionIndex = sectionIndex
            sectionSymbol.binding = SmoSymbolBinding.LOCAL.value
            sectionSymbol.type = SmoSymbolType.SECTION.value
        self.symbolTable.append(sectionSymbol)
        return newSection

    def getOrCreateNullSection(self):
        return self.getOrCreateSectionNamed('', LirSectionHeaderTypeNull, 0)

    def getOrCreateTextSection(self):
        return self.getOrCreateSectionNamed('.text', LirSectionHeaderTypeProgbits, LirSectionFlagAlloc | LirSectionFlagExecInstructions)

    def getOrCreateRoDataSection(self):
        return self.getOrCreateSectionNamed('.rodata', LirSectionHeaderTypeProgbits, LirSectionFlagAlloc)

    def getOrCreateDataSection(self):
        return self.getOrCreateSectionNamed('.data', LirSectionHeaderTypeProgbits, LirSectionFlagAlloc | LirSectionFlagWrite)

    def getOrCreateCommonSections(self):
        self.getOrCreateNullSection()
        self.getOrCreateTextSection()
        self.getOrCreateRoDataSection()
        self.getOrCreateDataSection()

    def makeSingleSegmentRelocatedToAddress(self, baseAddress):
        sectionOffset = baseAddress
        for section in self.sections:
            section.virtualAddress = sectionOffset
            sectionOffset += len(section.data)
        
        segmentData = bytearray()
        for section in self.sections:
            segmentData += section.getDataRelocatedToVirtualAddress(self)

        return segmentData

    def encodeModuleObject(self):
        stringTable = self.buildStringTable()
        header = SmoHeader()

        # Sections
        currentOffset = SmoHeader.StructSize
        sectionHeaders = []
        for section in self.sections:
            sectionSize = section.finish(currentOffset)
            sectionHeader = SmoSectionHeader()
            sectionHeader.nameIndex = stringTable.getStringIndex(section.name)
            sectionHeader.offset = currentOffset
            sectionHeader.size = sectionSize
            sectionHeader.alignment = section.alignment
            sectionHeader.flags = section.flags
            sectionHeader.type = section.type
            currentOffset += sectionSize

            sectionHeader.relocationTableOffset = currentOffset
            sectionHeader.relocationTableSize = len(section.relocations)
            currentOffset += SmoRelocation.StructSize * len(section.relocations)

            sectionHeaders.append(sectionHeader)

        # Section header table
        header.sectionTableOffset = currentOffset
        header.sectionTableSize = len(sectionHeaders)
        currentOffset += SmoSectionHeader.StructSize * len(sectionHeaders)

        # Symbol table
        header.symbolTableOffset = currentOffset
        header.symbolTableSize = len(self.symbolTable)
        currentOffset += SmoSymbol.StructSize * len(self.symbolTable)

        # String table
        stringTable.fileOffset = currentOffset
        currentOffset += len(stringTable.data)

        header.nameStringOffset = stringTable.getStringIndex(self.name)
        header.stringTableOffset = stringTable.fileOffset
        header.stringTableSize = len(stringTable.data)

        ## Encode the header.
        encodedData = bytearray()
        encodedData += header.encode()

        ## Encode the sections
        for eachSection in self.sections:
            encodedData += eachSection.data
            for eachRelocation in eachSection.relocations:
                encodedData += eachRelocation.encode()

        ## Encode the section table
        for eachSectionHeader in sectionHeaders:
            encodedData += eachSectionHeader.encode()

        # Encode the symbols
        for eachSymbol in self.symbolTable:
            symbol = SmoSymbol()
            symbol.value = eachSymbol.value
            symbol.size = eachSymbol.size
            symbol.nameIndex = stringTable.getStringIndex(eachSymbol.name)
            symbol.sectionIndex = eachSymbol.sectionIndex
            symbol.binding = eachSymbol.binding
            symbol.type = eachSymbol.type
            encodedData += symbol.encode()

        ## Encode the string table
        encodedData += stringTable.data
        return encodedData

    def decodeModuleObject(self, encodedModule):
        header = SmoHeader().decode(encodedModule[0: SmoHeader.StructSize])

        # String tables.
        stringTableData = encodedModule[header.stringTableOffset : header.stringTableOffset + header.stringTableSize]
        stringTableDecoder = LirStringTableDecoder(stringTableData)
        self.name = stringTableDecoder.getStringWithIndex(header.nameStringOffset)

        # Section tables.
        sectionHeaderOffset = header.sectionTableOffset
        for i in range(header.sectionTableSize):
            sectionHeaderData = encodedModule[sectionHeaderOffset : sectionHeaderOffset + SmoSectionHeader.StructSize]
            sectionHeader = SmoSectionHeader().decode(sectionHeaderData)

            section = LirModuleSection()
            section.index = len(self.sections)
            section.name = stringTableDecoder.getStringWithIndex(sectionHeader.nameIndex)
            section.flags = sectionHeader.flags
            section.type = sectionHeader.type
            section.alignment = sectionHeader.alignment
            section.data = encodedModule[sectionHeader.offset : sectionHeader.offset + sectionHeader.size]
            self.sections.append(section)

            sectionHeaderOffset += SmoSectionHeader.StructSize

        # Symbol table.
        symbolOffset = header.symbolTableOffset
        for i in range(header.symbolTableSize):
            symbolData = encodedModule[symbolOffset : symbolOffset + SmoSymbol.StructSize]
            symbol = SmoSymbol().decode(symbolData)
            
            lirSymbol = LirSymbol()
            lirSymbol.value = symbol.value
            lirSymbol.size = symbol.size
            lirSymbol.name = stringTableDecoder.getStringWithIndex(symbol.nameIndex)
            lirSymbol.sectionIndex = symbol.sectionIndex
            lirSymbol.binding = symbol.binding
            lirSymbol.type = symbol.type

            self.symbolTable.append(lirSymbol)

            symbolOffset += SmoSymbol.StructSize

        return self
    
    def saveModuleToFile(self, filename):
        encodedData = self.encodeModuleObject()
        with open(filename, "wb") as f:
            f.write(encodedData)

    def loadModuleToFile(self, filename):
        with open(filename, "rb") as f:
            self.decodeModuleObject(f.read())
        return self

class LirModuleElement:
    def __init__(self):
        self.fileOffset = 0

class LirModuleSection(LirModuleElement):
    def __init__(self):
        self.index = None
        self.name = None
        self.data = bytearray()
        self.sectionSymbol = None
        self.alignment = 1
        self.flags = 0
        self.type = 0
        self.virtualAddress = 0
        self.relocations = []

    def finish(self, fileOffset):
        self.fileOffset = fileOffset
        return len(self.data)

    def getDataRelocatedToVirtualAddress(self, module: LirModule):
        relocatedData = bytearray(self.data)
        for relocation in self.relocations:
            symbol = module.symbolTable[relocation.symbolIndex]
            symbolSection = module.sections[symbol.sectionIndex]
            symbolValue = symbolSection.virtualAddress + symbol.value
            relocationAddress = self.virtualAddress + relocation.offset
            match relocation.kind:
                case LirRelocation.Relative32 | LirRelocation.Relative32AtGot | LirRelocation.Relative32AtPlt:
                    relocationValue = symbolValue - relocationAddress + relocation.addend
                    setInt32InByteArray(relocatedData, relocation.offset, relocationValue)
                case _: raise RuntimeError("Unsupported relocation kind")
        return relocatedData

class LirSymbol:
    def __init__(self):
        self.value = 0
        self.size = 0
        self.name = ''
        self.sectionIndex = 0
        self.binding = SmoSymbolBinding.LOCAL.value
        self.type = SmoSymbolType.NOTYPE.value
        self.index = 0

class LirStringTable(LirModuleElement):
    def __init__(self):
        self.data = bytearray()
        self.data += b'\0'
        self.stringTable = {}

    def getOrAddString(self, string):
        if string is None or len(string) == 0:
            return 0
        if string in self.stringTable:
            return self.stringTable[string]

        stringOffset = len(self.data)
        stringData = string.encode('utf8')
        self.data += stringData
        self.data += b'\0'
        self.stringTable[string] = stringOffset
        assert stringOffset

    def getStringIndex(self, string):
        if string is None or len(string) == 0:
            return 0
        assert string in self.stringTable
        return self.stringTable[string]
        
class LirStringTableDecoder:
    def __init__(self, data):
        self.data = data

    def getStringWithIndex(self, index):
        if index == 0:
            return ''
        
        startIndex = index
        endIndex = startIndex
        while self.data[endIndex] != 0:
            endIndex += 1
        bytesRange = self.data[startIndex : endIndex]
        return bytesRange.decode('utf-8')

class LirAssembler:
    def __init__(self, module: LirModule):
        self.module = module
        self.currentSection : LirModuleSection = None

    def textSection(self):
        self.currentSection = self.module.getOrCreateTextSection()
    
    def rodataSection(self):
        self.currentSection = self.module.getOrCreateRoDataSection()

    def dataSection(self):
        self.currentSection = self.module.getOrCreateDataSection()

    def addByte(self, byte):
        self.currentSection.data.append(byte)

    def addByteList(self, byteList):
        for byte in byteList:
            self.currentSection.data.append(byte)
    
    def addEmptyFourBytes(self):
        self.addByte(0)
        self.addByte(0)
        self.addByte(0)
        self.addByte(0)
    
    def addInstructionRelocation(self, kind, symbol, addend):
        relocation = SmoRelocation()
        relocation.kind = kind
        relocation.symbolIndex = symbol.index
        relocation.offset = len(self.currentSection.data)
        relocation.addend = addend
        self.currentSection.relocations.append(relocation)

    def makeGlobalFunctionSymbol(self, name) -> LirSymbol:
        symbol = LirSymbol()
        symbol.name = name
        symbol.binding = SmoSymbolBinding.GLOBAL.value
        symbol.type = SmoSymbolType.FUNC.value
        self.module.addSymbol(symbol)
        return symbol

    def makeGlobalFunctionSymbolHere(self, name) -> LirSymbol:
        symbol = self.makeGlobalFunctionSymbol(name)
        self.setSymbolHere(symbol)
        return symbol

    def setSymbolHere(self, symbol) -> LirSymbol:
        symbol.sectionIndex = self.currentSection.index
        symbol.value = len(self.currentSection.data)
        return symbol

    def endFunctionSymbolHere(self, symbol: LirSymbol):
        symbol.size = len(self.currentSection.data) - symbol.value

    def x86_rexByte(self, W, R, X, B):
        byte = 0x40
        if W: byte |= 1<<3
        if R: byte |= 1<<2
        if X: byte |= 1<<1
        if B: byte |= 1<<0
        self.addByte(byte)

    def x86_rex(self, W, R, X, B):
        if W or R or X or B:
            self.x86_rexByte(W, R, X, B)

    def x86_rexRmReg(self, W, rm, reg):
        self.x86_rex(W, reg > X86_REG_HALF_MASK, False, rm > X86_REG_HALF_MASK);

    def x86_rexRm(self, W, rm):
        self.x86_rex(W, False, False, rm > X86_REG_HALF_MASK)

    def x86_opcode(self, opcode):
        self.addByte(opcode)

    def x86_imm32(self, immediate):
        self.addByte(immediate & 0xFF)
        self.addByte((immediate >> 8) & 0xFF)
        self.addByte((immediate >> 16) & 0xFF)
        self.addByte((immediate >> 24) & 0xFF)

    def x86_modRmByte(self, rm, regOpcode, mod):
        return (rm & X86_REG_HALF_MASK) | ((regOpcode & X86_REG_HALF_MASK) << 3) | (mod << 6)

    def x86_modRmReg(self, rm, reg):
        self.addByte(self.x86_modRmByte(rm, reg, 3))

    def x86_modRmOp(self, rm, opcode):
        self.addByte(self.x86_modRmByte(rm, opcode, 3))

    def x86_endbr64(self):
        self.addByteList([0xF3, 0x0F, 0x1E, 0xFA])

    def x86_callGsv(self, symbol):
        self.addByte(0xE8)
        self.addInstructionRelocation(LirRelocation.Relative32AtPlt, symbol, -4)
        self.addEmptyFourBytes()

    def x86_mov64RegReg_nopt(self, destination, source):
        self.x86_rexRmReg(True, source, destination)
        self.x86_opcode(0x8B)
        self.x86_modRmReg(source, destination)

    def x86_mov64RegReg(self, dest, source):
        if dest != source:
            self.x86_mov64RegReg_nopt(dest, source)

    def x86_alu32RmReg(self, opcode, destination, source):
        self.x86_rexRmReg(False, destination, source)
        self.x86_opcode(opcode)
        self.x86_modRmReg(destination, source)

    def x86_mov32RegReg_nopt(self, destination, source):
        self.x86_rexRmReg(False, source, destination)
        self.x86_opcode(0x8B)
        self.x86_modRmReg(source, destination)

    def x86_mov32RegImm32(self, destination, value):
        self.x86_rexRm(False, destination)
        self.x86_opcode(0xC7)
        self.x86_modRmOp(destination, 0)
        self.x86_imm32(value)

    def x86_mov32RegReg(self, dest, source):
        if dest != source:
            self.x86_mov32RegReg_nopt(dest, source)

    def x86_add32RegReg(self, destination, source):
        self.x86_alu32RmReg(0x01, destination, source)

    def x86_ret(self):
        self.addByte(0xC3)

    def x86_syscall(self):
        self.addByte(0x0F)
        self.addByte(0x05)

    def x86_int3(self):
        self.addByte(0xCC)

    def x86_entryPointForGsv(self, callSymbol):
        entrySymbol = self.makeGlobalFunctionSymbolHere('__entry')
        ## Call the provided function.
        self.x86_callGsv(callSymbol)

        # Linux exit syscall
        self.x86_mov64RegReg(X86_RDI, X86_RAX)
        self.x86_mov32RegImm32(X86_RAX, 60)
        self.x86_syscall()

        self.endFunctionSymbolHere(entrySymbol)