from enum import Enum
from mirContext import *

MirOpcode = Enum('MirOpcode', [
    'Nop',
    
    ## Function arguments
    'ArgumentInt32', 'ArgumentInt64', 'ArgumentPointer', 'ArgumentGCPointer', 'ArgumentFloat32', 'ArgumentFloat64',

    ## Function callouts
    'BeginCall',
    'CallArgumentInt32', 'CallArgumentInt64', 'CallArgumentPointer', 'CallArgumentGCPointer', 'CallArgumentFloat32', 'CallArgumentFloat64',
    'CallInt32Result', 'CallInt64Result', 'CallPointerResult', 'CallGCPointerResult', 'CallVoidResult', 'CallFloat32Result', 'CallFloat64Result',

    ## Memory allocation
    'GCAllocate',

    ## Load and store
    'LoadUInt8', 'LoadUInt16', 'LoadUInt32', 'LoadUInt64',
    'LoadInt8', 'LoadInt16', 'LoadInt32', 'LoadInt64',
    'LoadPointer', 'LoadGCPointer', 'LoadFloat32', 'LoadFloat64',

    'StoreInt8', 'StoreInt16', 'StoreInt32', 'StoreInt64',
    'StorePointer', 'StoreGCPointer', 'StoreFloat32', 'StoreFloat64',

    ## Phi
    'PhiInt32', 'PhiInt64', 'PhiPointer', 'PhiGCPointer', 'PhiFloat32', 'PhiFloat64',
    
    'PhiSourceInt32', 'PhiSourceInt64', 'PhiSourcePointer', 'PhiSourceGCPointer', 'PhiSourceFloat32', 'PhiSourceFloat64',

    ## Branches
    'Jump', 'JumpIfTrue', 'JumpIfFalse',

    ## Arithmetic
    'Int32Neg', 'Int64Neg',
    'Int32Add', 'Int64Add',
    'Int32Sub', 'Int64Sub',
    'Int32Mul', 'Int64Mul',
    'Int32SDiv', 'Int64SDiv',
    'Int32UDiv', 'Int64UDiv',
    'Int32SMod', 'Int64SMod',
    'Int32UMod', 'Int64UMod',

    ## Bitwise
    'Int32BitNot', 'Int64BitNot',
    'Int32BitAnd', 'Int64BitAnd',
    'Int32BitOr' , 'Int64BitOr',
    'Int32BitXor', 'Int64BitXor',
    'Int32ShiftLeft', 'Int64ShiftLeft',
    'Int32LShiftRight', 'Int64LShiftRight',
    'Int32AShiftRight', 'Int64AShiftRight',


    ## Comparisons
    'Int32Equals', 'Int64Equals', 'PointerEquals',
    'Int32NotEquals', 'Int64NotEquals', 'PointerNotEquals',

    'Int32LessThan', 'UInt32LessThan', 'Int64LessThan', 'UInt64LessThan',
    'Int32LessOrEquals', 'UInt32LessOrEquals', 'Int64LessOrEquals', 'UInt64LessOrEquals',
    'Int32GreaterThan', 'UInt32GreaterThan', 'Int64GreaterThan', 'UInt64GreaterThan',
    'Int32GreaterOrEqual', 'UInt32GreaterOrEqual', 'Int64GreaterOrEqual', 'UInt64GreaterOrEqual',

    ## Floating point arithmetic
    'Float32Neg',  'Float64Neg',
    'Float32Add',  'Float64Add',
    'Float32Sub',  'Float64Sub',
    'Float32Mul',  'Float64Mul',
    'Float32Div',  'Float64Div',
    'Float32Sqrt', 'Float64Sqrt',

    ## Pointer arithmetic
    'PointerAddConstantOffset',

    ## Constants
    'ConstInt32', 'ConstInt64', 'ConstPointer', 'ConstFloat32', 'ConstFloat64',
    'ConstGCPointer', 'ConstInteger', 'ConstCharacter', 'ConstFloat', 'ConstVoid',

    ## Returns
    'ReturnInt32', 'ReturnInt64', 'ReturnPointer', 'ReturnFloat32', 'ReturnFloat64',
    'ReturnGCPointer', 'ReturnVoid',
])


