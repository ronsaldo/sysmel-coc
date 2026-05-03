from parsetree import SourcePosition
from abc import ABC, abstractmethod

class HIRVisitor(ABC):
    def visitValue(self, value):
        pass

class HIRValue(ABC):
    def __init__(self, sourcePosition: SourcePosition):
        self.sourcePosition = sourcePosition
    
    def accept(self, visitor: HIRVisitor):
        return visitor.visitValue(self)
    
    @abstractmethod
    def getType(self):
        pass
    
    def isType(self):
        return False

    def isNominalType(self):
        return False

    def isDynamicType(self):
        return False

    def isUniverseType(self):
        return False

    def isAssociationType(self):
        return False

    def isTupleType(self):
        return False

    def isDependentFunctionType(self):
        return False

    def isSimpleFunctionType(self):
        return False

class HIRType(HIRValue):
    def __init__(self, coreTypes, sourcePosition):
        super().__init__(sourcePosition)
        self.coreTypes = coreTypes

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(0)
    
    def isType(self):
        return True

class HIRNominalType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isNominalType(self):
        return True
 

class HIRDynamicType(HIRType):
    def __init__(self, name: str, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.name = name

    def getName(self):
        return self.name

    def isDynamicType(self):
        return True

class HIRUniverseType(HIRType):
    def __init__(self, name: str, coreTypes, level: int):
        super().__init__(coreTypes, None)
        self.level = level
        self.name = name

    def getName(self):
        return self.name

    def getType(self):
        return self.coreTypes.getUniverseAtLevel(self.level + 1)

    def isUniverseType(self):
        return True

class HIRAssociationType(HIRType):
    def __init__(self, keyType: HIRType, valueType: HIRType, coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.keyType = keyType
        self.valueType = valueType

    def isAssociationType(self):
        return True    

class HIRTupleType(HIRType):
    def __init__(self, elements: list[HIRType], coreTypes, sourcePosition = None):
        super().__init__(coreTypes, sourcePosition)
        self.elements = elements

    def isTupleType(self):
        return True

class HIRSimpleFunctionType(HIRType):
    def __init__(self, argumentTypes: HIRType, resultType: HIRType, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.argumentTypes = argumentTypes
        self.resultType = resultType

    def isSimpleFunctionType(self):
        return True
    
class HIRDependentFunctionType(HIRType):
    def __init__(self, arguments, resultType: HIRValue, coreTypes, sourcePosition):
        super().__init__(coreTypes, sourcePosition)
        self.arguments = arguments
        self.resultType = resultType

    def isDependentFunctionType(self):
        return True
    
class HIRConstant(HIRValue):
    def __init__(self, sourcePosition):
        super().__init__(sourcePosition)

class HIRConstantLiteralValue(HIRConstant):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(sourcePosition)
        self.type = type

    def getType(self):
        return self.type

class HIRConstantLiteralIntegerValue(HIRConstantLiteralValue):
    def __init__(self, value: int, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralFloatValue(HIRConstantLiteralValue):
    def __init__(self, value: float, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralBooleanValue(HIRConstantLiteralValue):
    def __init__(self, value: bool, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralCharacterValue(HIRConstantLiteralValue):
    def __init__(self, value: int, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralStringValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralSymbolValue(HIRConstantLiteralValue):
    def __init__(self, value: str, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)
        self.value = value

class HIRConstantLiteralVoidValue(HIRConstantLiteralValue):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)

class HIRConstantLiteralNilValue(HIRConstantLiteralValue):
    def __init__(self, type: HIRType, sourcePosition):
        super().__init__(type, sourcePosition)

class HIRFunction(HIRConstant):
    def __init__(self, name: str, dependentFunctionType: HIRDependentFunctionType, sourcePosition):
        super().__init__(sourcePosition)
        self.name = name
        self.dependentFunctionType = dependentFunctionType
        self.captures = []
        self.firstBasicBlock = None
        self.lastBasicBlock = None
        self.enumeratedInstructions = None

    def getType(self):
        return self.dependentFunctionType
    
    def addBasicBlock(self, basicBlock):
        if self.lastBasicBlock is None:
            self.firstBasicBlock = self.lastBasicBlock = basicBlock
        else:
            basicBlock.previousBlock = self.lastBasicBlock
            self.lastBasicBlock.nextBlock = basicBlock
            self.lastBasicBlock = basicBlock

    def enumerateInstruction(self):
        if self.enumeratedInstructions is not None:
            return self.enumeratedInstructions
        
        self.enumeratedInstructions = []
        def addLocalValue(localValue):
            localValue.index = len(self.enumeratedInstructions)
            self.enumeratedInstructions.append(localValue)

        for argument in self.dependentFunctionType.arguments:
            addLocalValue(argument)

        for capture in self.captures:
            addLocalValue(capture)

        basicBlock = self.firstBasicBlock
        while basicBlock is not None:
            addLocalValue(basicBlock)

            instruction = basicBlock.firstInstruction
            while instruction is not None:
                addLocalValue(instruction)
                instruction = instruction.nextInstruction

            basicBlock = basicBlock.nextBlock

        return self.enumeratedInstructions

    def fullPrintString(self) -> str:
        self.enumerateInstruction()
        result = "HIRFunction "
        if self.name is not None:
            result += self.name
        result += " {\n"

        for argument in self.dependentFunctionType.arguments:
            result += argument.fullPrintString() + '\n'
        
        basicBlock = self.firstBasicBlock
        while basicBlock is not None:
            result += basicBlock.fullPrintString()
            basicBlock = basicBlock.nextBlock

        result += "}\n"
        return result

class HIRFunctionLocalValue(HIRValue):
    def __init__(self, type, name: str = None, sourcePosition = None):
        super().__init__(sourcePosition)
        self.type = type
        self.name = name
        self.index = -1

    def __str__(self):
        return '%d|%s' %(self.index, str(self.name))

    def getType(self):
        return self.type


class HIRArgument(HIRFunctionLocalValue):
    def fullPrintString(self) -> str:
        return '%d|%s := argument' %(self.index, str(self.name))

class HIRCapture(HIRFunctionLocalValue):
    def fullPrintString(self) -> str:
        return '%d|%s := capture' %(self.index, str(self.name))

class HIRBasicBlock(HIRFunctionLocalValue):
    def __init__(self, name = None, sourcePosition=None):
        super().__init__(None, name, sourcePosition)
        self.previousBlock = None
        self.nextBlock = None
        self.firstInstruction = None
        self.lastInstruction = None

    def addInstruction(self, instruction):
        if self.lastInstruction is None:
            self.firstInstruction = self.lastInstruction = instruction
        else:
            instruction.previousInstruction = self.lastInstruction
            self.lastInstruction.nextInstruction = instruction
            self.lastInstruction = instruction

    def fullPrintString(self) -> str:
        result = str(self.index)
        if self.name is not None:
            result += '|' + self.name

        instruction = self.firstInstruction
        while instruction is not None:
            result += '\n  ' + instruction.fullPrintString()
            instruction = instruction.nextInstruction

        result += '\n'
        return result

class HIRInstruction(HIRFunctionLocalValue):
    def __init__(self, type, name = None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.previousInstruction = None
        self.nextInstruction = None

class HIRReturnInstruction(HIRInstruction):
    def __init__(self, valueToReturn, type, name=None, sourcePosition=None):
        super().__init__(type, name, sourcePosition)
        self.valueToReturn = valueToReturn
    
    def fullPrintString(self) -> str:
        return "return " + str(self.valueToReturn)

class HIRPackage(HIRValue):
    def __init__(self, name: str):
        self.name = name
        self.usedPackages = []
        self.children = []
        self.publicSymbolTable = {}
        self.coreTypes = None

    def addCoreTypes(self, coreTypes):
        self.coreTypes = coreTypes
        for type in coreTypes.coreTypeList:
            typeName = type.getName()
            self.addSymbolWithBinding(typeName, type)
        for value, name in coreTypes.coreValueList:
            self.addSymbolWithBinding(name, value)

    def addSymbolWithBinding(self, symbol: str, binding: HIRValue):
        self.children.append(binding)
        self.publicSymbolTable[symbol] = binding

    def getType(self):
        return self.coreTypes.packageType

    def lookupSymbolRecursivelyOrNone(self, symbol: str):
        if symbol in self.publicSymbolTable:
            return self.publicSymbolTable[symbol]
        
        for usedPackage in self.usedPackages:
            usedSymbol = usedPackage.lookupSymbolRecursivelyOrNone(symbol)
            if usedSymbol is not None:
                return usedSymbol
                    
        return None

    def usePackage(self, package):
        if package not in self.usedPackages:
            self.usedPackages.append(package)

class HIREnvironment:
    def __init__(self):
        pass

class HIREmptyEnvironment(HIREnvironment):
    pass

class HIRLexicalEnvironment(HIREnvironment):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.symbolTable = {}

class HIRCoreTypes:
    def __init__(self):
        self.pointerSize = 8
        self.pointerAlignment = 8

        self.integerType   = HIRNominalType('Integer', self, None);
        self.characterType = HIRNominalType('Character', self, None);
        self.floatType     = HIRNominalType('Float', self, None);
        self.booleanType   = HIRNominalType('Boolean', self, None);
        self.stringType    = HIRNominalType('String', self, None);
        self.symbolType    = HIRNominalType('Symbol', self, None);
        self.voidType      = HIRNominalType('Void', self, None);
        self.undefinedType = HIRNominalType('Undefined', self, None);
        
        self.dynamicType = HIRDynamicType('Dynamic', self, None)

        self.packageType = HIRNominalType('Package', self, None)

        self.prop = HIRUniverseType('Prop', self, 0);
        self.type = HIRUniverseType('Type', self, 1);
        self.universeLevels = {
            0: self.prop,
            1: self.type,
        }

        self.voidValue = HIRConstantLiteralVoidValue(self.voidType, None)
        self.falseValue = HIRConstantLiteralBooleanValue(False, self.booleanType, None)
        self.trueValue = HIRConstantLiteralBooleanValue(True, self.booleanType, None)
        self.nilValue = HIRConstantLiteralNilValue(self.undefinedType, None)

        self.coreTypeList = [
            self.integerType,
            self.characterType,
            self.floatType,
            self.booleanType,
            self.stringType,
            self.symbolType,
            self.voidType,
            self.undefinedType,

            self.dynamicType,

            self.prop,
            self.type,
        ]
        self.coreValueList = [
            (self.voidValue,  'void'),
            (self.falseValue, 'false'),
            (self.trueValue,  'true'),
            (self.nilValue,   'nil'),
        ]
    
    def getUniverseAtLevel(self, level):
        if level in self.universeLevels:
            return self.universeLevels[level]
        newLevel = HIRUniverseType(None, self, level)
        self.universeLevels[level] = newLevel
        return newLevel

class HIRContext:
    def __init__(self):
        self.coreTypes = HIRCoreTypes()
        self.corePackage = HIRPackage('CoreLib')
        self.corePackage.addCoreTypes(self.coreTypes)
        self.currentPackage = self.corePackage

class HIRBuilder:
    def __init__(self, function: HIRFunction, context: HIRContext, basicBlock: HIRBasicBlock, environment: HIRLexicalEnvironment):
        self.function = function
        self.context = context
        self.basicBlock = basicBlock
        self.environment = environment

    def addInstruction(self, instruction):
        self.basicBlock.addInstruction(instruction)

    def returnValue(self, valueToReturn, sourcePosition):
        instruction = HIRReturnInstruction(valueToReturn, self.context.coreTypes.voidType, None, sourcePosition)
        self.addInstruction(instruction)
        return instruction