class MirPackage:
    def __init__(self, context: MirContext, name: str):
        self.context = context
        self.elementTable = []
        self.translatedPrimitiveMap = {}
        self.translatedFunctionMap = {}
        self.name = name

    def addElement(self, element):
        assert element.module is None
        self.elementTable.append(element)
        element.module = self

    def addMirFunction(self, mirFunction):
        self.addElement(mirFunction)
        assert mirFunction.sourceFunction not in self.translatedFunctionMap
        self.translatedFunctionMap[mirFunction.sourceFunction] = mirFunction

    def dumpToConsole(self):
        for element in self.elementTable:
            element.dumpToConsole()

    def getOrCreateRuntimePrimitiveNamed(self, primitiveRuntimeName):
        if primitiveRuntimeName in self.translatedPrimitiveMap:
            return self.translatedPrimitiveMap[primitiveRuntimeName]

        primitive = MirImportedFunction(primitiveRuntimeName)
        primitive.implementation = self.context.getRuntimePrimitiveImplementationOrNone(primitiveRuntimeName)
        self.translatedPrimitiveMap[primitiveRuntimeName] = primitive
        return primitive
    
class MirPackageElement:
    def __init__(self):
        self.module: MirPackage = None

    def isTemporary(self):
        return False

class MirTypeWithMethodDictionary(MirPackageElement):
    def __init__(self, name, sourceType):
        super().__init__()
        self.name = name
        self.sourceType = sourceType
        self.metaType = None
        self.children = []
        self.methodDictionary = {}

    def withSelectorAddMethod(self, selector, method):
        assert selector not in self.methodDictionary
        self.children.append(method)
        self.methodDictionary[selector] = method

    def dumpToConsole(self):
        print(str(self))
        for child in self.children:
            print(child)

    def __str__(self):
        return 'typeWithMethodDict ' + self.name

class MirImportedFunction(MirPackageElement):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.implementation = None

    def evaluateWithArguments(self, arguments):
        return self.implementation(*arguments)

    def __str__(self):
        return 'importedFunction ' + self.name

class MirGlobalData(MirPackageElement):
    def __init__(self, data: bytes, name = None):
        super().__init__()
        self.data = data
        self.name = name

class MirGlobalConstant:
    def __init__(self, value, type):
        self.value = value
        self.type = type

class MirFunction(MirPackageElement):
    def __init__(self, name = ''):
        super().__init__()
        self.sourcePosition = None
        self.sourceFunction = None
        self.name = name
        self.firstBasicBlock = None
        self.lastBasicBlock = None
        self.enumeratedInstructions = None
        self.temporaries = []

    def newTemporary(self, type, sourcePosition, name):
        temporary = MirTemporary(type, len(self.temporaries), sourcePosition, name)
        self.temporaries.append(temporary)
        return temporary

    def addBasicBlock(self, basicBlock):
        if self.firstBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            self.lastBasicBlock.next = basicBlock
            basicBlock.previous = self.lastBasicBlock
            self.lastBasicBlock = basicBlock

    def dumpToConsole(self):
        self.enumerateInstructions()
        print("function " + str(self.name) + " {")
        block = self.firstBasicBlock
        while block is not None:
            block.dumpToConsole()
            block = block.next

        print("}")

    def enumerateInstructions(self):
        if self.enumeratedInstructions is not None:
            return self.enumeratedInstructions
        
        self.enumeratedInstructions = []
        block = self.firstBasicBlock
        while block is not None:
            block.index = len(self.enumeratedInstructions)
            self.enumeratedInstructions.append(block)

            instruction = block.firstInstruction
            while instruction is not None:
                instruction.index = len(self.enumeratedInstructions)
                self.enumeratedInstructions.append(instruction)
                instruction = instruction.next

            block = block.next

        return self.enumeratedInstructions
    
    def evaluateWithArguments(self, arguments):
        self.enumerateInstructions()
        context = MirFunctionActivationContext(self, self.enumeratedInstructions, arguments)
        return context.evaluate()
    
    def __str__(self):
        return '@' + str(self.name)

class MirFunctionActivationContext:
    def __init__(self, function, instructions, arguments):
        self.function = function
        self.instructions = instructions
        self.arguments = arguments
        self.calloutArguments = []
        self.temporaries = [None] * len(function.temporaries)
        self.instructionPC = 0
        self.pc = 0
        self.hasReturnValue = False
        self.returnValue = None

    def evaluate(self):
        while self.pc < len(self.instructions):
            self.instructionPC = self.pc
            self.pc += 1
            instruction = self.instructions[self.instructionPC]
            instruction.evaluateInContext(self)

            if self.hasReturnValue:
                return self.returnValue

        raise RuntimeError("Reached beyond the instruction list.")
    def getTempValue(self, temp):
        return self.temporaries[temp.index]
    
    def getTempOrConstantValue(self, tempOrConstant):
        if tempOrConstant.isTemporary():
            return self.getTempValue(tempOrConstant)
        return tempOrConstant

    def setTempValue(self, temp, value):
        self.temporaries[temp.index] = value

    def setReturnValue(self, value):
        self.returnValue = value
        self.hasReturnValue = True

    def getArgumentValue(self, index):
        return self.arguments[index]
    
    def beginCall(self):
        self.calloutArguments = []

    def addCallArgument(self, argument):
        self.calloutArguments.append(argument)

class MirTemporary:
    def __init__(self, type, index, sourcePosition, name):
        self.type = type
        self.index = index
        self.sourcePosition = sourcePosition
        self.name = name

    def isTemporary(self):
        return True

    def __str__(self):
        return '$' + str(self.index)

class MirFunctionLocal:
    def __init__(self, sourcePosition, name = ''):
        self.index = -1
        self.sourcePosition = sourcePosition
        self.name = name
    
class MirBasicBlock(MirFunctionLocal):
    def __init__(self, sourcePosition, name = ''):
        super().__init__(sourcePosition, name)
        self.previous = None
        self.next = None
        self.firstInstruction = None
        self.lastInstruction = None

    def addInstruction(self, instruction):
        if self.firstInstruction is None:
            self.firstInstruction = self.lastInstruction = instruction
        else:
            self.lastInstruction.next = instruction
            instruction.previous = self.lastInstruction
            self.lastInstruction = instruction

    def dumpToConsole(self):
        print(str(self) + ":")

        instruction = self.firstInstruction
        while instruction is not None:
            instruction.dumpToConsole()
            instruction = instruction.next

    def evaluateInContext(self, context):
        ## Nothing is required here.
        pass

    def __str__(self):
        return str(self.index) + '|' + self.name

class MirMemorySimulation:
    def __init__(self, size):
        self.size = size
        self.data = bytearray(self.size)

    def isMirMemorySimulation(self):
        return True

    def loadUInt8At(self, offset):
        return self.data[offset]

    def loadUInt16At(self, offset):
        return self.data[offset] | (self.data[offset + 1] << 8)

    def loadUInt32At(self, offset):
        return self.data[offset] | (self.data[offset + 1] << 8) | (self.data[offset + 2] << 16) | (self.data[offset + 3] << 24)

    def loadUInt64At(self, offset):
        return self.data[offset] | \
            (self.data[offset + 1] <<  8) | \
            (self.data[offset + 2] << 16) | \
            (self.data[offset + 3] << 24) | \
            (self.data[offset + 4] << 32) | \
            (self.data[offset + 5] << 40) | \
            (self.data[offset + 6] << 48) | \
            (self.data[offset + 7] << 56)

    def loadInt8At(self, offset):
        loadedValue = self.loadUInt8At(offset)
        return (loadedValue & 0x7f) - (loadedValue & 0x80)

    def loadInt16At(self, offset):
        loadedValue = self.loadUInt16At(offset)
        return (loadedValue & 0x7fff) - (loadedValue & 0x8000)

    def loadInt32At(self, offset):
        loadedValue = self.loadUInt32At(offset)
        return (loadedValue & 0x7fffffff) - (loadedValue & 0x80000000)

    def loadInt64At(self, offset):
        loadedValue = self.loadUInt32At(offset)
        return (loadedValue & 0x7fffffffffffffff) - (loadedValue & 0x8000000000000000)

    def storeInt8At(self, offest, value):
        self.data[offest] = value & 0xff

    def storeInt16At(self, offest, value):
        self.data[offest    ] = value & 0xff
        self.data[offest + 1] = (value >> 8) & 0xff

    def storeInt32At(self, offest, value):
        self.data[offest    ] = value & 0xff
        self.data[offest + 1] = (value >> 8) & 0xff
        self.data[offest + 2] = (value >> 16) & 0xff
        self.data[offest + 3] = (value >> 24) & 0xff
    
    def storeInt64At(self, offest, value):
        self.data[offest    ] = value & 0xff
        self.data[offest + 1] = (value >> 8) & 0xff
        self.data[offest + 2] = (value >> 16) & 0xff
        self.data[offest + 3] = (value >> 24) & 0xff
        self.data[offest + 4] = (value >> 32) & 0xff
        self.data[offest + 5] = (value >> 40) & 0xff
        self.data[offest + 6] = (value >> 48) & 0xff
        self.data[offest + 7] = (value >> 56) & 0xff

class MirMemorySimulationPointer:
    def __init__(self, memory: MirMemorySimulation, offset: int):
        self.memory = memory
        self.offset = offset

    def __add__(self, offset):
        return MirMemorySimulationPointer(self.memory, self.offset + offset)

    def isMirMemorySimulationPointer(self):
        return True

    def loadUInt8(self):
        return self.memory.loadUInt8At(self.offset)

    def loadUInt16(self):
        return self.memory.loadUInt16At(self.offset)

    def loadUInt32(self):
        return self.memory.loadUInt32At(self.offset)

    def loadUInt64(self):
        return self.memory.loadUInt64At(self.offset)

    def loadInt8(self):
        return self.memory.loadInt8At(self.offset)

    def loadInt16(self):
        return self.memory.loadInt16At(self.offset)

    def loadInt32(self):
        return self.memory.loadInt32At(self.offset)

    def loadInt64(self):
        return self.memory.loadInt64At(self.offset)

    def storeInt8(self, value):
        self.memory.storeInt8At(self.offset, value)

    def storeInt16(self, value):
        self.memory.storeInt16At(self.offset, value)

    def storeInt32(self, value):
        self.memory.storeInt32At(self.offset, value)

    def storeInt64(self, value):
        self.memory.storeInt64At(self.offset, value)

class MirInstruction(MirFunctionLocal):
    def __init__(self, result, opcode: MirOpcode, firstArgument, secondArgument, sourcePosition, name = ''):
        super().__init__(sourcePosition, name)
        self.result = result
        self.opcode = opcode
        self.firstArgument = firstArgument
        self.secondArgument = secondArgument
        self.previous = None
        self.next = None

    def dumpToConsole(self):
        dumpString = "    "
        if self.result is not None:
            dumpString += str(self.result) + " := " 
        dumpString += str(self.opcode.name)
        if self.firstArgument is not None: dumpString += ' ' + str(self.firstArgument)
        if self.secondArgument is not None: dumpString += ' ' + str(self.secondArgument)
        print(dumpString)

    def evaluateInContext(self, context: MirFunctionActivationContext):
        match self.opcode:
            ## Calling and being called
            case MirOpcode.ArgumentInt32 | MirOpcode.ArgumentInt64 | MirOpcode.ArgumentPointer |MirOpcode.ArgumentGCPointer:
                context.setTempValue(self.result, context.arguments[self.index - 1])

            case MirOpcode.BeginCall:
                context.beginCall()
            
            case MirOpcode.CallArgumentInt32 | MirOpcode.CallArgumentInt64 | MirOpcode.CallArgumentPointer | MirOpcode.CallArgumentGCPointer:
                context.addCallArgument(context.getTempValue(self.firstArgument))

            case MirOpcode.CallInt32Result | MirOpcode.CallInt64Result | MirOpcode.CallPointerResult | MirOpcode.CallGCPointerResult:
                functional = context.getTempOrConstantValue(self.firstArgument)
                result = functional.evaluateWithArguments(context.calloutArguments)
                context.setTempValue(self.result, result)

            case MirOpcode.GCAllocate:
                memoryDescriptor = self.firstArgument
                memory = MirMemorySimulation(memoryDescriptor.size)
                pointer = MirMemorySimulationPointer(memory, 0)
                context.setTempValue(self.result, pointer)

            ## Store
            case MirOpcode.StoreInt8:
                pointer = context.getTempOrConstantValue(self.firstArgument)
                valueToStore = context.getTempOrConstantValue(self.secondArgument)
                pointer.storeInt8(valueToStore)

            case MirOpcode.StoreInt16:
                pointer = context.getTempOrConstantValue(self.firstArgument)
                valueToStore = context.getTempOrConstantValue(self.secondArgument)
                pointer.storeInt16(valueToStore)

            case MirOpcode.StoreInt32:
                pointer = context.getTempOrConstantValue(self.firstArgument)
                valueToStore = context.getTempOrConstantValue(self.secondArgument)
                pointer.storeInt32(valueToStore)

            case MirOpcode.StoreInt64:
                pointer = context.getTempOrConstantValue(self.firstArgument)
                valueToStore = context.getTempOrConstantValue(self.secondArgument)
                pointer.storeInt64(valueToStore)

            ## Load
            case MirOpcode.LoadUInt8:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadUInt8()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadUInt16:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadUInt16()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadUInt32:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadUInt32()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadUInt64:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadUInt64()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadInt8:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadInt8()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadInt16:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadInt16()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadInt32:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadInt32()
                context.setTempValue(self.result, value)

            case MirOpcode.LoadInt64:
                pointer: MirMemorySimulationPointer = context.getTempOrConstantValue(self.firstArgument)
                value = pointer.loadInt64()
                context.setTempValue(self.result, value)

            ## Phis
            case MirOpcode.PhiInt32 | MirOpcode.PhiInt64 | MirOpcode.PhiPointer | MirOpcode.PhiGCPointer | MirOpcode.PhiFloat32 | MirOpcode.PhiFloat64:
                # Nothing is required here
                pass
            case MirOpcode.PhiSourceInt32 | MirOpcode.PhiSourceInt64 | MirOpcode.PhiSourcePointer | MirOpcode.PhiSourceGCPointer | MirOpcode.PhiSourceFloat32 | MirOpcode.PhiSourceFloat64:
                value = context.getTempOrConstantValue(self.firstArgument)
                context.setTempValue(self.result, value)

            ## Jumps
            case MirOpcode.Jump:
                context.pc = self.firstArgument.index
            case MirOpcode.JumpIfTrue:
                condition = context.getTempValue(self.firstArgument)
                if condition:
                    context.pc = self.secondArgument.index
            case MirOpcode.JumpIfFalse:
                condition = context.getTempValue(self.firstArgument)
                if not condition:
                    context.pc = self.secondArgument.index

            ## Nop
            case MirOpcode.Nop:
                pass

            ## Arihmetic
            case MirOpcode.Int32Neg | MirOpcode.Int64Neg:
                context.setTempValue(self.result, -context.getTempValue(self.firstArgument))
            case MirOpcode.Int32Add | MirOpcode.Int64Add:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) + context.getTempValue(self.secondArgument))
            case MirOpcode.Int32Sub | MirOpcode.Int64Sub:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) - context.getTempValue(self.secondArgument))
            case MirOpcode.Int32Mul | MirOpcode.Int64Mul:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) * context.getTempValue(self.secondArgument))
            case MirOpcode.Int32SDiv | MirOpcode.Int64SDiv:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) // context.getTempValue(self.secondArgument))
            case MirOpcode.Int32SMod | MirOpcode.Int64SMod:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) % context.getTempValue(self.secondArgument))
            case MirOpcode.Int32UDiv | MirOpcode.Int64UDiv:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) // context.getTempValue(self.secondArgument))
            case MirOpcode.Int32UMod | MirOpcode.Int64UMod:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) % context.getTempValue(self.secondArgument))

            ## Bitwise operations
            case MirOpcode.Int32BitNot | MirOpcode.Int64BitNot:
                context.setTempValue(self.result, ~context.getTempValue(self.firstArgument))
            case MirOpcode.Int32BitAnd | MirOpcode.Int64BitAnd:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) & context.getTempValue(self.secondArgument))
            case MirOpcode.Int32BitOr | MirOpcode.Int64BitOr:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) | context.getTempValue(self.secondArgument))
            case MirOpcode.Int32BitXor | MirOpcode.Int64BitXor:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) ^ context.getTempValue(self.secondArgument))
            case MirOpcode.Int32ShiftLeft | MirOpcode.Int64ShiftLeft:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) << context.getTempValue(self.secondArgument))
            case MirOpcode.Int32AShiftRight | MirOpcode.Int64AShiftRight:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) >> context.getTempValue(self.secondArgument))
            case MirOpcode.Int32LShiftRight | MirOpcode.Int64LShiftRight:
                ## TODO: Use an actual logical right shift.
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) >> context.getTempValue(self.secondArgument))

            ## Equality comparisons
            case MirOpcode.Int32Equals | MirOpcode.Int64Equals | MirOpcode.PointerEquals:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) == context.getTempValue(self.secondArgument))
            case MirOpcode.Int32NotEquals | MirOpcode.Int64NotEquals | MirOpcode.PointerNotEquals:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) != context.getTempValue(self.secondArgument))

            ## Comparisons
            case MirOpcode.Int32LessThan | MirOpcode.UInt32LessThan | MirOpcode.Int64LessThan | MirOpcode.UInt64LessThan:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) < context.getTempValue(self.secondArgument))
            case MirOpcode.Int32LessOrEquals | MirOpcode.UInt32LessOrEquals | MirOpcode.Int64LessOrEquals | MirOpcode.UInt64LessOrEquals:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) <= context.getTempValue(self.secondArgument))
            case MirOpcode.Int32GreaterThan | MirOpcode.UInt32GreaterThan | MirOpcode.Int64GreaterThan | MirOpcode.UInt64GreaterThan:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) > context.getTempValue(self.secondArgument))
            case MirOpcode.Int32GreaterOrEqual | MirOpcode.UInt32GreaterOrEqual | MirOpcode.Int64GreaterOrEqual | MirOpcode.UInt64GreaterOrEqual:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) > context.getTempValue(self.secondArgument))

            ## Pointer arithmetic.
            case MirOpcode.PointerAddConstantOffset:
                context.setTempValue(self.result, context.getTempValue(self.firstArgument) + self.secondArgument)

            ## Constants
            case MirOpcode.ConstInt32 | MirOpcode.ConstInt64 | MirOpcode.ConstPointer | MirOpcode.ConstFloat32 | MirOpcode.ConstFloat64 | MirOpcode.ConstGCPointer | \
                MirOpcode.ConstCharacter | MirOpcode.ConstInteger | MirOpcode.ConstFloat | MirOpcode.ConstVoid:
                context.setTempValue(self.result, self.firstArgument)

            ## Returns
            case MirOpcode.ReturnInt32 | MirOpcode.ReturnInt64 | MirOpcode.ReturnPointer | MirOpcode.ReturnFloat32 | MirOpcode.ReturnFloat64 | MirOpcode.ReturnGCPointer:
                context.setReturnValue(context.getTempValue(self.firstArgument))
            case MirOpcode.ReturnVoid:
                context.setReturnValue(None)
            case _:
                raise RuntimeError("Unimplemented instruction " + self.opcode.name)

class MirBuilder:
    def __init__(self, function: MirFunction, basicBlock: MirBasicBlock):
        self.function = function
        self.basicBlock = basicBlock

    def addInstruction(self, instruction):
        self.basicBlock.addInstruction(instruction)
        return instruction
    
    def conditionalBranchAt(self, condition, trueDestination, falseDestination, sourcePosition, name = ''):
        self.jumpIfFalse(condition, falseDestination, sourcePosition, name)
        self.jump(trueDestination, sourcePosition, name)

    def gcAllocateAt(self, memoryDescriptor, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.GCAllocate, memoryDescriptor, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def storeInt8At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreInt8, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeInt16At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreInt16, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeInt32At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreInt32, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeInt64At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreInt64, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storePointerAt(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StorePointer, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeGCPointerAt(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreGCPointer, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeFloat32At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreFloat32, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def storeFloat64At(self, pointer, value, sourcePosition, name =''):
        instruction = MirInstruction(None, MirOpcode.StoreFloat64, pointer, value, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def loadInt8At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadInt8, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadInt16At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int16Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadInt16, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadInt32At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadInt32, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadInt64At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadInt64, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadUInt8At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.uint8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadUInt8, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadUInt16At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.uint16Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadUInt16, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadUInt32At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.uint32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadUInt32, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadUInt64At(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.uint64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadUInt64, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadPointer(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadPointer, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def loadGCPointer(self, storage, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.LoadGCPointer, storage, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def jump(self, destination, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.Jump, destination, None, sourcePosition, name)
        self.addInstruction(instruction)

    def jumpIfTrue(self, condition, destination, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.JumpIfTrue, condition, destination, sourcePosition, name)
        self.addInstruction(instruction)

    def jumpIfFalse(self, condition, destination, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.JumpIfFalse, condition, destination, sourcePosition, name)
        self.addInstruction(instruction)

    def argumentInt32At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentInt32, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def argumentInt64At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentInt64, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def argumentPointerAt(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentPointer, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def argumentGCPointerAt(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentGCPointer, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def argumentFloat32At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.float32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentFloat32, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def argumentFloat64At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.float64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.ArgumentFloat64, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def beginCallAt(self, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.BeginCall, None, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callArgumentInt32At(self, value, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.CallArgumentInt32, value, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callArgumentInt64At(self, value, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.CallArgumentInt64, value, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callArgumentPointerAt(self, value, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.CallArgumentPointer, value, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callArgumentGCPointerAt(self, value, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.CallArgumentGCPointer, value, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callArgumentFloat32(self, value, sourcePosition, name = ''):
        instruction = MirInstruction(None, MirOpcode.CallArgumentFloat32, value, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callInt32ResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallInt32Result, function, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def callInt64ResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallInt64Result, function, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def callPointerResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallPointerResult, function, None, sourcePosition, name)
        self.addInstruction(instruction)

    def callGCPointerResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallGCPointerResult, function, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def callVoidResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallVoidResult, function, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def callFloat32ResultAt(self, function, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.float32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.CallFloat32Result, function, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def phiInt32At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiInt32, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiInt64At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiInt64, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiPointerAt(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiPointer, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiGCPointerAt(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiGCPointer, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiFloat32At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.float32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiFloat32, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiFloat64At(self, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.float32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PhiFloat32, None, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def phiSourceInt32At(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourceInt32, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def phiSourceInt64At(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourceInt64, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def phiSourcePointerAt(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourcePointer, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def phiSourceGCPointerAt(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourceGCPointer, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def phiSourceFloat32At(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourceFloat32, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None

    def phiSourceFloat64At(self, targetTemp, sourceValue, sourcePosition, name = ''):
        instruction = MirInstruction(targetTemp, MirOpcode.PhiSourceFloat64, sourceValue, None, sourcePosition, name)
        self.addInstruction(instruction)
        return None
    
    def pointerAddConstantOffsetAt(self, pointer, offset, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.PointerAddConstantOffset, pointer, offset, sourcePosition, name)
        self.addInstruction(instruction)
        return temp


    def int32NegAt(self, operand, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32Neg, operand, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64NegAt(self, operand, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64Neg, operand, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32AddAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32Add, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64AddAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64Add, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32SubAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32Sub, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64SubAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64Sub, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32MulAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32Mul, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64MulAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64Mul, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32SDivAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32SDiv, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64SDivAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64SDiv, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32SModAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32SMod, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64SModAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64SMod, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32UDivAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32UDiv, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64UDivAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64UDiv, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32UModAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32UMod, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64UModAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64UMod, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32BitNotAt(self, operand, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32BitNot, operand, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def int64BitNotAt(self, operand, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64BitNot, operand, None, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32BitAndAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32BitAnd, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64BitAndAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64BitAnd, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32BitOrAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32BitOr, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64BitOrAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64BitOr, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32BitXorAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32BitXor, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64BitXorAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64BitXor, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    

    def int32ShiftLeftAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32ShiftLeft, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64ShiftLeftAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64ShiftLeft, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32AShiftRightAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32AShiftRight, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64AShiftRightAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64AShiftRight, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32LShiftRightAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32LShiftRight, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64LShiftRightAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64LShiftRight, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def int32EqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32Equals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64EqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64Equals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32NotEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32NotEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64NotEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64NotEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32LessThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32LessThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint32LessThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt32LessThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64LessThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64LessThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint64LessThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt64LessThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32LessOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32LessOrEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint32LessOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt32LessOrEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def int64LessOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64LessOrEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint64LessOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt64LessOrEquals, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int32GreaterThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32GreaterThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint32GreaterThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt32GreaterThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64GreaterThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64GreaterThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint64GreaterThanAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt64GreaterThan, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    
    def int32GreaterOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int32GreaterOrEqual, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint32GreaterOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt32GreaterOrEqual, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def int64GreaterOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.Int64GreaterOrEqual, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp

    def uint64GreaterOrEqualsAt(self, left, right, sourcePosition, name = ''):
        temp = self.function.newTemporary(self.function.module.context.boolean8Type, sourcePosition, name)
        instruction = MirInstruction(temp, MirOpcode.UInt64GreaterOrEqual, left, right, sourcePosition, name)
        self.addInstruction(instruction)
        return temp
    

    def constInt32At(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.int32Type, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstInt32, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constInt64At(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.int64Type, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstInt64, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constPointerAt(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.pointerType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstPointer, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constFloat32At(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.float32Type, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstFloat32, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constFloat64At(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.float64Type, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstFloat64, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constGCPointerAt(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstGCPointer, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constCharacterAt(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstCharacter, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp
    
    def constIntegerAt(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstInteger, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constFloatAt(self, value, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.gcPointerType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstFloat, value, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def constVoidAt(self, sourcePosition):
        temp = self.function.newTemporary(self.function.module.context.voidType, sourcePosition, None)
        instruction = MirInstruction(temp, MirOpcode.ConstVoid, None, None, sourcePosition)
        self.addInstruction(instruction)
        return temp

    def returnInt32At(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnInt32, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnInt64At(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnInt64, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnPointerAt(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnPointer, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnFloat32At(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnFloat32, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnFloat64At(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnFloat64, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnGCPointerAt(self, temp, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnGCPointer, temp, None, sourcePosition)
        return self.addInstruction(instruction)

    def returnVoidAt(self, sourcePosition):
        instruction = MirInstruction(None, MirOpcode.ReturnVoid, None, None, sourcePosition)
        return self.addInstruction(instruction)
        